//! Native Kit components. No Python callback is retained by this module.
use crate::view::NativeView;
use gpui_kit::{
    component::{self as c, ActiveTheme, Disableable, Sizable},
    prelude::FluentBuilder,
    *,
};
use serde_json::{Map, Value, json};

pub(crate) fn fields(kind: &str) -> Option<&'static [&'static str]> {
    Some(match kind {
        "row" | "container" | "scroll" | "toolbar" | "status_bar" | "spinner" | "skeleton"
        | "bubble" => &[],
        "group_box" => &["title"],
        "form" => &["label_layout", "columns", "label_width", "size", "error"],
        "field" => &["label", "name", "help", "required", "error", "col_span"],
        "resizable" => &["vertical"],
        "tree" => &["items", "value"],
        "markdown" | "html" => &["text"],
        "dialog" | "sheet" => &["title", "value"],
        "calendar" | "date_picker" | "time_field" | "color_picker" | "carousel" => &["value"],
        "checkbox" | "switch" | "radio" | "toggle" => &["text", "value", "disabled"],
        "radio_group" | "tabs" | "sidebar" | "breadcrumb" | "accordion" | "stepper" | "list" => {
            &["items", "value", "disabled"]
        }
        "rating" => &["value", "disabled"],
        "slider" => &["value", "minimum", "maximum", "step", "disabled"],
        "select" | "combobox" => &["items", "value", "placeholder", "disabled"],
        "textarea" | "number_input" | "editor" => &["value", "placeholder", "disabled"],
        "otp_input" => &["value", "length", "disabled"],
        "progress" | "progress_circle" => &["value", "loading"],
        "tag" => &["text", "variant"],
        "badge" => &["count", "text"],
        "avatar" | "icon" => &["name"],
        "image" => &[
            "source",
            "fit",
            "grayscale",
            "aspect_ratio",
            "loading_text",
            "error_text",
            "_revision",
        ],
        "separator" => &["text", "vertical"],
        "link" => &["text", "href", "disabled"],
        "pagination" => &["value", "pages"],
        "description_list" => &["items"],
        "empty" => &["title", "description"],
        "alert" => &["text", "title", "variant"],
        "shimmer" | "clipboard" | "tooltip" | "popover" | "hover_card" => &["text"],
        "kbd" => &["key"],
        "collapsible" => &["text", "value"],
        "table" => &["columns", "rows", "value", "column_width"],
        "line_chart" | "area_chart" | "bar_chart" | "pie_chart" | "candlestick_chart" => &["data"],
        "message" => &["text", "author"],
        "marker" => &["text", "loading"],
        "attachment" => &["title", "description"],
        _ => return None,
    })
}

fn finite(value: &Value) -> bool {
    value
        .as_f64()
        .is_some_and(|n| n.is_finite() && n.abs() <= 1e9)
}
fn strings(value: &Value) -> bool {
    value
        .as_array()
        .is_some_and(|a| a.len() <= 10_000 && a.iter().all(Value::is_string))
}
fn integer(value: &Value) -> bool {
    value.as_u64().is_some_and(|v| v <= 1_000_000)
}

fn valid_field(kind: &str, property: &str, value: &Value) -> bool {
    match property {
        "text" | "title" | "description" | "author" | "placeholder" | "href" | "label" | "help"
        | "error" | "loading_text" | "error_text" => value.is_string(),
        "source" => crate::images::valid_source(value),
        "fit" => value
            .as_str()
            .is_some_and(|v| matches!(v, "contain" | "cover" | "fill" | "scale_down" | "none")),
        "aspect_ratio" => finite(value) && value.as_f64().unwrap() >= 0.,
        "_revision" => integer(value),
        "name" if kind == "field" => value.as_str().is_some_and(|name| {
            name.is_empty() || (!name.trim().is_empty() && name.chars().count() <= 128)
        }),
        "columns" | "col_span" if kind == "form" || kind == "field" => {
            value.as_u64().is_some_and(|v| (1..=12).contains(&v))
        }
        "label_layout" => value
            .as_str()
            .is_some_and(|v| matches!(v, "vertical" | "horizontal")),
        "label_width" => value
            .as_f64()
            .is_some_and(|v| v.is_finite() && (0. ..=1e9).contains(&v)),
        "size" => value
            .as_str()
            .is_some_and(|v| matches!(v, "small" | "medium" | "large")),
        "key" => value.as_str().is_some_and(|s| Keystroke::parse(s).is_ok()),
        "name" => value.as_str().is_some_and(|s| {
            kind != "icon"
                || (!s.is_empty()
                    && s.bytes()
                        .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-'))
        }),
        "disabled" | "loading" | "vertical" | "required" | "grayscale" => value.is_boolean(),
        "minimum" | "maximum" | "step" => finite(value),
        "column_width" => finite(value) && value.as_f64().unwrap() >= 24.,
        "count" | "pages" | "length" => integer(value),
        "variant" => value.as_str().is_some_and(|s| {
            matches!(
                s,
                "primary" | "secondary" | "success" | "warning" | "danger" | "info"
            )
        }),
        "columns" => strings(value),
        "items" if matches!(kind, "accordion" | "description_list") => {
            value.as_array().is_some_and(|a| {
                a.len() <= 10_000
                    && a.iter()
                        .all(|r| strings(r) && r.as_array().unwrap().len() == 2)
            })
        }
        "items" if kind == "tree" => valid_tree(value),
        "items" => strings(value),
        "rows" => value
            .as_array()
            .is_some_and(|a| a.len() <= 10_000 && a.iter().all(strings)),
        "data" => value.as_array().is_some_and(|a| {
            a.len() <= 10_000
                && a.iter().all(|r| {
                    r.as_array().is_some_and(|r| {
                        r.len() == if kind == "candlestick_chart" { 5 } else { 2 }
                            && r[0].is_string()
                            && r[1..].iter().all(finite)
                            && (kind != "pie_chart" || r[1].as_f64().unwrap() >= 0.)
                            && (kind != "candlestick_chart" || {
                                let n = |i: usize| r[i].as_f64().unwrap();
                                n(3) <= n(1).min(n(4)) && n(1).max(n(4)) <= n(2)
                            })
                    })
                })
        }),
        "value" => match kind {
            "checkbox" | "switch" | "radio" | "toggle" | "collapsible" | "dialog" | "sheet" => {
                value.is_boolean()
            }
            "calendar" | "date_picker" => value.as_str().is_some_and(|s| {
                s.is_empty() || chrono::NaiveDate::parse_from_str(s, "%Y-%m-%d").is_ok()
            }),
            "time_field" => value
                .as_str()
                .is_some_and(|s| chrono::NaiveTime::parse_from_str(s, "%H:%M:%S").is_ok()),
            "color_picker" => value.as_str().is_some_and(|s| {
                matches!(s.len(), 7 | 9)
                    && s.starts_with('#')
                    && s[1..].bytes().all(|b| b.is_ascii_hexdigit())
            }),
            "select" | "combobox" | "textarea" | "number_input" | "otp_input" | "editor"
            | "tree" => value.is_string(),
            "slider" => finite(value),
            "progress" | "progress_circle" => {
                finite(value) && (0. ..=100.).contains(&value.as_f64().unwrap())
            }
            "rating" => value.as_u64().is_some_and(|v| v <= 5),
            _ => integer(value),
        },
        _ => false,
    }
}

pub(crate) fn validate_property(
    kind: &str,
    initial: &Map<String, Value>,
    property: &str,
    value: &Value,
) -> bool {
    if (kind == "slider" && matches!(property, "minimum" | "maximum" | "step"))
        || (kind == "table" && matches!(property, "columns" | "column_width"))
        || (matches!(kind, "dialog" | "sheet") && property == "title")
        || (matches!(kind, "select" | "combobox") && property == "items")
        || (kind == "otp_input" && property == "length")
        || (kind == "tree" && property == "items")
        || (kind == "resizable" && property == "vertical")
        || (kind == "field" && property == "name")
    {
        return false;
    }
    if !(fields(kind).is_some_and(|fields| fields.contains(&property))
        && valid_field(kind, property, value))
    {
        return false;
    }
    let p = Props(initial);
    match (kind, property) {
        ("tree", "value") => value == "" || tree_has(&initial["items"], value.as_str().unwrap()),
        ("slider", "value") => {
            (p.n("minimum") as f64..=p.n("maximum") as f64).contains(&value.as_f64().unwrap())
        }
        ("select" | "combobox", "value") => {
            value == "" || initial["items"].as_array().unwrap().contains(value)
        }
        ("otp_input", "value") => {
            value.as_str().unwrap().len() <= p.ix("length")
                && value.as_str().unwrap().bytes().all(|b| b.is_ascii_digit())
        }
        ("table", "rows") => value
            .as_array()
            .unwrap()
            .iter()
            .all(|r| r.as_array().unwrap().len() == p.strings("columns").len()),
        _ => true,
    }
}

pub(crate) fn validate(kind: &str, props: &Map<String, Value>) -> Result<(), String> {
    let fields = fields(kind).ok_or_else(|| format!("unsupported Kit component: {kind}"))?;
    if props.len() != fields.len()
        || fields
            .iter()
            .any(|f| !props.get(*f).is_some_and(|v| valid_field(kind, f, v)))
    {
        return Err(format!("invalid properties for Kit {kind}"));
    }
    let p = Props(props);
    if kind == "tree" && !p.s("value").is_empty() && !tree_has(&props["items"], &p.s("value")) {
        return Err("tree value must be an item ID".into());
    }
    if kind == "slider"
        && !(p.n("minimum") < p.n("maximum")
            && p.n("step") > 0.
            && (p.n("minimum")..=p.n("maximum")).contains(&p.n("value")))
    {
        return Err("invalid slider range/value".into());
    }
    if matches!(kind, "select" | "combobox")
        && !p.s("value").is_empty()
        && !p.strings("items").contains(&p.s("value"))
    {
        return Err("select value must be an item".into());
    }
    if kind == "otp_input"
        && (!(1..=32).contains(&p.ix("length"))
            || p.s("value").len() > p.ix("length")
            || !p.s("value").bytes().all(|b| b.is_ascii_digit()))
    {
        return Err("invalid OTP length/value".into());
    }
    if kind == "table"
        && p.rows("rows")
            .iter()
            .any(|r| r.len() != p.strings("columns").len())
    {
        return Err("table rows must match columns".into());
    }
    if kind == "pagination" && (p.ix("pages") == 0 || p.ix("value") >= p.ix("pages")) {
        return Err("invalid page index".into());
    }
    Ok(())
}

pub(crate) fn validate_style(style: &Map<String, Value>) -> Result<(), String> {
    for (key, value) in style {
        let valid = match key.as_str() {
            "width" | "height" | "min_width" | "min_height" | "padding" | "gap" | "radius"
            | "font_size" | "flex" => finite(value) && value.as_f64().unwrap() >= 0.,
            "full_width" | "full_height" | "border" | "bold" => value.is_boolean(),
            "background" | "color" => value.as_str().is_some_and(|s| {
                matches!(
                    s,
                    "background"
                        | "foreground"
                        | "muted"
                        | "muted_foreground"
                        | "primary"
                        | "primary_foreground"
                        | "secondary"
                        | "secondary_foreground"
                        | "border"
                        | "accent"
                        | "accent_foreground"
                        | "danger"
                        | "success"
                        | "warning"
                        | "info"
                        | "transparent"
                        | "popover"
                        | "sidebar"
                )
            }),
            "align" => value
                .as_str()
                .is_some_and(|s| matches!(s, "start" | "center" | "end" | "stretch")),
            "justify" => value
                .as_str()
                .is_some_and(|s| matches!(s, "start" | "center" | "end" | "between")),
            _ => false,
        };
        if !valid {
            return Err(format!("invalid style {key}"));
        }
    }
    Ok(())
}

pub(crate) struct Props<'a>(pub(crate) &'a Map<String, Value>);
impl Props<'_> {
    pub(crate) fn s(&self, key: &str) -> SharedString {
        self.0[key].as_str().unwrap().to_owned().into()
    }
    pub(crate) fn b(&self, key: &str) -> bool {
        self.0[key].as_bool().unwrap()
    }
    pub(crate) fn n(&self, key: &str) -> f32 {
        self.0[key].as_f64().unwrap() as f32
    }
    pub(crate) fn ix(&self, key: &str) -> usize {
        self.0[key].as_u64().unwrap() as usize
    }
    pub(crate) fn strings(&self, key: &str) -> Vec<SharedString> {
        self.0[key]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_owned().into())
            .collect()
    }
    pub(crate) fn rows(&self, key: &str) -> Vec<Vec<SharedString>> {
        self.0[key]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| {
                r.as_array()
                    .unwrap()
                    .iter()
                    .map(|v| v.as_str().unwrap().to_owned().into())
                    .collect()
            })
            .collect()
    }
    fn points(&self) -> Vec<(SharedString, Vec<f64>)> {
        self.0["data"]
            .as_array()
            .unwrap()
            .iter()
            .map(|r| {
                let r = r.as_array().unwrap();
                (
                    r[0].as_str().unwrap().to_owned().into(),
                    r[1..].iter().map(|v| v.as_f64().unwrap()).collect(),
                )
            })
            .collect()
    }
}

pub(crate) enum NativeState {
    None,
    Image(Entity<crate::images::NativeImage>),
    Slider(Entity<c::slider::SliderState>),
    Select(Entity<c::select::SelectState<Vec<SharedString>>>),
    Table(Entity<c::table::TableState<TableData>>),
    Combobox(Entity<c::combobox::ComboboxState<Vec<SharedString>>>),
    Textarea(Entity<c::input::TextareaState>),
    Number(Entity<c::input::InputState>),
    Otp(Entity<c::input::OtpState>),
    Calendar(Entity<c::calendar::CalendarState>),
    DatePicker(Entity<c::date_picker::DatePickerState>),
    Time(Entity<c::time_field::TimeFieldState>),
    Color(Entity<c::color_picker::ColorPickerState>),
    Carousel(Entity<c::carousel::CarouselState>),
    Editor(Entity<c::input::EditorState>),
    Tree(Entity<c::tree::TreeState>),
    Resizable(Entity<c::ResizableState>),
}

pub(crate) struct NativeKit {
    pub(crate) kind: String,
    pub(crate) props: Map<String, Value>,
    pub(crate) children: Vec<u64>,
    pub(crate) state: NativeState,
}

pub(crate) struct TableData {
    pub(crate) columns: Vec<SharedString>,
    pub(crate) rows: Vec<Vec<SharedString>>,
    pub(crate) width: f32,
}

impl c::table::TableDelegate for TableData {
    fn columns_count(&self, _: &App) -> usize {
        self.columns.len()
    }
    fn rows_count(&self, _: &App) -> usize {
        self.rows.len()
    }
    fn column(&self, ix: usize, _: &App) -> c::table::Column {
        c::table::Column::new(format!("col-{ix}"), self.columns[ix].clone()).width(px(self.width))
    }
    fn render_td(
        &mut self,
        row: usize,
        col: usize,
        _: &mut Window,
        _: &mut Context<c::table::TableState<Self>>,
    ) -> impl IntoElement {
        div().child(
            self.rows
                .get(row)
                .and_then(|r| r.get(col))
                .cloned()
                .unwrap_or_default(),
        )
    }
}

impl NativeKit {
    pub(crate) fn value(&self, cx: &App) -> Option<Value> {
        Some(match &self.state {
            NativeState::Editor(s) => json!(s.read(cx).value().as_str()),
            NativeState::Tree(s) => json!(
                s.read(cx)
                    .selected_item()
                    .map(|item| item.id.as_str())
                    .unwrap_or("")
            ),
            NativeState::Textarea(s) => json!(s.read(cx).value().as_str()),
            NativeState::Number(s) => json!(s.read(cx).value().as_str()),
            NativeState::Otp(s) => json!(s.read(cx).value().as_str()),
            NativeState::Slider(s) => match s.read(cx).value() {
                c::slider::SliderValue::Single(v) => json!(v),
                _ => unreachable!(),
            },
            NativeState::Select(s) => json!(
                s.read(cx)
                    .selected_value()
                    .map(SharedString::as_str)
                    .unwrap_or("")
            ),
            NativeState::Combobox(s) => json!(
                s.read(cx)
                    .selected_value()
                    .as_ref()
                    .map(SharedString::as_str)
                    .unwrap_or("")
            ),
            NativeState::Calendar(s) => json!(date_string(s.read(cx).date())),
            NativeState::DatePicker(s) => json!(date_string(s.read(cx).date())),
            NativeState::Time(s) => json!(s.read(cx).time().format("%H:%M:%S").to_string()),
            NativeState::Color(s) => {
                use c::Colorize;
                json!(s.read(cx).value().map(|v| v.to_hex()).unwrap_or_default())
            }
            NativeState::Carousel(s) => json!(s.read(cx).selected_index().unwrap_or(0)),
            _ => return self.props.get("value").cloned(),
        })
    }
    pub(crate) fn apply(
        &mut self,
        property: &str,
        value: Value,
        window: &mut Window,
        cx: &mut Context<NativeView>,
    ) {
        self.props.insert(property.to_owned(), value);
        let p = Props(&self.props);
        match &self.state {
            NativeState::Image(state) if matches!(property, "source" | "_revision") => {
                state.update(cx, |state, cx| state.reset(&self.props, window, cx));
            }
            NativeState::Editor(state) => state.update(cx, |state, cx| {
                if property == "value" {
                    state.set_value(p.s("value"), window, cx);
                } else if property == "placeholder" {
                    state.set_placeholder(p.s("placeholder"), window, cx);
                }
            }),
            NativeState::Tree(state) if property == "value" => state.update(cx, |state, cx| {
                let item = c::tree::TreeItem::new(p.s("value"), "");
                state.set_selected_item(
                    if p.s("value").is_empty() {
                        None
                    } else {
                        Some(&item)
                    },
                    cx,
                );
            }),
            NativeState::Slider(state) if property == "value" => {
                state.update(cx, |state, cx| state.set_value(p.n("value"), window, cx))
            }
            NativeState::Select(state) if property == "value" => state.update(cx, |state, cx| {
                state.set_selected_value(&p.s("value"), window, cx)
            }),
            NativeState::Combobox(state) if property == "value" => state.update(cx, |state, cx| {
                state.set_selected_values(&[p.s("value")], window, cx)
            }),
            NativeState::Textarea(state) => state.update(cx, |state, cx| {
                if property == "value" {
                    state.set_value(p.s("value"), window, cx);
                } else if property == "placeholder" {
                    state.set_placeholder(p.s("placeholder"), window, cx);
                }
            }),
            NativeState::Number(state) => state.update(cx, |state, cx| {
                if property == "value" {
                    state.set_value(p.s("value"), window, cx);
                } else if property == "placeholder" {
                    state.set_placeholder(p.s("placeholder"), window, cx);
                }
            }),
            NativeState::Otp(state) if property == "value" => {
                state.update(cx, |state, cx| state.set_value(p.s("value"), window, cx))
            }
            NativeState::Calendar(state) if property == "value" => state.update(cx, |state, cx| {
                state.set_date(date_value(&p.s("value")), window, cx)
            }),
            NativeState::DatePicker(state) if property == "value" => state
                .update(cx, |state, cx| {
                    state.set_date(date_value(&p.s("value")), window, cx)
                }),
            NativeState::Time(state) if property == "value" => state.update(cx, |state, cx| {
                state.set_time(
                    chrono::NaiveTime::parse_from_str(&p.s("value"), "%H:%M:%S").unwrap(),
                    window,
                    cx,
                )
            }),
            NativeState::Color(state) if property == "value" => state.update(cx, |state, cx| {
                state.set_value(color_value(&p.s("value")), window, cx)
            }),
            NativeState::Carousel(state) if property == "value" => {
                state.update(cx, |state, cx| state.set_selected_index(p.ix("value"), cx))
            }
            NativeState::Table(state) if property == "rows" => state.update(cx, |state, cx| {
                state.delegate_mut().rows = p.rows("rows");
                state.clear_selection(cx);
                state.refresh(cx);
            }),
            NativeState::Table(state) if property == "value" => state.update(cx, |state, cx| {
                if p.ix("value") < state.delegate().rows.len() {
                    state.set_selected_row(p.ix("value"), cx);
                }
            }),
            _ => (),
        }
    }

    pub(crate) fn render(
        &self,
        id: u64,
        children: Vec<AnyElement>,
        style: &Map<String, Value>,
        cx: &Context<NativeView>,
    ) -> AnyElement {
        let p = Props(&self.props);
        let eid = ("kit", id);
        let change =
            move |view: &mut NativeView,
                  value: &Value,
                  _: &mut Window,
                  cx: &mut Context<NativeView>| view.change(id, value.clone(), cx);
        match self.kind.as_str() {
            "image" => {
                let NativeState::Image(state) = &self.state else {
                    unreachable!()
                };
                crate::images::ImageElement {
                    state: state.clone(),
                    id,
                    // Never copy encoded source payloads on every paint.
                    props: self
                        .props
                        .iter()
                        .filter(|(key, _)| key.as_str() != "source")
                        .map(|(key, value)| (key.clone(), value.clone()))
                        .collect(),
                    style: style.clone(),
                }
                .into_any_element()
            }
            "row" | "container" | "scroll" => apply_style(
                div()
                    .id(eid)
                    .flex()
                    .gap_3()
                    .when(self.kind == "row", |el| el.items_center())
                    .when(self.kind != "row", |el| el.flex_col())
                    .when(self.kind == "scroll", |el| el.overflow_y_scroll()),
                style,
                cx,
            )
            .children(children)
            .into_any_element(),
            "group_box" => c::group_box::GroupBox::new()
                .title(p.s("title"))
                .child(div().flex().flex_col().gap_3().children(children))
                .into_any_element(),
            "toolbar" => c::toolbar::Toolbar::new(eid)
                .contents(children)
                .into_any_element(),
            "resizable" => {
                let NativeState::Resizable(state) = &self.state else {
                    unreachable!()
                };
                let group = if p.b("vertical") {
                    c::v_resizable(eid)
                } else {
                    c::h_resizable(eid)
                };
                group
                    .with_state(state)
                    .children(
                        children
                            .into_iter()
                            .map(|child| c::resizable_panel().child(child)),
                    )
                    .on_resize(
                        cx.listener(move |v, state: &Entity<c::ResizableState>, _, cx| {
                            v.event(
                                id,
                                "resize",
                                json!(
                                    state
                                        .read(cx)
                                        .sizes()
                                        .iter()
                                        .map(|p| f32::from(*p))
                                        .collect::<Vec<_>>()
                                ),
                                cx,
                            )
                        }),
                    )
                    .into_any_element()
            }
            "markdown" => c::text::TextView::markdown(eid, p.s("text"))
                .selectable(true)
                .into_any_element(),
            "html" => c::text::TextView::html(eid, p.s("text"))
                .selectable(true)
                .into_any_element(),
            "editor" => {
                let NativeState::Editor(state) = &self.state else {
                    unreachable!()
                };
                c::input::Editor::new(state)
                    .disabled(p.b("disabled"))
                    .h_full()
                    .into_any_element()
            }
            "tree" => {
                let NativeState::Tree(state) = &self.state else {
                    unreachable!()
                };
                c::tree::Tree::new(state, |i, entry, _, _, _| {
                    c::list::ListItem::new(("tree-item", i))
                        .pl(px(entry.depth() as f32 * 16. + 12.))
                        .child(
                            div()
                                .flex()
                                .gap_2()
                                .child(if entry.is_folder() {
                                    c::IconName::Folder
                                } else {
                                    c::IconName::File
                                })
                                .child(entry.item().label.clone()),
                        )
                })
                .into_any_element()
            }
            "status_bar" => c::status_bar::StatusBar::new()
                .children(children)
                .into_any_element(),
            "checkbox" => c::checkbox::Checkbox::new(eid)
                .with_size(crate::theme::checkbox_size(cx))
                .when(crate::theme::platform_controls(cx), |el| {
                    el.text_size(cx.theme().font_size)
                })
                .label(p.s("text"))
                .checked(p.b("value"))
                .disabled(p.b("disabled"))
                .on_change(
                    cx.listener(move |v, value: &bool, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "switch" => c::switch::Switch::new(eid)
                .with_size(crate::theme::switch_size(cx))
                .color(crate::theme::switch_color(cx))
                .label(p.s("text"))
                .checked(p.b("value"))
                .disabled(p.b("disabled"))
                .on_change(
                    cx.listener(move |v, value: &bool, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "radio" => c::radio::Radio::new(eid)
                .label(p.s("text"))
                .checked(p.b("value"))
                .disabled(p.b("disabled"))
                .on_change(
                    cx.listener(move |v, value: &bool, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "toggle" => c::button::Toggle::new(eid)
                .label(p.s("text"))
                .checked(p.b("value"))
                .disabled(p.b("disabled"))
                .on_click(
                    cx.listener(move |v, value: &bool, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "radio_group" => c::radio::RadioGroup::horizontal(eid)
                .children(
                    p.strings("items")
                        .into_iter()
                        .enumerate()
                        .map(|(i, s)| c::radio::Radio::new(("radio-item", i)).label(s)),
                )
                .selected_index(Some(p.ix("value")))
                .disabled(p.b("disabled"))
                .on_change(
                    cx.listener(move |v, value: &usize, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "tabs" => c::tab::TabBar::new(eid)
                .children(
                    p.strings("items")
                        .into_iter()
                        .map(|s| c::tab::Tab::new().label(s).disabled(p.b("disabled"))),
                )
                .selected_index(p.ix("value"))
                .on_click(
                    cx.listener(move |v, value: &usize, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "sidebar" => c::sidebar::Sidebar::new(eid)
                .child(c::sidebar::SidebarMenu::new().children(
                    p.strings("items").into_iter().enumerate().map(|(i, s)| {
                        c::sidebar::SidebarMenuItem::new(s)
                            .active(i == p.ix("value"))
                            .disable(p.b("disabled"))
                            .on_click(cx.listener(move |v, _, w, cx| change(v, &json!(i), w, cx)))
                    }),
                ))
                .into_any_element(),
            "breadcrumb" => c::breadcrumb::Breadcrumb::new()
                .children(p.strings("items").into_iter().enumerate().map(|(i, s)| {
                    c::breadcrumb::BreadcrumbItem::new(s)
                        .disabled(p.b("disabled"))
                        .on_click(cx.listener(move |v, _, w, cx| change(v, &json!(i), w, cx)))
                }))
                .into_any_element(),
            "rating" => c::rating::Rating::new(eid)
                .value(p.ix("value"))
                .disabled(p.b("disabled"))
                .on_click(
                    cx.listener(move |v, value: &usize, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "slider" => {
                let NativeState::Slider(state) = &self.state else {
                    unreachable!()
                };
                c::slider::Slider::new(state)
                    .disabled(p.b("disabled"))
                    .w_full()
                    .into_any_element()
            }
            "select" => {
                let NativeState::Select(state) = &self.state else {
                    unreachable!()
                };
                crate::theme::select(
                    c::select::Select::new(state)
                        .id(eid)
                        .placeholder(p.s("placeholder"))
                        .disabled(p.b("disabled"))
                        .appearance(!crate::theme::field_frame(cx))
                        .with_size(crate::theme::size(cx))
                        .w_full(),
                    state.focus_handle(cx),
                    p.b("disabled"),
                    style,
                    cx,
                )
            }
            "table" => {
                let NativeState::Table(state) = &self.state else {
                    unreachable!()
                };
                c::table::DataTable::new(state)
                    .stripe(true)
                    .bordered(true)
                    .into_any_element()
            }
            "combobox" => {
                let NativeState::Combobox(state) = &self.state else {
                    unreachable!()
                };
                c::combobox::Combobox::new(state)
                    .placeholder(p.s("placeholder"))
                    .disabled(p.b("disabled"))
                    .w_full()
                    .into_any_element()
            }
            "textarea" => {
                let NativeState::Textarea(state) = &self.state else {
                    unreachable!()
                };
                crate::theme::field(
                    c::input::Textarea::new(state)
                        .disabled(p.b("disabled"))
                        .appearance(!crate::theme::field_frame(cx))
                        .h_full(),
                    state.focus_handle(cx),
                    p.b("disabled"),
                    true,
                    style,
                    cx,
                )
            }
            "number_input" => {
                let NativeState::Number(state) = &self.state else {
                    unreachable!()
                };
                c::input::NumberInput::new(state)
                    .placeholder(p.s("placeholder"))
                    .disabled(p.b("disabled"))
                    .w_full()
                    .into_any_element()
            }
            "otp_input" => {
                let NativeState::Otp(state) = &self.state else {
                    unreachable!()
                };
                c::input::OtpInput::new(state)
                    .disabled(p.b("disabled"))
                    .into_any_element()
            }
            "calendar" => {
                let NativeState::Calendar(state) = &self.state else {
                    unreachable!()
                };
                c::calendar::Calendar::new(state).into_any_element()
            }
            "date_picker" => {
                let NativeState::DatePicker(state) = &self.state else {
                    unreachable!()
                };
                c::date_picker::DatePicker::new(state).into_any_element()
            }
            "time_field" => {
                let NativeState::Time(state) = &self.state else {
                    unreachable!()
                };
                c::time_field::TimeField::new(state).into_any_element()
            }
            "color_picker" => {
                let NativeState::Color(state) = &self.state else {
                    unreachable!()
                };
                c::color_picker::ColorPicker::new(state).into_any_element()
            }
            "carousel" => {
                let NativeState::Carousel(state) = &self.state else {
                    unreachable!()
                };
                c::carousel::Carousel::new(eid, state)
                    .child(c::carousel::CarouselContent::new(state).children(
                        children.into_iter().enumerate().map(|(i, child)| {
                            c::carousel::CarouselItem::new(("carousel-item", i), i, state)
                                .child(child)
                        }),
                    ))
                    .child(c::carousel::CarouselPrevious::new(state))
                    .child(c::carousel::CarouselNext::new(state))
                    .into_any_element()
            }
            "dialog" | "sheet" => div().into_any_element(),
            "stepper" => c::stepper::Stepper::new(eid)
                .items(
                    p.strings("items")
                        .into_iter()
                        .map(|s| c::stepper::StepperItem::new().child(s)),
                )
                .selected_index(p.ix("value"))
                .disabled(p.b("disabled"))
                .on_click(
                    cx.listener(move |v, value: &usize, w, cx| change(v, &json!(value), w, cx)),
                )
                .into_any_element(),
            "list" => div()
                .id(eid)
                .flex()
                .flex_col()
                .children(p.strings("items").into_iter().enumerate().map(|(i, s)| {
                    c::list::ListItem::new(("list-item", i))
                        .child(s)
                        .selected(p.ix("value") == i)
                        .disabled(p.b("disabled"))
                        .on_click(cx.listener(move |v, _, w, cx| change(v, &json!(i), w, cx)))
                }))
                .into_any_element(),
            "progress" => c::progress::Progress::new(eid)
                .value(p.n("value"))
                .loading(p.b("loading"))
                .into_any_element(),
            "progress_circle" => c::progress::ProgressCircle::new(eid)
                .value(p.n("value"))
                .loading(p.b("loading"))
                .into_any_element(),
            "spinner" => c::spinner::Spinner::new().into_any_element(),
            "tag" => {
                let tag = match p.s("variant").as_str() {
                    "primary" => c::tag::Tag::primary(),
                    "success" => c::tag::Tag::success(),
                    "warning" => c::tag::Tag::warning(),
                    "danger" => c::tag::Tag::danger(),
                    "info" => c::tag::Tag::info(),
                    _ => c::tag::Tag::secondary(),
                };
                tag.child(p.s("text")).into_any_element()
            }
            "badge" => c::badge::Badge::new()
                .count(p.ix("count"))
                .child(p.s("text"))
                .into_any_element(),
            "avatar" => c::avatar::Avatar::new()
                .name(p.s("name"))
                .into_any_element(),
            "icon" => c::Icon::default()
                .path(format!("icons/{}.svg", p.s("name")))
                .into_any_element(),
            "separator" => {
                let s = if p.b("vertical") {
                    c::separator::Separator::vertical()
                } else {
                    c::separator::Separator::horizontal()
                };
                s.label(p.s("text")).into_any_element()
            }
            "link" => c::link::Link::new(eid)
                .href(p.s("href"))
                .disabled(p.b("disabled"))
                .child(p.s("text"))
                .on_click(cx.listener(move |v, _, _, cx| v.click(id, cx)))
                .into_any_element(),
            "pagination" => c::pagination::Pagination::new(eid)
                .total_pages(p.ix("pages"))
                .current_page(p.ix("value") + 1)
                .on_click(cx.listener(move |v, value: &usize, w, cx| {
                    change(v, &json!(value.saturating_sub(1)), w, cx)
                }))
                .into_any_element(),
            "description_list" => c::description_list::DescriptionList::new()
                .columns(1)
                .label_width(px(110.))
                .children(p.rows("items").into_iter().map(|r| {
                    c::description_list::DescriptionItem::new(r[0].clone()).value(r[1].clone())
                }))
                .into_any_element(),
            "empty" => c::empty::Empty::new()
                .header(
                    c::empty::EmptyHeader::new()
                        .title(c::empty::EmptyTitle::new().child(p.s("title")))
                        .description(c::empty::EmptyDescription::new().child(p.s("description"))),
                )
                .into_any_element(),
            "alert" => {
                let alert = match p.s("variant").as_str() {
                    "success" => c::alert::Alert::success(eid, p.s("text")),
                    "warning" => c::alert::Alert::warning(eid, p.s("text")),
                    "danger" => c::alert::Alert::error(eid, p.s("text")),
                    _ => c::alert::Alert::info(eid, p.s("text")),
                };
                alert.title(p.s("title")).into_any_element()
            }
            "skeleton" => c::skeleton::Skeleton::new()
                .w_full()
                .h_6()
                .into_any_element(),
            "shimmer" => c::shimmer::ShimmerText::new(p.s("text")).into_any_element(),
            "kbd" => c::kbd::Kbd::new(Keystroke::parse(&p.s("key")).expect("validated keystroke"))
                .into_any_element(),
            "collapsible" => c::collapsible::Collapsible::new()
                .motion_id(eid)
                .open(p.b("value"))
                .child(
                    c::button::Button::new(("collapse", id))
                        .label(p.s("text"))
                        .on_click(cx.listener(move |v, _, _, cx| v.toggle(id, cx))),
                )
                .content(div().flex().flex_col().gap_3().children(children))
                .into_any_element(),
            "accordion" => {
                let mut a = c::accordion::Accordion::new(eid).disabled(p.b("disabled"));
                for (i, r) in p.rows("items").into_iter().enumerate() {
                    a = a.item(|item| {
                        item.title(r[0].clone())
                            .child(r[1].clone())
                            .open(i == p.ix("value"))
                    });
                }
                a.on_toggle_click(cx.listener(move |v, values: &[usize], w, cx| {
                    if let Some(i) = values.first() {
                        change(v, &json!(i), w, cx);
                    }
                }))
                .into_any_element()
            }
            "line_chart" => {
                let data = p.points();
                let (low, high) = chart_domain(&data);
                c::chart::LineChart::new(data)
                    .id(eid)
                    .x(|p| p.0.clone())
                    .y(|p| p.1[0])
                    .y_axis(true)
                    .y_domain(low, high)
                    .stroke(cx.theme().success)
                    .into_any_element()
            }
            "area_chart" => c::chart::AreaChart::new(p.points())
                .id(eid)
                .x(|p| p.0.clone())
                .y(|p| p.1[0])
                .y_axis(true)
                .stroke(cx.theme().success)
                .fill(cx.theme().primary.opacity(0.15))
                .into_any_element(),
            "bar_chart" => c::chart::BarChart::new(p.points())
                .id(eid)
                .band(|p| p.0.clone())
                .value(|p| p.1[0])
                .into_any_element(),
            "pie_chart" => c::chart::PieChart::new(p.points())
                .id(eid)
                .value(|p| p.1[0] as f32)
                .label(|p| p.0.clone())
                .inner_radius(0.5)
                .into_any_element(),
            "candlestick_chart" => c::chart::CandlestickChart::new(p.points())
                .id(eid)
                .x(|p| p.0.clone())
                .open(|p| p.1[0])
                .high(|p| p.1[1])
                .low(|p| p.1[2])
                .close(|p| p.1[3])
                .into_any_element(),
            "bubble" => c::bubble::Bubble::new()
                .children(children)
                .into_any_element(),
            "message" => c::message::Message::new()
                .header(c::message::MessageHeader::new().child(p.s("author")))
                .content(
                    c::message::MessageContent::new()
                        .bubble(c::bubble::Bubble::new().child(p.s("text"))),
                )
                .into_any_element(),
            "marker" => c::marker::Marker::new()
                .id(eid)
                .loading(p.b("loading"))
                .content(c::marker::MarkerContent::new().text(p.s("text")))
                .into_any_element(),
            "attachment" => c::attachment::Attachment::new()
                .id(eid)
                .content(
                    c::attachment::AttachmentContent::new()
                        .title(c::attachment::AttachmentTitle::new(p.s("title")))
                        .description(c::attachment::AttachmentDescription::new(
                            p.s("description"),
                        )),
                )
                .into_any_element(),
            "clipboard" => c::clipboard::Clipboard::new(eid)
                .value(p.s("text"))
                .into_any_element(),
            "tooltip" => {
                let text = p.s("text");
                div()
                    .id(eid)
                    .children(children)
                    .tooltip(move |w, cx| c::tooltip::Tooltip::new(text.clone()).build(w, cx))
                    .into_any_element()
            }
            "popover" | "hover_card" => {
                let ids = self.children.clone();
                let view = cx.entity();
                if self.kind == "popover" {
                    c::popover::Popover::new(eid)
                        .trigger(c::button::Button::new(("popover-trigger", id)).label(p.s("text")))
                        .content(move |_, _, cx| {
                            view.update(cx, |v, cx| {
                                div()
                                    .flex()
                                    .flex_col()
                                    .gap_3()
                                    .children(ids.iter().map(|id| v.render_control(*id, cx)))
                            })
                        })
                        .into_any_element()
                } else {
                    c::hover_card::HoverCard::new(eid)
                        .trigger(c::button::Button::new(("hover-trigger", id)).label(p.s("text")))
                        .content(move |_, _, cx| {
                            view.update(cx, |v, cx| {
                                div()
                                    .flex()
                                    .flex_col()
                                    .gap_3()
                                    .children(ids.iter().map(|id| v.render_control(*id, cx)))
                            })
                        })
                        .into_any_element()
                }
            }
            _ => unreachable!("validated Kit component"),
        }
    }
}

// Return the actual Kit Field so Form can supply layout/grid properties.
pub(crate) fn form_field(
    kit: &NativeKit,
    children: Vec<AnyElement>,
    style: &Map<String, Value>,
    cx: &App,
) -> c::form::Field {
    let p = Props(&kit.props);
    let help = p.s("help");
    let error = p.s("error");
    let field = c::form::Field::new()
        .label(p.s("label"))
        .required(p.b("required"))
        .col_span(p.ix("col_span") as u16)
        .children(children)
        .when(!help.is_empty() || !error.is_empty(), |field| {
            field.description_fn(move |_, cx| {
                div()
                    .flex()
                    .flex_col()
                    .gap_1()
                    .when(!help.is_empty(), |el| {
                        el.child(
                            div()
                                .text_color(cx.theme().muted_foreground)
                                .child(help.clone()),
                        )
                    })
                    .when(!error.is_empty(), |el| {
                        el.child(div().text_color(cx.theme().danger).child(error.clone()))
                    })
            })
        });
    apply_style(field, style, cx)
}

pub(crate) fn form(
    kit: &NativeKit,
    fields: Vec<c::form::Field>,
    style: &Map<String, Value>,
    cx: &App,
) -> AnyElement {
    let p = Props(&kit.props);
    let form = c::form::Form::new()
        .label_layout(if p.s("label_layout") == "horizontal" {
            Axis::Horizontal
        } else {
            Axis::Vertical
        })
        .columns(p.ix("columns"))
        .label_width(px(p.n("label_width")))
        .with_size(c::Size::from_str(&p.s("size")))
        .children(fields)
        .when(!p.s("error").is_empty(), |form| {
            form.footer(
                div()
                    .w_full()
                    .text_sm()
                    .text_color(cx.theme().danger)
                    .child(p.s("error")),
            )
        });
    apply_style(form, style, cx).into_any_element()
}

pub(crate) fn date_value(value: &str) -> c::calendar::Date {
    c::calendar::Date::Single(if value.is_empty() {
        None
    } else {
        Some(chrono::NaiveDate::parse_from_str(value, "%Y-%m-%d").unwrap())
    })
}
pub(crate) fn date_string(date: c::calendar::Date) -> String {
    match date {
        c::calendar::Date::Single(Some(date)) => date.to_string(),
        _ => String::new(),
    }
}

fn valid_tree(value: &Value) -> bool {
    fn visit(value: &Value, depth: usize, ids: &mut std::collections::HashSet<String>) -> bool {
        if depth > 32 {
            return false;
        }
        value.as_array().is_some_and(|nodes| {
            nodes.iter().all(|node| {
                node.as_object().is_some_and(|n| {
                    n.len() == 3
                        && n.get("text").is_some_and(Value::is_string)
                        && n.get("id").and_then(Value::as_str).is_some_and(|id| {
                            !id.is_empty() && ids.len() < 10_000 && ids.insert(id.to_owned())
                        })
                        && n.get("children")
                            .is_some_and(|children| visit(children, depth + 1, ids))
                })
            })
        })
    }
    visit(value, 0, &mut std::collections::HashSet::new())
}
fn tree_has(items: &Value, id: &str) -> bool {
    items
        .as_array()
        .unwrap()
        .iter()
        .any(|item| item["id"] == id || tree_has(&item["children"], id))
}
pub(crate) fn tree_items(items: &Value) -> Vec<c::tree::TreeItem> {
    items
        .as_array()
        .unwrap()
        .iter()
        .map(|item| {
            c::tree::TreeItem::new(
                item["id"].as_str().unwrap().to_owned(),
                item["text"].as_str().unwrap().to_owned(),
            )
            .children(tree_items(&item["children"]))
            .expanded(true)
        })
        .collect()
}

fn color(token: &str, cx: &App) -> Hsla {
    let t = cx.theme();
    match token {
        "background" => t.background,
        "foreground" => t.foreground,
        "muted" => t.muted,
        "muted_foreground" => t.muted_foreground,
        "primary" => t.primary,
        "primary_foreground" => t.primary_foreground,
        "secondary" => t.secondary,
        "secondary_foreground" => t.secondary_foreground,
        "border" => t.border,
        "accent" => t.accent,
        "accent_foreground" => t.accent_foreground,
        "danger" => t.danger,
        "success" => t.success,
        "warning" => t.warning,
        "info" => t.info,
        "popover" => t.popover,
        "sidebar" => t.sidebar,
        _ => transparent_black(),
    }
}

pub(crate) fn styled(
    id: u64,
    child: AnyElement,
    style: &Map<String, Value>,
    cx: &App,
) -> AnyElement {
    if style.is_empty() {
        return child;
    }
    apply_style(div().id(("style", id)), style, cx)
        .child(child)
        .into_any_element()
}

pub(crate) fn apply_style<T: Styled + FluentBuilder>(
    el: T,
    style: &Map<String, Value>,
    cx: &App,
) -> T {
    el.when(style.contains_key("flex"), |el| el.min_w_0().min_h_0())
        .map(|mut el| {
            for (key, value) in style {
                el = match key.as_str() {
                    "width" => el.w(px(value.as_f64().unwrap() as f32)).flex_shrink_0(),
                    "height" => el.h(px(value.as_f64().unwrap() as f32)).flex_shrink_0(),
                    "min_width" => el.min_w(px(value.as_f64().unwrap() as f32)),
                    "min_height" => el.min_h(px(value.as_f64().unwrap() as f32)),
                    "padding" => el.p(px(value.as_f64().unwrap() as f32)),
                    "gap" => el.gap(px(value.as_f64().unwrap() as f32)),
                    "radius" => el.rounded(px(value.as_f64().unwrap() as f32)),
                    "font_size" => el.text_size(px(value.as_f64().unwrap() as f32)),
                    "flex" => el
                        .flex_grow(value.as_f64().unwrap() as f32)
                        .flex_basis(relative(0.)),
                    "full_width" if value.as_bool().unwrap() => el.w_full(),
                    "full_height" if value.as_bool().unwrap() => el.h_full(),
                    "border" if value.as_bool().unwrap() => {
                        el.border_1().border_color(cx.theme().border)
                    }
                    "bold" if value.as_bool().unwrap() => el.font_weight(FontWeight::SEMIBOLD),
                    "background" => el.bg(color(value.as_str().unwrap(), cx)),
                    "color" => el.text_color(color(value.as_str().unwrap(), cx)),
                    "align" => match value.as_str().unwrap() {
                        "center" => el.items_center(),
                        "end" => el.items_end(),
                        "stretch" => el.items_stretch(),
                        _ => el.items_start(),
                    },
                    "justify" => match value.as_str().unwrap() {
                        "center" => el.justify_center(),
                        "end" => el.justify_end(),
                        "between" => el.justify_between(),
                        _ => el.justify_start(),
                    },
                    _ => el,
                };
            }
            el
        })
}

fn chart_domain(data: &[(SharedString, Vec<f64>)]) -> (f64, f64) {
    let low = data.iter().map(|p| p.1[0]).fold(f64::INFINITY, f64::min);
    let high = data
        .iter()
        .map(|p| p.1[0])
        .fold(f64::NEG_INFINITY, f64::max);
    if data.is_empty() {
        return (0., 1.);
    }
    let padding = ((high - low) * 0.15).max(0.01);
    (low - padding, high + padding)
}

pub(crate) fn color_value(value: &str) -> Hsla {
    let hex = u32::from_str_radix(&value[1..], 16).expect("validated color");
    if value.len() == 9 {
        rgba(hex).into()
    } else {
        rgb(hex).into()
    }
}
