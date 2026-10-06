//! Strict Python theme contract translated into Kit's native ThemeConfig.
use gpui_kit::{
    component::{
        ActiveTheme, Colorize, Sizable, Size, Theme, ThemeConfig, ThemeMode, button::Button,
    },
    prelude::FluentBuilder,
    *,
};
use serde::Deserialize;
use serde_json::{Map, Value, json};
use std::{collections::BTreeMap, rc::Rc};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ThemeSpec {
    name: String,
    mode: ThemeMode,
    colors: BTreeMap<String, String>,
    radius: u8,
    radius_lg: u8,
    font_size: f32,
    font_family: Option<String>,
    mono_font_size: f32,
    mono_font_family: Option<String>,
    shadow: bool,
}

#[derive(Clone, Copy, Default, PartialEq, Eq)]
enum PlatformStyle {
    #[default]
    Kit,
    Mac,
    Windows,
}

#[derive(Clone, Default)]
struct Appearance {
    platform: PlatformStyle,
    control_background: Option<Hsla>,
    switch_checked: Option<Hsla>,
}
impl Global for Appearance {}

pub(crate) struct NativeTheme {
    config: ThemeConfig,
    appearance: Appearance,
    automatic_font: bool,
}

fn appearance(cx: &App) -> Appearance {
    cx.try_global::<Appearance>().cloned().unwrap_or_default()
}

fn color_key(key: &str) -> Option<&'static str> {
    Some(match key {
        "background" => "background",
        "foreground" => "foreground",
        "primary" => "primary.background",
        "primary_foreground" => "primary.foreground",
        "primary_hover" => "primary.hover.background",
        "primary_active" => "primary.active.background",
        "secondary" => "secondary.background",
        "secondary_foreground" => "secondary.foreground",
        "muted" => "muted.background",
        "muted_foreground" => "muted.foreground",
        "border" => "border",
        "input" => "input.border",
        "ring" => "ring",
        "accent" => "accent.background",
        "accent_foreground" => "accent.foreground",
        "danger" => "danger.background",
        "danger_foreground" => "danger.foreground",
        "success" => "success.background",
        "warning" => "warning.background",
        "info" => "info.background",
        "selection" => "selection.background",
        "caret" => "caret",
        "button" => "button.background",
        "button_hover" => "button.hover.background",
        "button_active" => "button.active.background",
        "popover" => "popover.background",
        "sidebar" => "sidebar.background",
        "switch" => "switch.background",
        "switch_thumb" => "switch.thumb.background",
        "slider" => "slider.background",
        "slider_thumb" => "slider.thumb.background",
        _ => return None,
    })
}

pub(crate) fn parse(value: &str) -> Result<NativeTheme, String> {
    let spec: ThemeSpec = serde_json::from_str(value).map_err(|e| e.to_string())?;
    if spec.name.trim().is_empty() || spec.name.len() > 64 {
        return Err("theme name requires 1–64 characters".into());
    }
    if spec.radius > 64 || spec.radius_lg > 64 {
        return Err("theme radius requires 0–64 pixels".into());
    }
    for size in [spec.font_size, spec.mono_font_size] {
        if !size.is_finite() || !(8. ..=48.).contains(&size) {
            return Err("theme font size requires 8–48 pixels".into());
        }
    }
    for family in [&spec.font_family, &spec.mono_font_family]
        .into_iter()
        .flatten()
    {
        if family.trim().is_empty() || family.chars().count() > 256 {
            return Err("theme font family requires 1–256 characters".into());
        }
    }
    let mut appearance = Appearance {
        platform: match spec.name.as_str() {
            "macos" => PlatformStyle::Mac,
            "windows" => PlatformStyle::Windows,
            _ => PlatformStyle::Kit,
        },
        ..Default::default()
    };
    let automatic_font = spec.font_family.is_none();
    let mut colors = serde_json::Map::new();
    for (key, value) in spec.colors {
        if !(value.len() == 7 || value.len() == 9)
            || !value.starts_with('#')
            || !value.as_bytes()[1..].iter().all(u8::is_ascii_hexdigit)
        {
            return Err("theme colors require #RRGGBB or #RRGGBBAA".into());
        }
        match key.as_str() {
            "control_background" => {
                appearance.control_background =
                    Some(Hsla::parse_hex(&value).map_err(|e| e.to_string())?)
            }
            "switch_checked" => {
                appearance.switch_checked =
                    Some(Hsla::parse_hex(&value).map_err(|e| e.to_string())?)
            }
            _ => {
                let key = color_key(&key).ok_or_else(|| format!("unknown theme color: {key}"))?;
                colors.insert(key.into(), json!(value));
            }
        }
    }
    // Specify every scalar, including default font families, so switching away
    // from a custom theme cannot retain that theme's typography/radius/shadows.
    let defaults = Theme::default();
    let config = serde_json::from_value(json!({
        "name":spec.name, "mode":spec.mode, "colors":colors,
        "radius":spec.radius, "radius.lg":spec.radius_lg, "shadow":spec.shadow,
        "font.size":spec.font_size,
        "font.family":spec.font_family.unwrap_or_else(|| defaults.font_family.to_string()),
        "mono_font.size":spec.mono_font_size,
        "mono_font.family":spec.mono_font_family.unwrap_or_else(|| defaults.mono_font_family.to_string()),
    })).map_err(|e| e.to_string())?;
    Ok(NativeTheme {
        config,
        appearance,
        automatic_font,
    })
}

pub(crate) fn apply(mut native: NativeTheme, cx: &mut App) {
    if native.automatic_font {
        let candidates: &[&str] = match native.appearance.platform {
            PlatformStyle::Mac if cfg!(target_os = "macos") => &[".SystemUIFont"],
            PlatformStyle::Mac => &[
                "SF Pro Text",
                "Helvetica Neue",
                "Inter",
                "Liberation Sans",
                "DejaVu Sans",
            ],
            PlatformStyle::Windows => &[
                "Segoe UI Variable Text",
                "Segoe UI",
                "Noto Sans",
                "DejaVu Sans",
            ],
            PlatformStyle::Kit => &[],
        };
        let installed = cx.text_system().all_font_names();
        if let Some(family) = candidates.iter().find(|family| {
            **family == ".SystemUIFont"
                || installed
                    .iter()
                    .any(|name| name.eq_ignore_ascii_case(family))
        }) {
            native.config.font_family = Some((*family).into());
        }
    }
    // Install the renderer hints before Kit refreshes the window. Neither changes entities.
    cx.set_global(native.appearance);
    let config = native.config;
    // update synchronizes legacy colors, component background tokens, semantic
    // tokens and the Base theme used by scrollbars, popovers and input helpers.
    Theme::update(cx, |theme| theme.apply_config(&Rc::new(config)));
}

pub(crate) fn snapshot(cx: &App) -> Value {
    let theme = Theme::global(cx);
    let base = gpui_kit::base::Theme::global(cx);
    let appearance = appearance(cx);
    let mut snapshot = json!({
        "name": if theme.mode.is_dark() { &theme.dark_theme.name } else { &theme.light_theme.name },
        "mode":theme.mode, "radius":f32::from(theme.radius), "radius_lg":f32::from(theme.radius_lg),
        "font_size":f32::from(theme.font_size), "font_family":theme.font_family,
        "mono_font_size":f32::from(theme.mono_font_size), "mono_font_family":theme.mono_font_family,
        "shadow":theme.shadow,
        "colors": {
            "background":theme.background.to_hex(), "foreground":theme.foreground.to_hex(),
            "primary":theme.primary.to_hex(), "primary_foreground":theme.primary_foreground.to_hex(),
            "primary_hover":theme.primary_hover.to_hex(), "primary_active":theme.primary_active.to_hex(),
            "button_primary":theme.button_primary.to_hex(),
            "button_primary_hover":theme.button_primary_hover.to_hex(),
            "button_primary_active":theme.button_primary_active.to_hex(),
            "secondary":theme.secondary.to_hex(), "secondary_foreground":theme.secondary_foreground.to_hex(),
            "muted":theme.muted.to_hex(), "muted_foreground":theme.muted_foreground.to_hex(),
            "border":theme.border.to_hex(), "input":theme.input.to_hex(), "ring":theme.ring.to_hex(),
            "selection":theme.selection.to_hex(), "caret":theme.caret.to_hex(),
            "accent":theme.accent.to_hex(), "accent_foreground":theme.accent_foreground.to_hex(),
            "danger":theme.danger.to_hex(), "danger_foreground":theme.danger_foreground.to_hex(),
            "success":theme.success.to_hex(), "warning":theme.warning.to_hex(), "info":theme.info.to_hex(),
            "button":theme.button.to_hex(), "button_hover":theme.button_hover.to_hex(),
            "button_active":theme.button_active.to_hex(), "popover":theme.popover.to_hex(),
            "sidebar":theme.sidebar.to_hex(),

        },
        "base": {"background":base.tokens.colors.background.to_hex(),
                 "primary":base.tokens.colors.primary.to_hex(), "radius":f32::from(base.tokens.radius.md)},
    });
    for (key, color) in [
        (
            "control_background",
            appearance
                .control_background
                .unwrap_or_else(|| theme.input_background()),
        ),
        ("switch", theme.switch),
        ("switch_thumb", theme.switch_thumb),
        (
            "switch_checked",
            appearance.switch_checked.unwrap_or(theme.primary),
        ),
        ("slider", theme.slider_bar),
        ("slider_thumb", theme.slider_thumb),
    ] {
        snapshot["colors"][key] = json!(color.to_hex());
    }
    snapshot
}

// Kit's sizing hooks act on the real control, unlike a styled outer Python host.
pub(crate) fn size(cx: &App) -> Size {
    match appearance(cx).platform {
        PlatformStyle::Mac => Size::Small,
        PlatformStyle::Windows => Size::Medium,
        PlatformStyle::Kit => Size::Medium,
    }
}

fn number(style: &Map<String, Value>, key: &str, fallback: f32) -> f32 {
    style
        .get(key)
        .and_then(Value::as_f64)
        .map(|v| v as f32)
        .unwrap_or(fallback)
}

pub(crate) fn button(button: Button, style: &Map<String, Value>, cx: &App) -> Button {
    let platform = appearance(cx).platform;
    if platform == PlatformStyle::Kit {
        return button;
    }
    button
        .with_size(size(cx))
        .h(px(number(
            style,
            "height",
            if platform == PlatformStyle::Mac {
                24.
            } else {
                32.
            },
        )))
        .px(px(number(
            style,
            "padding",
            if platform == PlatformStyle::Mac {
                10.
            } else {
                12.
            },
        )))
        .rounded(px(number(style, "radius", cx.theme().radius.into())))
        .text_size(px(number(style, "font_size", cx.theme().font_size.into())))
        .when(platform == PlatformStyle::Windows, |el| {
            el.shadow(Vec::new())
        })
}

pub(crate) fn switch_size(cx: &App) -> Size {
    if appearance(cx).platform == PlatformStyle::Windows {
        Size::Large
    } else {
        Size::Medium
    }
}

pub(crate) fn switch_color(cx: &App) -> Hsla {
    appearance(cx).switch_checked.unwrap_or(cx.theme().primary)
}

pub(crate) fn platform_controls(cx: &App) -> bool {
    appearance(cx).platform != PlatformStyle::Kit
}

pub(crate) fn checkbox_size(cx: &App) -> Size {
    match appearance(cx).platform {
        PlatformStyle::Mac => Size::Medium,
        PlatformStyle::Windows => Size::Large,
        PlatformStyle::Kit => Size::Medium,
    }
}

pub(crate) fn field_frame(cx: &App) -> bool {
    let appearance = appearance(cx);
    appearance.platform != PlatformStyle::Kit || appearance.control_background.is_some()
}

// The frame is presentation only. Kit keeps the original entity, focus handle,
// keyboard actions, accessibility role, context menu, caret and undo engine.
#[derive(IntoElement)]
struct FieldFrame {
    child: AnyElement,
    focus: FocusHandle,
    disabled: bool,
    style: Map<String, Value>,
    height: Option<Pixels>,
}

impl RenderOnce for FieldFrame {
    fn render(self, window: &mut Window, cx: &mut App) -> impl IntoElement {
        let appearance = appearance(cx);
        let focused = self.focus.is_focused(window) && !self.disabled;
        let windows = appearance.platform == PlatformStyle::Windows;
        div()
            .w_full()
            .when_some(self.height, |el, height| el.h(height))
            .rounded(px(number(&self.style, "radius", cx.theme().radius.into())))
            .bg(appearance
                .control_background
                .unwrap_or_else(|| cx.theme().input_background()))
            .text_color(if self.disabled {
                cx.theme().muted_foreground
            } else {
                cx.theme().foreground
            })
            .border_1()
            .border_color(if focused && !windows {
                cx.theme().ring
            } else {
                cx.theme().input
            })
            .relative()
            .when(!self.disabled, |el| {
                let focus = self.focus.clone();
                el.on_mouse_down(MouseButton::Left, move |_, window, cx| {
                    focus.focus(window, cx)
                })
            })
            .when(focused && !windows, |el| {
                el.shadow(vec![BoxShadow {
                    inset: false,
                    color: cx.theme().ring.opacity(0.25),
                    offset: point(px(0.), px(0.)),
                    blur_radius: px(0.),
                    spread_radius: px(3.),
                }])
            })
            .when(self.disabled, |el| el.opacity(0.5))
            .child(self.child)
            .when(windows, |el| {
                el.child(
                    div()
                        .absolute()
                        .left(px(1.))
                        .right(px(1.))
                        .bottom(px(0.))
                        .h(px(if focused { 2. } else { 1. }))
                        .rounded_b(cx.theme().radius)
                        .bg(if focused {
                            cx.theme().ring
                        } else {
                            cx.theme().muted_foreground.opacity(0.65)
                        }),
                )
            })
    }
}

pub(crate) fn field<T: IntoElement + Styled + Sizable>(
    element: T,
    focus: FocusHandle,
    disabled: bool,
    multiline: bool,
    style: &Map<String, Value>,
    cx: &App,
) -> AnyElement {
    if !field_frame(cx) {
        return element.into_any_element();
    }
    let height = style
        .get("height")
        .and_then(Value::as_f64)
        .map(|v| px(v as f32))
        .or_else(|| {
            (!multiline).then(|| {
                px(if appearance(cx).platform == PlatformStyle::Mac {
                    24.
                } else {
                    32.
                })
            })
        });
    let element = element.with_size(size(cx)).h_full().text_size(px(number(
        style,
        "font_size",
        cx.theme().font_size.into(),
    )));
    FieldFrame {
        child: element.into_any_element(),
        focus,
        disabled,
        style: style.clone(),
        height,
    }
    .into_any_element()
}

pub(crate) fn select<T: IntoElement>(
    element: T,
    focus: FocusHandle,
    disabled: bool,
    style: &Map<String, Value>,
    cx: &App,
) -> AnyElement {
    if !field_frame(cx) {
        return element.into_any_element();
    }
    FieldFrame {
        child: element.into_any_element(),
        focus,
        disabled,
        style: style.clone(),
        height: Some(px(number(
            style,
            "height",
            if appearance(cx).platform == PlatformStyle::Mac {
                24.
            } else {
                32.
            },
        ))),
    }
    .into_any_element()
}
