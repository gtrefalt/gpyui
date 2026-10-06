use crate::{
    bridge::Transport,
    commands::{self, Actions, ContextMenuSpec, InvokeCommand, MenuEntry, Popups, UiConfig},
    kit::{NativeKit, NativeState, Props, TableData},
    protocol::{Command, Control, Node, Patch},
};
use async_channel::Receiver;
use gpui_kit::{
    component::{
        ActiveTheme,
        button::Button,
        input::{AnyInputState, Input, InputEvent, InputState},
        label::Label,
    },
    *,
};
use serde_json::{Value, json};
use std::{
    cell::RefCell,
    collections::{BTreeMap, HashMap, HashSet},
    rc::Rc,
    sync::Arc,
};

enum NativeControl {
    Column(Vec<u64>),
    Label(SharedString),
    Input(Entity<InputState>),
    DropdownMenu {
        text: SharedString,
        items: Vec<MenuEntry>,
        disabled: bool,
    },
    Button {
        command: Option<u64>,
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
    subscriptions: HashMap<u64, Vec<Subscription>>,
    visible: HashMap<u64, bool>,
    attached: HashSet<u64>,
    displayed: HashSet<u64>,
    opened: HashMap<String, u64>,
    actions: Actions,
    bound_actions: HashSet<u64>,
    menus: Vec<MenuEntry>,
    menus_dirty: bool,
    popups_dirty: bool,
    rendered: bool,
    menu_bar: Option<Entity<gpui_kit::component::menu::AppMenuBar>>,
    popups: Popups,
    context_menus: HashMap<u64, ContextMenuSpec>,
    focus: FocusHandle,
    window_state: crate::windows::WindowState,
    _window_bounds: Subscription,
    _commands: Task<()>,
}

impl NativeView {
    pub(crate) fn new(
        nodes: Vec<Node>,
        config: UiConfig,
        commands: Receiver<Command>,
        transport: Arc<Transport>,
        window_state: crate::windows::WindowState,
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
        let bounds_subscription = cx.observe_window_bounds(window, |view, window, _| {
            view.window_state.enforce_size(window);
        });
        let mut view = Self {
            roots: nodes.iter().map(|n| n.id).collect(),
            controls: HashMap::new(),
            styles: HashMap::new(),
            transport,
            subscriptions: HashMap::new(),
            visible: HashMap::new(),
            attached: HashSet::new(),
            displayed: HashSet::new(),
            opened: HashMap::new(),
            actions: Rc::new(RefCell::new(HashMap::new())),
            bound_actions: HashSet::new(),
            menus: Vec::new(),
            menus_dirty: true,
            popups_dirty: true,
            rendered: false,
            menu_bar: None,
            popups: Rc::new(RefCell::new(HashMap::new())),
            context_menus: HashMap::new(),
            focus: cx.focus_handle(),
            window_state,
            _window_bounds: bounds_subscription,
            _commands: task,
        };
        window.focus(&view.focus, cx);
        view.configure(config, cx);
        view.mount(nodes, window, cx);
        view.refresh(window, cx);
        view
    }
    fn mount(&mut self, nodes: Vec<Node>, window: &mut Window, cx: &mut Context<Self>) {
        for node in nodes {
            if self.controls.contains_key(&node.id) {
                if let Control::Column { children } | Control::Kit { children, .. } = node.control {
                    let ids = children.iter().map(|child| child.id).collect();
                    self.mount(children, window, cx);
                    match self.controls.get_mut(&node.id).expect("retained control") {
                        NativeControl::Column(children) => *children = ids,
                        NativeControl::Kit(kit) => kit.children = ids,
                        _ => unreachable!("validated retained container"),
                    }
                }
                continue;
            }
            let mut subscriptions = Vec::new();
            if let Some(menu) = node.context_menu {
                self.context_menus.insert(node.id, menu);
            }
            self.visible.insert(node.id, node.visible);
            self.styles.insert(node.id, node.style);
            let control = match node.control {
                Control::Column { children } => {
                    let ids: Vec<u64> = children.iter().map(|n| n.id).collect();
                    self.mount(children, window, cx);
                    NativeControl::Column(ids)
                }
                Control::Label { text } => NativeControl::Label(text.into()),
                Control::DropdownMenu {
                    text,
                    items,
                    disabled,
                } => NativeControl::DropdownMenu {
                    text: text.into(),
                    items,
                    disabled,
                },
                Control::Button {
                    command,
                    text,
                    disabled,
                    variant,
                    icon,
                } => NativeControl::Button {
                    command,
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
                    subscriptions.push(cx.subscribe_in(&input, window, move |view, input, event, _, cx| {
                        if view.displayed.contains(&id) && matches!(event, InputEvent::Change)
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.subscribe_in(
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
                            subscriptions.push(cx.observe(&state, move |view, state, cx| {
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
                        "image" => {
                            let state = cx.new(|_| crate::images::NativeImage::new(&props));
                            subscriptions.push(cx.subscribe(&state, move |view, _, event: &crate::images::ImageEvent, cx| {
                                if view.displayed.contains(&id) && !view.transport.emit(json!({
                                    "event":event.name, "id":id, "revision":event.revision, "value":event.value
                                })) { cx.quit(); }
                                cx.notify();
                            }));
                            NativeState::Image(state)
                        }
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
            self.subscriptions.insert(node.id, subscriptions);
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
        let mut snapshot: BTreeMap<u64, Value> = self.controls
            .iter()
            .map(|(id, control)| {
                let mut value = match control {
                    NativeControl::Column(children) => {
                        json!({"type":"column", "children":children})
                    }
                    NativeControl::Label(text) => json!({"type":"label", "text":text.as_str()}),
                    NativeControl::Input(input) => {
                        json!({"type":"input", "value":input.read(cx).value().as_str()})
                    }
                    NativeControl::Button { text, disabled, command, .. } => {
                        json!({"type":"button", "text":text.as_str(), "disabled":*disabled || command.is_some_and(|id| !self.actions.borrow()[&id].enabled), "command":command})
                    }
                    NativeControl::DropdownMenu { text, items, disabled } => json!({"type":"dropdown_menu", "text":text.as_str(), "items":items, "disabled":disabled}),
                    NativeControl::Kit(kit) => {
                        let mut props = kit.props.clone();
                        props.insert("type".into(), json!(kit.kind));
                        props.insert("children".into(), json!(kit.children));
                        if let Some(value) = kit.value(cx) {
                            props.insert("value".into(), value);
                        }
                        if let NativeState::Image(state) = &kit.state {
                            props.insert("image".into(), state.read(cx).status());
                        }
                        Value::Object(props)
                    }
                };
                value["context_menu"] = json!(self.context_menus.get(id));
                value["visible"] = json!(self.visible[id]);
                value["attached"] = json!(self.attached.contains(id));
                value["displayed"] = json!(self.displayed.contains(id));
                (*id, value)
            })
            .collect();
        for (id, command) in self.actions.borrow().iter() {
            snapshot.insert(*id, json!({"type":"command", "label":command.label, "shortcut":command.shortcut, "enabled":command.enabled, "checked":command.checked}));
        }
        snapshot
    }
    fn apply(&mut self, command: Command, window: &mut Window, cx: &mut Context<Self>) {
        let focused = self.focused_control(window, cx);
        match command {
            Command::Theme(config) => {
                crate::theme::apply(*config, cx);
                cx.notify();
            }
            Command::ThemeSnapshot(token) => {
                if !self.transport.emit(json!({"event":"theme_snapshot", "token":token, "theme":crate::theme::snapshot(cx)})) {
                    cx.quit();
                }
            }
            Command::Window(command) => {
                use crate::windows::WindowCommand as W;
                match command {
                    W::Title(title) => { window.set_window_title(&title); self.window_state.title = title; },
                    W::Resize(width, height) => {
                        if self.window_state.config.validate_size(width, height).is_ok() {
                            self.window_state.resize(width, height, window);
                        }
                    },
                    W::Activate => window.activate_window(),
                    W::Minimize if self.window_state.config.minimizable => window.minimize_window(),
                    W::ToggleMaximized if self.window_state.config.resizable => window.zoom_window(),
                    W::ToggleFullscreen => window.toggle_fullscreen(),
                    W::Snapshot(token) if !self.transport.emit(json!({"event":"window_snapshot", "token":token,
                        "window":self.window_state.snapshot(window)})) => { cx.quit(); },
                    _ => {},
                }
            }
            Command::Execute(id) => self.invoke(id, None, cx),
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
            Command::Reconcile {
                nodes,
                roots,
                patches,
                retained,
                config,
            } => {
                self.configure(config, cx);
                self.mount(nodes, window, cx);
                self.roots = roots;
                for (id, control) in &self.controls {
                    if !retained.contains(id)
                        && let NativeControl::Kit(kit) = control
                        && let NativeState::Image(state) = &kit.state {
                        state.update(cx, |image, cx| image.release(window, cx));
                    }
                }
                self.controls.retain(|id, _| retained.contains(id));
                self.styles.retain(|id, _| retained.contains(id));
                self.visible.retain(|id, _| retained.contains(id));
                self.context_menus.retain(|id, _| retained.contains(id));
                self.subscriptions.retain(|id, _| retained.contains(id));
                self.apply_patches(patches, window, cx);
                self.refresh(window, cx);
                cx.notify();
            }
            Command::Batch(patches) => {
                let changed = !patches.is_empty();
                self.apply_patches(patches, window, cx);
                if changed {
                    self.refresh(window, cx);
                    cx.notify();
                }
            }
        }
        if focused.is_some_and(|id| !self.displayed.contains(&id)) {
            window.blur(cx);
        }
    }
    fn apply_patches(&mut self, patches: Vec<Patch>, window: &mut Window, cx: &mut Context<Self>) {
        for Patch {
            id,
            property,
            value,
        } in patches
        {
            if let Some(command) = self.actions.borrow_mut().get_mut(&id) {
                self.menus_dirty = true;
                self.popups_dirty = true;
                if property == "enabled" {
                    command.enabled = value.as_bool().expect("validated enabled");
                } else {
                    command.checked = value.as_bool().expect("validated checked");
                }
                continue;
            }
            if property == "context_menu" {
                self.popups_dirty = true;
                if value.is_null() {
                    self.context_menus.remove(&id);
                } else {
                    self.context_menus.insert(
                        id,
                        serde_json::from_value(value).expect("validated context menu"),
                    );
                }
                continue;
            }
            if property == "visible" {
                self.visible
                    .insert(id, value.as_bool().expect("validated visibility"));
                continue;
            }
            if property == "style" {
                self.styles
                    .insert(id, value.as_object().expect("validated style").clone());
                continue;
            }
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
                NativeControl::DropdownMenu {
                    text,
                    items,
                    disabled,
                } => {
                    self.popups_dirty = true;
                    match property.as_str() {
                        "text" => *text = value.as_str().expect("validated text").to_owned().into(),
                        "items" => {
                            *items = serde_json::from_value(value).expect("validated menu items")
                        }
                        _ => *disabled = value.as_bool().expect("validated disabled"),
                    }
                }
                NativeControl::Column(_) => unreachable!("columns have no component properties"),
                NativeControl::Kit(kit) => kit.apply(&property, value, window, cx),
            }
        }
    }
    fn configure(&mut self, config: UiConfig, cx: &mut Context<Self>) {
        let retained: HashSet<_> = config.commands.iter().map(|command| command.id).collect();
        self.actions
            .borrow_mut()
            .retain(|id, _| retained.contains(id));
        for command in config.commands {
            if self.bound_actions.insert(command.id) && !command.shortcut.is_empty() {
                cx.bind_keys([KeyBinding::new(
                    &command.shortcut,
                    InvokeCommand { id: command.id },
                    Some("Gpyui"),
                )]);
            }
            if !self.actions.borrow().contains_key(&command.id) {
                self.menus_dirty = true;
                self.popups_dirty = true;
            }
            self.actions
                .borrow_mut()
                .entry(command.id)
                .or_insert(command);
        }
        if self.menus != config.menus {
            self.menus_dirty = true;
        }
        self.menus = config.menus;
    }

    pub(crate) fn invoke(&mut self, id: u64, source: Option<u64>, cx: &mut Context<Self>) {
        if !self
            .actions
            .borrow()
            .get(&id)
            .is_some_and(|command| command.enabled)
        {
            return;
        }
        if let Some(source) = source {
            if !self.displayed.contains(&source) {
                return;
            }
            let allowed = match self.controls.get(&source) {
                Some(NativeControl::Button {
                    command: Some(command),
                    disabled,
                    ..
                }) => *command == id && !disabled,
                Some(NativeControl::DropdownMenu {
                    items, disabled, ..
                }) => !disabled && commands::has_command(items, id),
                _ => false,
            } || self
                .context_menus
                .get(&source)
                .is_some_and(|menu| commands::has_command(&menu.items, id));
            if !allowed {
                return;
            }
        }
        if !self
            .transport
            .emit(json!({"event":"command", "id":id, "source":source, "values":self.values(cx)}))
        {
            cx.quit();
        }
    }

    fn refresh_menus(&mut self, window: &mut Window, cx: &mut Context<Self>) {
        if self.menus_dirty {
            // AppMenuBar::reload replaces popup entities. Dismiss an active
            // application menu through Kit first so its focus target survives.
            if self.rendered
                && window
                    .context_stack()
                    .iter()
                    .any(|context| context.contains("AppMenuBar"))
                && let Some(focus) = window.focused(cx)
            {
                focus.dispatch_action(&gpui_kit::base::actions::Cancel, window, cx);
            }
            commands::application_menus(&self.menus, &self.actions, &mut self.menu_bar, cx);
            self.menus_dirty = false;
        }
        let popups: Vec<_> = self
            .popups
            .borrow()
            .iter()
            .filter_map(|(key, popup)| popup.upgrade().map(|popup| (*key, popup)))
            .collect();
        for ((id, context), popup) in popups {
            let entries = if context {
                self.context_menus
                    .get(&id)
                    .filter(|menu| !menu.native)
                    .map(|menu| menu.items.clone())
            } else {
                match self.controls.get(&id) {
                    Some(NativeControl::DropdownMenu {
                        items,
                        disabled: false,
                        ..
                    }) => Some(items.clone()),
                    _ => None,
                }
            };
            let Some(entries) = entries.filter(|_| self.displayed.contains(&id)) else {
                // Use Kit's Cancel action before the old dispatch node disappears,
                // preserving its native focus restoration and submenu dismissal.
                let focus = popup.read(cx).focus_handle(cx);
                focus.dispatch_action(&gpui_kit::base::actions::Cancel, window, cx);
                // Also close menus created but not painted yet (no dispatch node).
                popup.update(cx, |_, cx| cx.emit(DismissEvent));
                self.popups.borrow_mut().remove(&(id, context));
                continue;
            };
            if !self.popups_dirty {
                continue;
            }
            let view = cx.weak_entity();
            let actions = self.actions.clone();
            let focus = popup.read(cx).focus_handle(cx);
            let focused = focus.contains_focused(window, cx);
            popup.update(cx, |popup, cx| {
                popup.rebuild(window, cx, |popup, window, cx| {
                    commands::build_popup(popup, &entries, &actions, id, &view, window, cx)
                })
            });
            if focused {
                // Rebuilding closes any old submenu; keep keyboard navigation
                // on the retained root instead of a discarded submenu entity.
                focus.focus(window, cx);
            }
        }
        self.popups
            .borrow_mut()
            .retain(|_, popup| popup.upgrade().is_some());
        self.popups_dirty = false;
    }

    fn focused_control(&self, window: &Window, cx: &App) -> Option<u64> {
        self.controls.iter().find_map(|(id, control)| {
            let focus = match control {
                NativeControl::Input(state) => Some(state.read(cx).focus_handle(cx)),
                NativeControl::Kit(kit) => match &kit.state {
                    NativeState::Textarea(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Number(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Otp(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Editor(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Select(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Combobox(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::DatePicker(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Time(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Color(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Table(state) => Some(state.read(cx).focus_handle(cx)),
                    NativeState::Carousel(state) => Some(state.read(cx).focus_handle(cx)),
                    _ => None,
                },
                _ => None,
            };
            focus
                .filter(|focus| focus.contains_focused(window, cx))
                .map(|_| *id)
        })
    }
    fn refresh(&mut self, window: &mut Window, cx: &mut Context<Self>) {
        fn visit(
            view: &NativeView,
            id: u64,
            shown: bool,
            attached: &mut HashSet<u64>,
            displayed: &mut HashSet<u64>,
        ) {
            attached.insert(id);
            let shown = shown && view.visible[&id];
            if shown {
                displayed.insert(id);
            }
            let children = match &view.controls[&id] {
                NativeControl::Column(children) => children.as_slice(),
                NativeControl::Kit(kit) => kit.children.as_slice(),
                _ => &[],
            };
            for child in children {
                visit(view, *child, shown, attached, displayed);
            }
        }
        let mut attached = HashSet::new();
        let mut displayed = HashSet::new();
        for root in &self.roots {
            visit(self, *root, true, &mut attached, &mut displayed);
        }
        self.attached = attached;
        self.displayed = displayed;
        self.refresh_menus(window, cx);
        let carousels: Vec<_> = self
            .controls
            .iter()
            .filter_map(|(id, control)| {
                if let NativeControl::Kit(kit) = control
                    && let NativeState::Carousel(state) = &kit.state
                {
                    return Some((
                        *id,
                        state.clone(),
                        kit.children.iter().filter(|id| self.visible[id]).count(),
                    ));
                }
                None
            })
            .collect();
        for (id, state, count) in carousels {
            let old = state.read(cx).selected_index();
            state.update(cx, |state, cx| state.set_item_count(count, cx));
            let new = state.read(cx).selected_index();
            if old != new {
                self.change(id, json!(new.unwrap_or(0)), cx);
            }
        }
        for kind in ["dialog", "sheet"] {
            let wanted = self
                .controls
                .iter()
                .find_map(|(id, control)| match control {
                    NativeControl::Kit(kit)
                        if kit.kind == kind
                            && kit.props["value"] == true
                            && self.displayed.contains(id) =>
                    {
                        Some(*id)
                    }
                    _ => None,
                });
            if self.opened.get(kind).copied() != wanted {
                use gpui_kit::component::WindowExt;
                if self.opened.remove(kind).is_some() {
                    if kind == "sheet" {
                        window.close_sheet(cx);
                    } else {
                        window.close_dialog(cx);
                    }
                }
                if let Some(id) = wanted {
                    self.open_overlay(id, window, cx);
                }
            }
        }
    }
    pub(crate) fn change(&mut self, id: u64, value: Value, cx: &mut Context<Self>) {
        if let Some(NativeControl::Kit(kit)) = self.controls.get_mut(&id) {
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
        self.opened.insert(kit.kind.clone(), id);
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
                        div().flex().flex_col().gap_3().children(
                            v.controls
                                .get(&id)
                                .into_iter()
                                .flat_map(|control| match control {
                                    NativeControl::Kit(kit) => kit.children.as_slice(),
                                    _ => &[],
                                })
                                .filter(|id| v.visible[id])
                                .map(|id| v.render_control(*id, cx)),
                        )
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
                        div().flex().flex_col().gap_3().children(
                            v.controls
                                .get(&id)
                                .into_iter()
                                .flat_map(|control| match control {
                                    NativeControl::Kit(kit) => kit.children.as_slice(),
                                    _ => &[],
                                })
                                .filter(|id| v.visible[id])
                                .map(|id| v.render_control(*id, cx)),
                        )
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
        if self.displayed.contains(&id)
            && !self
                .transport
                .emit(json!({"event":"click", "id":id, "values":self.values(cx)}))
        {
            cx.quit();
        }
    }
    pub(crate) fn event(&mut self, id: u64, event: &str, value: Value, cx: &mut Context<Self>) {
        if self.displayed.contains(&id)
            && !self
                .transport
                .emit(json!({"event":event, "id":id, "value":value, "values":self.values(cx)}))
        {
            cx.quit();
        }
    }
    fn context_inputs(&self, id: u64, inputs: &mut Vec<AnyInputState>) {
        match &self.controls[&id] {
            NativeControl::Input(input) => inputs.push(AnyInputState::Input(input.clone())),
            NativeControl::Column(children) => {
                for id in children {
                    self.context_inputs(*id, inputs);
                }
            }
            NativeControl::Kit(kit) => {
                match &kit.state {
                    NativeState::Textarea(state) => {
                        inputs.push(AnyInputState::Textarea(state.clone()))
                    }
                    NativeState::Editor(state) => inputs.push(AnyInputState::Editor(state.clone())),
                    NativeState::Number(state) => inputs.push(AnyInputState::Input(state.clone())),
                    _ => {}
                }
                for id in &kit.children {
                    self.context_inputs(*id, inputs);
                }
            }
            _ => {}
        }
    }

    pub(crate) fn render_control(&self, id: u64, cx: &Context<Self>) -> AnyElement {
        let element = match &self.controls[&id] {
            NativeControl::Column(children) => crate::kit::apply_style(
                div().id(("column", id)).flex().flex_col().gap_3(),
                &self.styles[&id],
                cx,
            )
            .children(
                children
                    .iter()
                    .filter(|id| self.visible[id])
                    .map(|id| self.render_control(*id, cx)),
            )
            .into_any_element(),
            NativeControl::Label(text) => div()
                .id(("label", id))
                .child(Label::new(text.clone()))
                .into_any_element(),
            NativeControl::Input(input) => crate::theme::field(
                Input::new(input)
                    .id(("input", id))
                    .w_full()
                    .appearance(!crate::theme::field_frame(cx)),
                input.focus_handle(cx),
                false,
                false,
                &self.styles[&id],
                cx,
            ),
            NativeControl::DropdownMenu {
                text,
                items,
                disabled,
            } => {
                use gpui_kit::component::{Disableable, menu::DropdownMenu};
                let entries = items.clone();
                let actions = self.actions.clone();
                let view = cx.weak_entity();
                let popups = self.popups.clone();
                crate::theme::button(Button::new(("dropdown-menu", id)), &self.styles[&id], cx)
                    .label(text.clone())
                    .disabled(*disabled)
                    .dropdown_menu(move |popup, window, cx| {
                        popups.borrow_mut().insert((id, false), cx.weak_entity());
                        commands::build_popup(popup, &entries, &actions, id, &view, window, cx)
                    })
                    .into_any_element()
            }
            NativeControl::Button {
                command,
                text,
                disabled,
                variant,
                icon,
            } => {
                use gpui_kit::component::Disableable;
                use gpui_kit::{component::button::ButtonVariants, prelude::FluentBuilder};
                crate::theme::button(Button::new(("button", id)), &self.styles[&id], cx)
                    .label(text.clone())
                    .disabled(
                        *disabled || command.is_some_and(|id| !self.actions.borrow()[&id].enabled),
                    )
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
                    .on_click(cx.listener({
                        let command = *command;
                        move |view, _, _, cx| {
                            if let Some(command) = command {
                                view.invoke(command, Some(id), cx);
                                return;
                            }
                            if !view
                                .transport
                                .emit(json!({"event":"click", "id":id, "values":view.values(cx)}))
                            {
                                cx.quit();
                            }
                        }
                    }))
                    .into_any_element()
            }
            NativeControl::Kit(kit) if kit.kind == "form" => {
                let fields = kit
                    .children
                    .iter()
                    .filter(|id| self.visible[id])
                    .map(|id| {
                        let NativeControl::Kit(field) = &self.controls[id] else {
                            unreachable!()
                        };
                        crate::kit::form_field(
                            field,
                            field
                                .children
                                .iter()
                                .filter(|id| self.visible[id])
                                .map(|id| self.render_control(*id, cx))
                                .collect(),
                            &self.styles[id],
                            cx,
                        )
                    })
                    .collect();
                crate::kit::form(kit, fields, &self.styles[&id], cx)
            }
            NativeControl::Kit(kit) if kit.kind == "field" => crate::kit::form_field(
                kit,
                kit.children
                    .iter()
                    .filter(|id| self.visible[id])
                    .map(|id| self.render_control(*id, cx))
                    .collect(),
                &self.styles[&id],
                cx,
            )
            .into_any_element(),
            NativeControl::Kit(kit) => kit.render(
                id,
                kit.children
                    .iter()
                    .filter(|id| self.visible[id])
                    .map(|id| self.render_control(*id, cx))
                    .collect(),
                &self.styles[&id],
                cx,
            ),
        };
        let element = if matches!(&self.controls[&id], NativeControl::Column(_))
            || matches!(&self.controls[&id], NativeControl::Kit(k) if matches!(k.kind.as_str(), "row" | "container" | "scroll" | "form" | "field" | "image"))
        {
            element
        } else {
            crate::kit::styled(id, element, &self.styles[&id], cx)
        };
        if let Some(menu) = self.context_menus.get(&id) {
            use gpui_kit::component::{menu::ContextMenuExt, native_menu::NativeMenu};
            let entries = menu.items.clone();
            let actions = self.actions.clone();
            let view = cx.weak_entity();
            let popups = self.popups.clone();
            let layout = self.styles[&id]
                .iter()
                .filter(|(key, _)| {
                    matches!(
                        key.as_str(),
                        "width"
                            | "height"
                            | "min_width"
                            | "min_height"
                            | "flex"
                            | "full_width"
                            | "full_height"
                    )
                })
                .map(|(key, value)| (key.clone(), value.clone()))
                .collect();
            let host = crate::kit::apply_style(
                div()
                    .id(("context-menu-host", id))
                    .flex()
                    .flex_col()
                    .child(element),
                &layout,
                cx,
            );
            if menu.native {
                host.capture_any_mouse_down(move |event, window, cx| {
                    if event.button != MouseButton::Right {
                        return;
                    }
                    // Stop the native input's default editing menu from replacing
                    // this explicitly assigned application context menu.
                    cx.stop_propagation();
                    NativeMenu::from(Menu::new("").items(commands::gpui_items(&entries, &actions)))
                        .show(event.position, window, cx);
                })
                .into_any_element()
            } else {
                let mut inputs = Vec::new();
                self.context_inputs(id, &mut inputs);
                host.capture_any_mouse_down(move |event, _, cx| {
                    if event.button != MouseButton::Right {
                        return;
                    }
                    // The assigned Kit context menu opens during bubbling. Suppress
                    // each underlying editor's default menu for this press only;
                    // its Kit input builder restores it on the next render.
                    for input in &inputs {
                        match input {
                            AnyInputState::Input(state) => state.update(cx, |state, _| {
                                state.on_context_menu(Rc::new(|_, _, _, _, _| {}));
                            }),
                            AnyInputState::Textarea(state) => state.update(cx, |state, _| {
                                state.on_context_menu(Rc::new(|_, _, _, _, _| {}));
                            }),
                            AnyInputState::Editor(state) => state.update(cx, |state, _| {
                                state.on_context_menu(Rc::new(|_, _, _, _, _| {}));
                            }),
                            AnyInputState::Otp(_) => {}
                        }
                    }
                })
                .context_menu(move |popup, window, cx| {
                    popups.borrow_mut().insert((id, true), cx.weak_entity());
                    commands::build_popup(popup, &entries, &actions, id, &view, window, cx)
                })
                .into_any_element()
            }
        } else {
            element
        }
    }
}

impl Render for NativeView {
    fn render(&mut self, _: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        self.rendered = true;
        div()
            .key_context("Gpyui")
            .track_focus(&self.focus)
            .on_action(
                cx.listener(|view, action: &InvokeCommand, _, cx| view.invoke(action.id, None, cx)),
            )
            .children(
                self.menu_bar
                    .as_ref()
                    .map(|bar| div().h(px(28.)).w_full().child(bar.clone())),
            )
            .size_full()
            .p_6()
            .flex()
            .flex_col()
            .gap_3()
            .bg(cx.theme().background)
            .text_color(cx.theme().foreground)
            .children(
                self.roots
                    .iter()
                    .filter(|id| self.visible[id])
                    .map(|id| self.render_control(*id, cx)),
            )
    }
}
