use crate::commands::UiConfig;
use crate::protocol::{self, Command, ControlType, Node, Patch};
use async_channel::{Receiver, Sender};
use gpui_kit::*;
use pyo3::{
    exceptions::{PyRuntimeError, PyValueError},
    prelude::*,
};
use serde_json::{Value, json};
use std::{
    collections::{HashMap, HashSet},
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, Ordering},
    },
};

const QUEUE_CAPACITY: usize = 1024;
static RUN_STARTED: AtomicBool = AtomicBool::new(false);

pub(crate) struct Transport {
    pub(crate) commands: Sender<Command>,
    pub(crate) events: Sender<Value>,
    pub(crate) finished: AtomicBool,
    pub(crate) error: Mutex<Option<String>>,
}

impl Transport {
    pub(crate) fn emit(&self, event: Value) -> bool {
        if self.events.try_send(event).is_err() {
            self.fail("Python event queue overflowed; callbacks cannot keep up".into());
            return false;
        }
        true
    }
    pub(crate) fn fail(&self, message: String) {
        let mut error = self.error.lock().expect("error lock poisoned");
        if error.is_none() {
            *error = Some(message);
        }
    }
    fn finish(&self) {
        self.finished.store(true, Ordering::Release);
        self.commands.close();
        self.events.close();
    }
}

type NativeStartup = (Vec<Node>, UiConfig, Receiver<Command>);

/// Thread-safe transport containing no Python callbacks or GPUI handles.
#[pyclass]
pub(crate) struct Bridge {
    transport: Arc<Transport>,
    event_receiver: Receiver<Value>,
    native: Mutex<Option<NativeStartup>>,
    schema: Mutex<HashMap<u64, ControlType>>,
    retired: Mutex<HashSet<u64>>,
    config: Mutex<UiConfig>,
}

#[pymethods]
impl Bridge {
    #[new]
    #[pyo3(signature = (tree_json, config_json=""))]
    fn new(tree_json: &str, config_json: &str) -> PyResult<Self> {
        let config: UiConfig = if config_json.is_empty() {
            UiConfig::default()
        } else {
            serde_json::from_str(config_json)
                .map_err(|error| PyValueError::new_err(error.to_string()))?
        };
        let nodes: Vec<Node> =
            serde_json::from_str(tree_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let schema = protocol::schema(&nodes, &config).map_err(PyValueError::new_err)?;
        protocol::validate_roots(
            &nodes,
            &nodes.iter().map(|node| node.id).collect::<Vec<_>>(),
        )
        .map_err(PyValueError::new_err)?;
        let (commands, receiver) = async_channel::bounded(QUEUE_CAPACITY);
        let (events, event_receiver) = async_channel::bounded(QUEUE_CAPACITY);
        Ok(Self {
            transport: Arc::new(Transport {
                commands,
                events,
                finished: AtomicBool::new(false),
                error: Mutex::new(None),
            }),
            event_receiver,
            native: Mutex::new(Some((nodes, config.clone(), receiver))),
            schema: Mutex::new(schema),
            retired: Mutex::new(HashSet::new()),
            config: Mutex::new(config),
        })
    }
    /// Validate the entire batch before enqueueing any update.
    fn submit(&self, batch_json: &str) -> PyResult<()> {
        let patches: Vec<Patch> =
            serde_json::from_str(batch_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let schema = self.schema.lock().expect("schema lock poisoned");
        protocol::validate_batch(&patches, &schema).map_err(PyValueError::new_err)?;
        self.send(Command::Batch(patches))
    }
    /// Atomically validate/enqueue topology and properties before changing schema.
    #[pyo3(signature = (tree_json, roots_json, batch_json, config_json=None))]
    fn reconcile(
        &self,
        tree_json: &str,
        roots_json: &str,
        batch_json: &str,
        config_json: Option<&str>,
    ) -> PyResult<()> {
        let mut current = self.config.lock().expect("config lock poisoned");
        let config: UiConfig = if let Some(value) = config_json {
            serde_json::from_str(value).map_err(|error| PyValueError::new_err(error.to_string()))?
        } else {
            current.clone()
        };
        let nodes: Vec<Node> =
            serde_json::from_str(tree_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let roots: Vec<u64> =
            serde_json::from_str(roots_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let patches: Vec<Patch> =
            serde_json::from_str(batch_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let mut next = protocol::schema(&nodes, &config).map_err(PyValueError::new_err)?;
        protocol::validate_roots(&nodes, &roots).map_err(PyValueError::new_err)?;
        let mut schema = self.schema.lock().expect("schema lock poisoned");
        let mut retired = self.retired.lock().expect("retired lock poisoned");
        for (id, kind) in &mut next {
            if retired.contains(id) {
                return Err(PyValueError::new_err(format!("control {id} was disposed")));
            }
            if let Some(existing) = schema.get(id) {
                if !protocol::validate_identity(existing, kind) {
                    return Err(PyValueError::new_err(format!(
                        "control {id} changed type or constructor-only fields"
                    )));
                }
                *kind = existing.clone();
            }
        }
        protocol::validate_batch(&patches, &next).map_err(PyValueError::new_err)?;
        let retained = next.keys().copied().collect();
        self.send(Command::Reconcile {
            nodes,
            roots,
            patches,
            retained,
            config: config.clone(),
        })?;
        *current = config;
        retired.extend(schema.keys().filter(|id| !next.contains_key(id)));
        *schema = next;
        Ok(())
    }
    fn execute(&self, id: u64) -> PyResult<()> {
        if !matches!(
            self.schema.lock().expect("schema lock poisoned").get(&id),
            Some(ControlType::Action { .. })
        ) {
            return Err(PyValueError::new_err("unknown command"));
        }
        self.send(Command::Execute(id))
    }
    fn snapshot(&self, token: u64) -> PyResult<()> {
        self.send(Command::Snapshot(token))
    }
    #[pyo3(signature = (message, title="", variant="info"))]
    fn notify(&self, message: &str, title: &str, variant: &str) -> PyResult<()> {
        if !matches!(variant, "info" | "success" | "warning" | "danger") {
            return Err(PyValueError::new_err("invalid notification variant"));
        }
        self.send(Command::Notify {
            message: message.into(),
            title: title.into(),
            variant: variant.into(),
        })
    }
    fn close(&self) -> PyResult<()> {
        if self.transport.finished.load(Ordering::Acquire) {
            return Ok(());
        }
        self.send(Command::Close)
    }
    /// Release the GIL while waiting. Closing the queue wakes the reader.
    fn next_events(&self, py: Python<'_>) -> PyResult<String> {
        let receiver = self.event_receiver.clone();
        py.detach(move || {
            let mut events = Vec::new();
            match receiver.recv_blocking() {
                Ok(event) => events.push(event),
                Err(_) => return Ok("[{\"event\":\"closed\"}]".to_owned()),
            }
            while events.len() < 256 {
                match receiver.try_recv() {
                    Ok(event) => events.push(event),
                    Err(_) => break,
                }
            }
            serde_json::to_string(&events).map_err(|e| PyRuntimeError::new_err(e.to_string()))
        })
    }
    #[pyo3(signature = (title, width, height, theme="light"))]
    fn run(
        &self,
        py: Python<'_>,
        title: String,
        width: f32,
        height: f32,
        theme: &str,
    ) -> PyResult<()> {
        let dark = match theme {
            "light" => false,
            "dark" => true,
            _ => return Err(PyValueError::new_err("theme requires light or dark")),
        };
        let threading = py.import("threading")?;
        if !threading
            .call_method0("current_thread")?
            .is(&threading.call_method0("main_thread")?)
        {
            return Err(PyRuntimeError::new_err(
                "GPUI must run on Python's main thread",
            ));
        }
        if !width.is_finite() || !height.is_finite() || width < 240. || height < 160. {
            return Err(PyValueError::new_err(
                "window size must be finite and at least 240 x 160",
            ));
        }
        #[cfg(target_os = "linux")]
        if std::env::var_os("DISPLAY").is_none() && std::env::var_os("WAYLAND_DISPLAY").is_none() {
            return Err(PyRuntimeError::new_err(
                "GPUI requires an X11 or Wayland display",
            ));
        }
        if RUN_STARTED.swap(true, Ordering::AcqRel) {
            return Err(PyRuntimeError::new_err(
                "only one native Application.run() is supported per process",
            ));
        }
        let (nodes, config, commands) = self
            .native
            .lock()
            .expect("native lock poisoned")
            .take()
            .ok_or_else(|| PyRuntimeError::new_err("this native bridge has already run"))?;
        let transport = self.transport.clone();
        let cleanup = transport.clone();
        let result = py.detach(move || {
            std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                gpui_kit::application()
                    .with_assets(gpui_kit::assets::AllAssets)
                    .run(move |cx| {
                        gpui_kit::init(cx);
                        gpui_kit::component::Theme::change(
                            if dark {
                                gpui_kit::component::ThemeMode::Dark
                            } else {
                                gpui_kit::component::ThemeMode::Light
                            },
                            None,
                            cx,
                        );
                        let options = WindowOptions {
                            window_bounds: Some(WindowBounds::centered(
                                size(px(width), px(height)),
                                cx,
                            )),
                            window_min_size: Some(size(px(240.), px(160.))),
                            ..Default::default()
                        };
                        let view_transport = transport.clone();
                        match gpui_kit::open_window(options, cx, move |window, cx| {
                            window.set_window_title(&title);
                            cx.new(|cx| {
                                crate::view::NativeView::new(
                                    nodes,
                                    config,
                                    commands,
                                    view_transport,
                                    window,
                                    cx,
                                )
                            })
                        }) {
                            Ok((_, view)) => {
                                let view = view.downgrade();
                                cx.on_action(move |action: &crate::commands::InvokeCommand, cx| {
                                    _ = view
                                        .update(cx, |view, cx| view.invoke(action.id, None, cx));
                                });
                                if !transport.emit(json!({"event": "ready"})) {
                                    cx.quit();
                                }
                                cx.on_window_closed(|cx, _| {
                                    if cx.windows().is_empty() {
                                        cx.quit();
                                    }
                                })
                                .detach();
                                cx.activate(true);
                            }
                            Err(error) => {
                                transport.fail(format!("could not open native window: {error:#}"));
                                cx.quit();
                            }
                        }
                    });
            }))
        });
        cleanup.finish();
        if let Err(panic) = result {
            let message = panic
                .downcast_ref::<String>()
                .cloned()
                .or_else(|| panic.downcast_ref::<&str>().map(|s| s.to_string()))
                .unwrap_or_else(|| "native application panicked".into());
            return Err(PyRuntimeError::new_err(message));
        }
        if let Some(error) = cleanup.error.lock().expect("error lock poisoned").clone() {
            return Err(PyRuntimeError::new_err(error));
        }
        Ok(())
    }
    /// Wake a reader if startup failed before entering the native loop.
    fn finish(&self) {
        self.transport.finish();
    }
}

impl Bridge {
    fn send(&self, command: Command) -> PyResult<()> {
        self.transport
            .commands
            .try_send(command)
            .map_err(|e| PyRuntimeError::new_err(format!("native command queue unavailable: {e}")))
    }
}
