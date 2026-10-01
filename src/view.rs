use crate::{
    bridge::Transport,
    kit::{NativeKit, NativeState, Props, TableData},
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
    Button {
        text: SharedString,
        disabled: bool,
        variant: String,
        icon: SharedString,
    },
    Kit(NativeKit),
}

pub(crate) struct NativeView {
    roots: Vec<u64>,
    controls: HashMap<u64, NativeControl>,
    styles: HashMap<u64, serde_json::Map<String, Value>>,
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
            styles: HashMap::new(),
            transport,
            _subscriptions: Vec::new(),
            _commands: task,
        };
        view.mount(nodes, window, cx);
        let initial_overlays: Vec<_> = view
            .controls
            .iter()
            .filter_map(|(id, c)| match c {
                NativeControl::Kit(k)
                    if matches!(k.kind.as_str(), "dialog" | "sheet")
                        && k.props["value"] == true =>
                {
                    Some(*id)
                }
                _ => None,
            })
            .collect();
        for id in initial_overlays {
            view.open_overlay(id, window, cx);
        }
        view
    }
    fn mount(&mut self, nodes: Vec<Node>, window: &mut Window, cx: &mut Context<Self>) {
        for node in nodes {
            self.styles.insert(node.id, node.style);
            let control = match node.control {
                Control::Column { children } => {
                    let ids: Vec<u64> = children.iter().map(|n| n.id).collect();
                    self.mount(children, window, cx);
                    NativeControl::Column(ids)
                }
                Control::Label { text } => NativeControl::Label(text.into()),
                Control::Button {
                    text,
                    disabled,
                    variant,
                    icon,
                } => NativeControl::Button {
                    text: text.into(),
                    disabled,
                    variant,
                    icon: icon.into(),
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
                Control::Kit {
                    kind,
                    props,
                    children,
                } => {
                    let ids: Vec<u64> = children.iter().map(|n| n.id).collect();
                    self.mount(children, window, cx);
                    let p = Props(&props);
                    let id = node.id;
                    let state = match kind.as_str() {
                        "slider" => {
                            use gpui_kit::component::slider::{
                                SliderEvent, SliderState, SliderValue,
                            };
                            let state = cx.new(|_| {
                                SliderState::new()
                                    .min(p.n("minimum"))
                                    .max(p.n("maximum"))
                                    .step(p.n("step"))
                                    .default_value(p.n("value"))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| match event {
                                    SliderEvent::Change(SliderValue::Single(value)) => {
                                        view.change(id, json!(value), cx)
                                    }
                                    SliderEvent::Release(SliderValue::Single(value)) => {
                                        view.event(id, "release", json!(value), cx)
                                    }
                                    _ => (),
                                },
                            ));
                            NativeState::Slider(state)
                        }
                        "select" => {
                            use gpui_kit::component::select::{SelectEvent, SelectState};
                            let items = p.strings("items");
                            let index = items
                                .iter()
                                .position(|s| *s == p.s("value"))
                                .map(|i| gpui_kit::component::IndexPath::default().row(i));
                            let state = cx.new(|cx| SelectState::new(items, index, window, cx));
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event: &SelectEvent<Vec<SharedString>>, _, cx| {
                                    let SelectEvent::Confirm(value) = event;
                                    view.change(
                                        id,
                                        json!(
                                            value.as_ref().map(SharedString::as_str).unwrap_or("")
                                        ),
                                        cx,
                                    );
                                },
                            ));
                            NativeState::Select(state)
                        }
                        "table" => {
                            use gpui_kit::component::table::{TableEvent, TableState};
                            let state = cx.new(|cx| {
                                TableState::new(
                                    TableData {
                                        columns: p.strings("columns"),
                                        rows: p.rows("rows"),
                                        width: p.n("column_width"),
                                    },
                                    window,
                                    cx,
                                )
                                .sortable(false)
                                .col_movable(false)
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    if let TableEvent::SelectRow(value) = event {
                                        view.change(id, json!(value), cx);
                                    }
                                },
                            ));
                            NativeState::Table(state)
                        }
                        "combobox" => {
                            use gpui_kit::component::combobox::{ComboboxEvent, ComboboxState};
                            let state = cx.new(|cx| {
                                ComboboxState::new(p.strings("items"), vec![], window, cx)
                                    .searchable(true)
                            });
                            state.update(cx, |state, cx| {
                                state.set_selected_values(&[p.s("value")], window, cx)
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event: &ComboboxEvent<Vec<SharedString>>, _, cx| {
                                    if let ComboboxEvent::Change(values) = event {
                                        view.change(
                                            id,
                                            json!(
                                                values
                                                    .first()
                                                    .map(SharedString::as_str)
                                                    .unwrap_or("")
                                            ),
                                            cx,
                                        );
                                    }
                                },
                            ));
                            NativeState::Combobox(state)
                        }
                        "textarea" => {
                            use gpui_kit::component::input::TextareaState;
                            let state = cx.new(|cx| {
                                TextareaState::new(window, cx)
                                    .default_value(p.s("value"))
                                    .placeholder(p.s("placeholder"))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, state, event, _, cx| {
                                    if matches!(event, InputEvent::Change) {
                                        view.change(id, json!(state.read(cx).value().as_str()), cx);
                                    }
                                },
                            ));
                            NativeState::Textarea(state)
                        }
                        "number_input" => {
                            let state = cx.new(|cx| {
                                InputState::new(window, cx)
                                    .default_value(p.s("value"))
                                    .placeholder(p.s("placeholder"))
                                    .step(1.)
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, state, event, _, cx| {
                                    if matches!(event, InputEvent::Change) {
                                        view.change(id, json!(state.read(cx).value().as_str()), cx);
                                    }
                                },
                            ));
                            NativeState::Number(state)
                        }
                        "otp_input" => {
                            use gpui_kit::component::input::{OtpEvent, OtpState};
                            let state = cx.new(|cx| {
                                OtpState::new(p.ix("length"), window, cx)
                                    .default_value(p.s("value"))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, state, event, _, cx| {
                                    if matches!(event, OtpEvent::Change) {
                                        view.change(id, json!(state.read(cx).value().as_str()), cx);
                                    }
                                },
                            ));
                            NativeState::Otp(state)
                        }
                        "calendar" => {
                            use gpui_kit::component::calendar::{CalendarEvent, CalendarState};
                            let state = cx.new(|cx| CalendarState::new(window, cx));
                            state.update(cx, |state, cx| {
                                state.set_date(crate::kit::date_value(&p.s("value")), window, cx)
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    let CalendarEvent::Selected(date) = event;
                                    view.change(id, json!(crate::kit::date_string(*date)), cx);
                                },
                            ));
                            NativeState::Calendar(state)
                        }
                        "date_picker" => {
                            use gpui_kit::component::date_picker::{
                                DatePickerEvent, DatePickerState,
                            };
                            let state = cx.new(|cx| DatePickerState::new(window, cx));
                            state.update(cx, |state, cx| {
                                state.set_date(crate::kit::date_value(&p.s("value")), window, cx)
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    let DatePickerEvent::Change(date) = event;
                                    view.change(
                                        id,
                                        json!(crate::kit::date_string(date.date())),
                                        cx,
                                    );
                                },
                            ));
                            NativeState::DatePicker(state)
                        }
                        "time_field" => {
                            use gpui_kit::component::time_field::{
                                TimeFieldEvent, TimeFieldState, TimePrecision,
                            };
                            let state = cx.new(|cx| {
                                TimeFieldState::new(window, cx).precision(TimePrecision::Second)
                            });
                            state.update(cx, |state, cx| {
                                state.set_time(
                                    chrono::NaiveTime::parse_from_str(&p.s("value"), "%H:%M:%S")
                                        .unwrap(),
                                    window,
                                    cx,
                                )
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    let TimeFieldEvent::Change(time) = event;
                                    view.change(id, json!(time.format("%H:%M:%S").to_string()), cx);
                                },
                            ));
                            NativeState::Time(state)
                        }
                        "color_picker" => {
                            use gpui_kit::component::Colorize;
                            use gpui_kit::component::color_picker::{
                                ColorPickerEvent, ColorPickerState,
                            };
                            let state = cx.new(|cx| {
                                ColorPickerState::new(window, cx)
                                    .default_value(crate::kit::color_value(&p.s("value")))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    let ColorPickerEvent::Change(color) = event;
                                    if let Some(color) = color {
                                        view.change(id, json!(color.to_hex()), cx);
                                    }
                                },
                            ));
                            NativeState::Color(state)
                        }
                        "carousel" => {
                            use gpui_kit::component::carousel::{CarouselEvent, CarouselState};
                            let state = cx.new(|_| {
                                CarouselState::new(ids.len()).with_selected_index(p.ix("value"))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, _, event, _, cx| {
                                    let CarouselEvent::Change(index) = event;
                                    view.change(id, json!(index), cx);
                                },
                            ));
                            NativeState::Carousel(state)
                        }
                        "editor" => {
                            use gpui_kit::component::input::EditorState;
                            let state = cx.new(|cx| {
                                EditorState::new(window, cx)
                                    .default_value(p.s("value"))
                                    .placeholder(p.s("placeholder"))
                            });
                            self._subscriptions.push(cx.subscribe_in(
                                &state,
                                window,
                                move |view, state, event, _, cx| {
                                    if matches!(event, InputEvent::Change) {
                                        view.change(id, json!(state.read(cx).value().as_str()), cx);
                                    }
                                },
                            ));
                            NativeState::Editor(state)
                        }
                        "tree" => {
                            use gpui_kit::component::tree::{TreeItem, TreeState};
                            let state = cx.new(|cx| {
                                TreeState::new(cx).items(crate::kit::tree_items(&props["items"]))
                            });
                            state.update(cx, |state, cx| {
                                let item = TreeItem::new(p.s("value"), "");
                                state.set_selected_item(
                                    if p.s("value").is_empty() {
                                        None
                                    } else {
                                        Some(&item)
                                    },
                                    cx,
                                );
                            });
                            self._subscriptions
                                .push(cx.observe(&state, move |view, state, cx| {
                                    view.change(
                                        id,
                                        json!(
                                            state
                                                .read(cx)
                                                .selected_item()
                                                .map(|item| item.id.as_str())
                                                .unwrap_or("")
                                        ),
                                        cx,
                                    )
                                }));
                            NativeState::Tree(state)
                        }
                        "resizable" => NativeState::Resizable(
                            cx.new(|_| gpui_kit::component::ResizableState::default()),
                        ),
                        _ => NativeState::None,
                    };
                    NativeControl::Kit(NativeKit {
                        kind,
                        props,
                        children: ids,
                        state,
                    })
                }
            };
            self.controls.insert(node.id, control);
        }
    }
    fn values(&self, cx: &App) -> BTreeMap<u64, Value> {
        self.controls
            .iter()
            .filter_map(|(id, control)| {
                if let NativeControl::Input(input) = control {
                    Some((*id, json!(input.read(cx).value().as_str())))
                } else if let NativeControl::Kit(kit) = control {
                    kit.value(cx).map(|value| (*id, value))
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
                    NativeControl::Button { text, disabled, .. } => {
                        json!({"type":"button", "text":text.as_str(), "disabled":disabled})
                    }
                    NativeControl::Kit(kit) => {
                        let mut props = kit.props.clone();
                        props.insert("type".into(), json!(kit.kind));
                        props.insert("children".into(), json!(kit.children));
                        if let Some(value) = kit.value(cx) {
                            props.insert("value".into(), value);
                        }
                        Value::Object(props)
                    }
                };
                (*id, value)
            })
            .collect()
    }
    fn apply(&mut self, command: Command, window: &mut Window, cx: &mut Context<Self>) {
        match command {
            Command::Close => cx.quit(),
            Command::Notify {
                message,
                title,
                variant,
            } => {
                use gpui_kit::component::{
                    WindowExt,
                    notification::{Notification, NotificationType},
                };
                window.push_notification(
                    Notification::new().message(message).title(title).with_type(
                        match variant.as_str() {
                            "success" => NotificationType::Success,
                            "warning" => NotificationType::Warning,
                            "danger" => NotificationType::Error,
                            _ => NotificationType::Info,
                        },
                    ),
                    cx,
                );
            }
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
                    if property == "style" {
                        self.styles
                            .insert(id, value.as_object().expect("validated style").clone());
                        continue;
                    }
                    // The bridge validates the whole batch against the immutable schema.
                    let overlay_change = matches!(&self.controls[&id], NativeControl::Kit(k) if matches!(k.kind.as_str(), "dialog" | "sheet") && property == "value");
                    match self.controls.get_mut(&id).expect("validated control ID") {
                        NativeControl::Label(text) => {
                            *text = value.as_str().expect("validated string").to_owned().into()
                        }
                        NativeControl::Button { text, disabled, .. } => {
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
                        NativeControl::Kit(kit) => kit.apply(&property, value, window, cx),
                    }
                    if overlay_change {
                        self.open_overlay(id, window, cx);
                    }
                }
                if changed {
                    cx.notify();
                }
            }
        }
    }
    pub(crate) fn change(&mut self, id: u64, value: Value, cx: &mut Context<Self>) {
        if let NativeControl::Kit(kit) = self.controls.get_mut(&id).expect("mounted Kit control") {
            if kit.props.get("value") == Some(&value) {
                return;
            }
            kit.props.insert("value".into(), value.clone());
            if !self
                .transport
                .emit(json!({"event":"change", "id":id, "value":value, "values":self.values(cx)}))
            {
                cx.quit();
            }
            cx.notify();
        }
    }
    fn open_overlay(&mut self, id: u64, window: &mut Window, cx: &mut Context<Self>) {
        use gpui_kit::component::WindowExt;
        let NativeControl::Kit(kit) = &self.controls[&id] else {
            unreachable!()
        };
        let sheet = kit.kind == "sheet";
        if !kit.props["value"].as_bool().unwrap() {
            if sheet {
                window.close_sheet(cx);
            } else {
                window.close_dialog(cx);
            }
            return;
        }
        let title = Props(&kit.props).s("title");
        let children = kit.children.clone();
        let view = cx.entity();
        let close = std::rc::Rc::new(
            cx.listener(move |view, _: &ClickEvent, _, cx| view.change(id, json!(false), cx)),
        );
        if sheet {
            window.open_sheet(cx, move |sheet, _, cx| {
                sheet
                    .title(title.clone())
                    .on_close({
                        let close = close.clone();
                        move |e, w, cx| close(e, w, cx)
                    })
                    .child(view.update(cx, |v, cx| {
                        div()
                            .flex()
                            .flex_col()
                            .gap_3()
                            .children(children.iter().map(|id| v.render_control(*id, cx)))
                    }))
            });
        } else {
            window.open_dialog(cx, move |dialog, _, cx| {
                dialog
                    .title(title.clone())
                    .on_close({
                        let close = close.clone();
                        move |e, w, cx| close(e, w, cx)
                    })
                    .child(view.update(cx, |v, cx| {
                        div()
                            .flex()
                            .flex_col()
                            .gap_3()
                            .children(children.iter().map(|id| v.render_control(*id, cx)))
                    }))
            });
        }
    }
    pub(crate) fn toggle(&mut self, id: u64, cx: &mut Context<Self>) {
        if let NativeControl::Kit(kit) = &self.controls[&id] {
            self.change(id, json!(!kit.props["value"].as_bool().unwrap()), cx);
        }
    }
    pub(crate) fn click(&mut self, id: u64, cx: &mut Context<Self>) {
        if !self
            .transport
            .emit(json!({"event":"click", "id":id, "values":self.values(cx)}))
        {
            cx.quit();
        }
    }
    pub(crate) fn event(&mut self, id: u64, event: &str, value: Value, cx: &mut Context<Self>) {
        if !self
            .transport
            .emit(json!({"event":event, "id":id, "value":value, "values":self.values(cx)}))
        {
            cx.quit();
        }
    }
    pub(crate) fn render_control(&self, id: u64, cx: &Context<Self>) -> AnyElement {
        let element = match &self.controls[&id] {
            NativeControl::Column(children) => {
                return crate::kit::apply_style(
                    div().id(("column", id)).flex().flex_col().gap_3(),
                    &self.styles[&id],
                    cx,
                )
                .children(children.iter().map(|id| self.render_control(*id, cx)))
                .into_any_element();
            }
            NativeControl::Label(text) => div()
                .id(("label", id))
                .child(Label::new(text.clone()))
                .into_any_element(),
            NativeControl::Input(input) => Input::new(input)
                .id(("input", id))
                .w_full()
                .into_any_element(),
            NativeControl::Button {
                text,
                disabled,
                variant,
                icon,
            } => {
                use gpui_kit::component::Disableable;
                use gpui_kit::{component::button::ButtonVariants, prelude::FluentBuilder};
                Button::new(("button", id))
                    .label(text.clone())
                    .disabled(*disabled)
                    .map(|b| match variant.as_str() {
                        "primary" => b.primary(),
                        "outline" => b.outline(),
                        "ghost" => b.ghost(),
                        "danger" => b.danger(),
                        _ => b,
                    })
                    .when(!icon.is_empty(), |b| {
                        b.icon(
                            gpui_kit::component::Icon::default().path(format!("icons/{icon}.svg")),
                        )
                    })
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
            NativeControl::Kit(kit) => kit.render(
                id,
                kit.children
                    .iter()
                    .map(|id| self.render_control(*id, cx))
                    .collect(),
                &self.styles[&id],
                cx,
            ),
        };
        if matches!(&self.controls[&id], NativeControl::Kit(k) if matches!(k.kind.as_str(), "row" | "container" | "scroll"))
        {
            element
        } else {
            crate::kit::styled(id, element, &self.styles[&id], cx)
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
