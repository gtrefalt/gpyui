use crate::protocol::{self, Command, ControlType, Node, Patch};
use async_channel::{Receiver, Sender};
use gpui_kit::*;
use pyo3::{
    exceptions::{PyRuntimeError, PyValueError},
    prelude::*,
};
use serde_json::{Value, json};
use std::{
    collections::HashMap,
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

/// Thread-safe transport containing no Python callbacks or GPUI handles.
#[pyclass]
pub(crate) struct Bridge {
    transport: Arc<Transport>,
    event_receiver: Receiver<Value>,
    native: Mutex<Option<(Vec<Node>, Receiver<Command>)>>,
    schema: HashMap<u64, ControlType>,
}

#[pymethods]
impl Bridge {
    #[new]
    fn new(tree_json: &str) -> PyResult<Self> {
        let nodes: Vec<Node> =
            serde_json::from_str(tree_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        let schema = protocol::schema(&nodes).map_err(PyValueError::new_err)?;
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
            native: Mutex::new(Some((nodes, receiver))),
            schema,
        })
    }
    /// Validate the entire batch before enqueueing any update.
    fn submit(&self, batch_json: &str) -> PyResult<()> {
        let patches: Vec<Patch> =
            serde_json::from_str(batch_json).map_err(|e| PyValueError::new_err(e.to_string()))?;
        protocol::validate_batch(&patches, &self.schema).map_err(PyValueError::new_err)?;
        self.send(Command::Batch(patches))
    }
    fn snapshot(&self, token: u64) -> PyResult<()> {
        self.send(Command::Snapshot(token))
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
    fn run(&self, py: Python<'_>, title: String, width: f32, height: f32) -> PyResult<()> {
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
        let (nodes, commands) = self
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
                    .with_assets(gpui_kit::assets::Assets)
                    .run(move |cx| {
                        gpui_kit::init(cx);
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
                                    commands,
                                    view_transport,
                                    window,
                                    cx,
                                )
                            })
                        }) {
                            Ok(_) => {
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
