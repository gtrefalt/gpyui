//! Native image ownership. Decode with GPUI's loader on its background executor.
use base64::{Engine, engine::general_purpose::STANDARD};
use gpui_kit::{component::ActiveTheme, prelude::FluentBuilder, *};
use serde_json::{Map, Value, json};
use std::{
    borrow::Cow,
    collections::HashMap,
    path::PathBuf,
    sync::{
        Arc, Mutex,
        atomic::{AtomicU64, Ordering},
    },
};

const MAX_BYTES: usize = 32 * 1024 * 1024;

pub(crate) fn valid_source(source: &Value) -> bool {
    if source.is_null() {
        return true;
    }
    let Some(source) = source.as_object().filter(|v| v.len() == 2) else {
        return false;
    };
    let Some(value) = source.get("value").and_then(Value::as_str) else {
        return false;
    };
    match source.get("kind").and_then(Value::as_str) {
        Some("bytes") => {
            value.len() <= MAX_BYTES.div_ceil(3) * 4
                && STANDARD
                    .decode(value)
                    .is_ok_and(|v| !v.is_empty() && v.len() <= MAX_BYTES)
        }
        Some(kind @ ("file" | "asset" | "url")) => {
            if value.is_empty() || value.chars().count() > 32768 || value.chars().any(|c| c < ' ') {
                return false;
            }
            kind != "url"
                || http_client::Url::parse(value).is_ok_and(|url| {
                    matches!(url.scheme(), "http" | "https")
                        && url.host_str().is_some()
                        && url.username().is_empty()
                        && url.password().is_none()
                })
        }
        _ => false,
    }
}

/// Keep Kit icons and make encoded Python images available to its normal loader.
#[derive(Clone, Default)]
pub(crate) struct ImageAssets(Arc<Mutex<HashMap<String, Vec<u8>>>>);
impl Global for ImageAssets {}
impl AssetSource for ImageAssets {
    fn load(&self, path: &str) -> Result<Option<Cow<'static, [u8]>>> {
        if let Some(bytes) = self.0.lock().expect("image assets mutex").get(path) {
            return Ok(Some(Cow::Owned(bytes.clone())));
        }
        gpui_kit::assets::AllAssets.load(path)
    }
    fn list(&self, path: &str) -> Result<Vec<SharedString>> {
        gpui_kit::assets::AllAssets.list(path)
    }
}

struct MemoryAsset {
    key: String,
    assets: ImageAssets,
}
impl Drop for MemoryAsset {
    fn drop(&mut self) {
        self.assets
            .0
            .lock()
            .expect("image assets mutex")
            .remove(&self.key);
    }
}

pub(crate) struct ImageEvent {
    pub revision: u64,
    pub name: &'static str,
    pub value: Value,
}

pub(crate) struct NativeImage {
    source: Value,
    revision: u64,
    result: Option<std::result::Result<Arc<RenderImage>, ImageCacheError>>,
    task: Option<Task<()>>,
    memory: Option<MemoryAsset>,
}
impl EventEmitter<ImageEvent> for NativeImage {}

impl NativeImage {
    pub(crate) fn new(props: &Map<String, Value>) -> Self {
        Self {
            source: props["source"].clone(),
            revision: props["_revision"].as_u64().unwrap(),
            result: None,
            task: None,
            memory: None,
        }
    }
    pub(crate) fn release(&mut self, window: &mut Window, cx: &mut App) {
        self.task = None; // Superseded tasks cannot deliver an old result.
        self.memory = None;
        if let Some(Ok(image)) = self.result.take() {
            // Dropping the CPU result alone does not evict GPUI's GPU atlas entries.
            cx.drop_image(image, Some(window));
        }
        self.source = Value::Null;
    }
    pub(crate) fn reset(
        &mut self,
        props: &Map<String, Value>,
        window: &mut Window,
        cx: &mut Context<Self>,
    ) {
        self.release(window, cx);
        self.source = props["source"].clone();
        self.revision = props["_revision"].as_u64().unwrap();
        cx.notify();
    }
    pub(crate) fn status(&self) -> Value {
        match &self.result {
            Some(Ok(image)) => json!({"status":"loaded", "width":image.size(0).width.0,
                "height":image.size(0).height.0, "frames":image.frame_count()}),
            Some(Err(error)) => json!({"status":"error", "error":error.to_string()}),
            None => json!({"status": if self.source.is_null() { "empty" } else { "loading" }}),
        }
    }
    fn start(&mut self, cx: &mut Context<Self>) {
        if self.source.is_null() || self.task.is_some() || self.result.is_some() {
            return;
        }
        let value = self.source["value"].as_str().unwrap();
        let resource = match self.source["kind"].as_str().unwrap() {
            "file" => Resource::Path(PathBuf::from(value).into()),
            "url" => Resource::Uri(value.to_owned().into()),
            "asset" => Resource::Embedded(value.to_owned().into()),
            "bytes" => {
                static NEXT_ID: AtomicU64 = AtomicU64::new(0);
                let key = format!("__gpyui_images/{}", NEXT_ID.fetch_add(1, Ordering::Relaxed));
                let assets = cx.global::<ImageAssets>().clone();
                assets.0.lock().expect("image assets mutex").insert(
                    key.clone(),
                    STANDARD.decode(value).expect("validated bytes"),
                );
                self.memory = Some(MemoryAsset {
                    key: key.clone(),
                    assets,
                });
                Resource::Embedded(key.into())
            }
            _ => unreachable!("validated source"),
        };
        // Keep a single decoded result per control rather than caching every
        // replacement for the lifetime of the application.
        let future = ImageAssetLoader::load(resource, cx);
        let decode = cx.background_executor().spawn(future);
        let revision = self.revision;
        self.task = Some(cx.spawn(async move |image, cx| {
            let result = decode.await;
            let _ = image.update(cx, |image, cx| {
                if image.revision != revision {
                    return;
                }
                let (name, value) = match &result {
                    Ok(data) => (
                        "load",
                        json!({"width":data.size(0).width.0,
                        "height":data.size(0).height.0, "frames":data.frame_count()}),
                    ),
                    Err(error) => ("error", json!(error.to_string())),
                };
                image.result = Some(result);
                image.memory = None;
                cx.emit(ImageEvent {
                    revision,
                    name,
                    value,
                });
                cx.notify();
            });
        }));
    }
}

#[derive(IntoElement)]
pub(crate) struct ImageElement {
    pub state: Entity<NativeImage>,
    pub id: u64,
    pub props: Map<String, Value>,
    pub style: Map<String, Value>,
}
impl RenderOnce for ImageElement {
    fn render(self, _: &mut Window, cx: &mut App) -> impl IntoElement {
        self.state.update(cx, |image, cx| image.start(cx));
        let ratio = self.props["aspect_ratio"].as_f64().unwrap() as f32;
        if self.state.read(cx).source.is_null() {
            return crate::kit::apply_style(div(), &self.style, cx)
                .when(ratio > 0., |el| el.aspect_ratio(ratio))
                .into_any_element();
        }
        let state = self.state.clone();
        let source =
            ImageSource::from(move |_: &mut Window, cx: &mut App| state.read(cx).result.clone());
        let loading = self.props["loading_text"].as_str().unwrap().to_owned();
        let fallback = self.props["error_text"].as_str().unwrap().to_owned();
        let muted = cx.theme().muted_foreground;
        let fit = match self.props["fit"].as_str().unwrap() {
            "cover" => ObjectFit::Cover,
            "fill" => ObjectFit::Fill,
            "scale_down" => ObjectFit::ScaleDown,
            "none" => ObjectFit::None,
            _ => ObjectFit::Contain,
        };
        crate::kit::apply_style(
            img(source)
                .id(SharedString::from(format!(
                    "image-{}-{}",
                    self.id, self.props["_revision"]
                )))
                .object_fit(fit)
                .grayscale(self.props["grayscale"].as_bool().unwrap())
                .when(ratio > 0., |el| el.aspect_ratio(ratio))
                .with_loading(move || {
                    div()
                        .size_full()
                        .flex()
                        .items_center()
                        .justify_center()
                        .text_color(muted)
                        .child(loading.clone())
                        .into_any_element()
                })
                .with_fallback(move || {
                    div()
                        .size_full()
                        .flex()
                        .items_center()
                        .justify_center()
                        .text_color(muted)
                        .child(fallback.clone())
                        .into_any_element()
                }),
            &self.style,
            cx,
        )
        .into_any_element()
    }
}
