use crate::{
    bridge::Transport,
    protocol::{Command, Control, Node, Patch},
};
use async_channel::Receiver;
use gpui_kit::{
    component::{
        ActiveTheme,
        button::Button,
        input::{Input, InputEvent, InputState},
        label::Label,
    },
    *,
};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, HashMap},
    sync::Arc,
};

enum NativeControl {
    Column(Vec<u64>),
    Label(SharedString),
    Input(Entity<InputState>),
    Button { text: SharedString, disabled: bool },
}

pub(crate) struct NativeView {
    roots: Vec<u64>,
    controls: HashMap<u64, NativeControl>,
    transport: Arc<Transport>,
    _subscriptions: Vec<Subscription>,
    _commands: Task<()>,
}

impl NativeView {
    pub(crate) fn new(
        nodes: Vec<Node>,
        commands: Receiver<Command>,
        transport: Arc<Transport>,
        window: &mut Window,
        cx: &mut Context<Self>,
    ) -> Self {
        let task = cx.spawn_in(window, async move |view, cx| {
            while let Ok(command) = commands.recv().await {
                if view
                    .update_in(cx, |view, window, cx| view.apply(command, window, cx))
                    .is_err()
                {
                    break;
                }
            }
        });
        let mut view = Self {
            roots: nodes.iter().map(|n| n.id).collect(),
            controls: HashMap::new(),
            transport,
            _subscriptions: Vec::new(),
            _commands: task,
        };
        view.mount(nodes, window, cx);
        view
    }
    fn mount(&mut self, nodes: Vec<Node>, window: &mut Window, cx: &mut Context<Self>) {
        for node in nodes {
            let control = match node.control {
                Control::Column { children } => {
                    let ids = children.iter().map(|n| n.id).collect();
                    self.mount(children, window, cx);
                    NativeControl::Column(ids)
                }
                Control::Label { text } => NativeControl::Label(text.into()),
                Control::Button { text, disabled } => NativeControl::Button {
                    text: text.into(),
                    disabled,
                },
                Control::Input { value, placeholder } => {
                    let input = cx.new(|cx| {
                        InputState::new(window, cx)
                            .default_value(value)
                            .placeholder(placeholder)
                    });
                    let id = node.id;
                    self._subscriptions.push(cx.subscribe_in(&input, window, move |view, input, event, _, cx| {
                        if matches!(event, InputEvent::Change)
                            && !view.transport.emit(json!({"event":"change", "id":id, "value":input.read(cx).value().as_str()})) { cx.quit(); }
                    }));
                    NativeControl::Input(input)
                }
            };
            self.controls.insert(node.id, control);
        }
    }
    fn values(&self, cx: &App) -> BTreeMap<u64, String> {
        self.controls
            .iter()
            .filter_map(|(id, control)| {
                if let NativeControl::Input(input) = control {
                    Some((*id, input.read(cx).value().to_string()))
                } else {
                    None
                }
            })
            .collect()
    }
    fn snapshot(&self, cx: &App) -> BTreeMap<u64, Value> {
        self.controls
            .iter()
            .map(|(id, control)| {
                let value = match control {
                    NativeControl::Column(children) => {
                        json!({"type":"column", "children":children})
                    }
                    NativeControl::Label(text) => json!({"type":"label", "text":text.as_str()}),
                    NativeControl::Input(input) => {
                        json!({"type":"input", "value":input.read(cx).value().as_str()})
                    }
                    NativeControl::Button { text, disabled } => {
                        json!({"type":"button", "text":text.as_str(), "disabled":disabled})
                    }
                };
                (*id, value)
            })
            .collect()
    }
    fn apply(&mut self, command: Command, window: &mut Window, cx: &mut Context<Self>) {
        match command {
            Command::Close => cx.quit(),
            Command::Snapshot(token) => {
                if !self
                    .transport
                    .emit(json!({"event":"snapshot", "token":token, "nodes":self.snapshot(cx)}))
                {
                    cx.quit();
                }
            }
            Command::Batch(patches) => {
                let changed = !patches.is_empty();
                for Patch {
                    id,
                    property,
                    value,
                } in patches
                {
                    // The bridge validates the whole batch against the immutable schema.
                    match self.controls.get_mut(&id).expect("validated control ID") {
                        NativeControl::Label(text) => {
                            *text = value.as_str().expect("validated string").to_owned().into()
                        }
                        NativeControl::Button { text, disabled } => {
                            if property == "text" {
                                *text = value.as_str().expect("validated string").to_owned().into();
                            } else {
                                *disabled = value.as_bool().expect("validated bool");
                            }
                        }
                        NativeControl::Input(input) => input.update(cx, |input, cx| {
                            let text = value.as_str().expect("validated string").to_owned();
                            if property == "value" {
                                input.set_value(text, window, cx);
                            } else {
                                input.set_placeholder(text, window, cx);
                            }
                        }),
                        NativeControl::Column(_) => {
                            unreachable!("columns have no mutable properties")
                        }
                    }
                }
                if changed {
                    cx.notify();
                }
            }
        }
    }
    fn render_control(&self, id: u64, cx: &Context<Self>) -> AnyElement {
        match &self.controls[&id] {
            NativeControl::Column(children) => div()
                .id(("column", id))
                .flex()
                .flex_col()
                .gap_3()
                .children(children.iter().map(|id| self.render_control(*id, cx)))
                .into_any_element(),
            NativeControl::Label(text) => div()
                .id(("label", id))
                .child(Label::new(text.clone()))
                .into_any_element(),
            NativeControl::Input(input) => Input::new(input)
                .id(("input", id))
                .w_full()
                .into_any_element(),
            NativeControl::Button { text, disabled } => {
                use gpui_kit::component::Disableable;
                Button::new(("button", id))
                    .label(text.clone())
                    .disabled(*disabled)
                    .on_click(cx.listener(move |view, _, _, cx| {
                        if !view
                            .transport
                            .emit(json!({"event":"click", "id":id, "values":view.values(cx)}))
                        {
                            cx.quit();
                        }
                    }))
                    .into_any_element()
            }
        }
    }
}

impl Render for NativeView {
    fn render(&mut self, _: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        div()
            .size_full()
            .p_6()
            .flex()
            .flex_col()
            .gap_3()
            .bg(cx.theme().background)
            .text_color(cx.theme().foreground)
            .children(self.roots.iter().map(|id| self.render_control(*id, cx)))
    }
}
