use crate::commands::{ContextMenuSpec, MenuEntry, UiConfig};
use serde::Deserialize;
use serde_json::Value;
use std::collections::{HashMap, HashSet};

#[derive(Clone, Deserialize)]
pub(crate) struct Node {
    pub(crate) id: u64,
    #[serde(default)]
    pub(crate) style: serde_json::Map<String, Value>,
    #[serde(default = "visible_by_default")]
    pub(crate) visible: bool,
    #[serde(default)]
    pub(crate) context_menu: Option<ContextMenuSpec>,
    #[serde(flatten)]
    pub(crate) control: Control,
}

#[derive(Clone, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub(crate) enum Control {
    Column {
        children: Vec<Node>,
    },
    Label {
        text: String,
    },
    Input {
        value: String,
        placeholder: String,
        #[serde(default)]
        disabled: bool,
        #[serde(default)]
        read_only: bool,
        #[serde(default)]
        password: bool,
        #[serde(default)]
        clearable: bool,
        #[serde(default)]
        prefix: String,
        #[serde(default)]
        suffix: String,
    },
    DropdownMenu {
        text: String,
        items: Vec<MenuEntry>,
        disabled: bool,
    },
    Button {
        #[serde(default)]
        command: Option<u64>,
        text: String,
        disabled: bool,
        #[serde(default)]
        variant: String,
        #[serde(default)]
        icon: String,
    },
    Kit {
        kind: String,
        props: serde_json::Map<String, Value>,
        #[serde(default)]
        children: Vec<Node>,
    },
}

fn visible_by_default() -> bool {
    true
}

#[derive(Clone, PartialEq)]
pub(crate) enum ControlType {
    Column,
    Label,
    Input,
    Button {
        variant: String,
        icon: String,
        command: Option<u64>,
    },
    DropdownMenu,
    Action {
        label: String,
        shortcut: String,
    },
    Kit(String, serde_json::Map<String, Value>),
}

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Patch {
    pub(crate) id: u64,
    pub(crate) property: String,
    pub(crate) value: Value,
}

pub(crate) enum Command {
    Batch(Vec<Patch>),
    Reconcile {
        nodes: Vec<Node>,
        roots: Vec<u64>,
        patches: Vec<Patch>,
        retained: HashSet<u64>,
        config: UiConfig,
    },
    Execute(u64),
    Snapshot(u64),
    Theme(Box<crate::theme::NativeTheme>),
    ThemeSnapshot(u64),
    Window(crate::windows::WindowCommand),
    Close,
    Notify {
        message: String,
        title: String,
        variant: String,
    },
}

pub(crate) fn schema(
    nodes: &[Node],
    config: &UiConfig,
) -> Result<HashMap<u64, ControlType>, String> {
    fn visit(
        nodes: &[Node],
        out: &mut HashMap<u64, ControlType>,
        depth: usize,
    ) -> Result<(), String> {
        if depth > 64 {
            return Err("control tree exceeds 64 levels".into());
        }
        for node in nodes {
            let control = match &node.control {
                Control::Column { .. } => ControlType::Column,
                Control::Label { .. } => ControlType::Label,
                Control::Input { .. } => ControlType::Input,
                Control::Button {
                    variant,
                    icon,
                    command,
                    ..
                } => ControlType::Button {
                    variant: variant.clone(),
                    icon: icon.clone(),
                    command: *command,
                },
                Control::DropdownMenu { .. } => ControlType::DropdownMenu,
                Control::Kit {
                    kind,
                    props,
                    children,
                } => {
                    crate::kit::validate(kind, props)?;
                    if !children.is_empty()
                        && !matches!(
                            kind.as_str(),
                            "row"
                                | "container"
                                | "scroll"
                                | "group_box"
                                | "toolbar"
                                | "status_bar"
                                | "bubble"
                                | "collapsible"
                                | "tooltip"
                                | "popover"
                                | "hover_card"
                                | "carousel"
                                | "dialog"
                                | "sheet"
                                | "resizable"
                                | "form"
                                | "field"
                        )
                    {
                        return Err(format!("{kind} does not accept children"));
                    }
                    if kind == "form" {
                        let mut names = HashSet::new();
                        for child in children {
                            let Control::Kit { kind, props, .. } = &child.control else {
                                return Err("Form accepts Field children".into());
                            };
                            if kind != "field" {
                                return Err("Form accepts Field children".into());
                            }
                            let name = props
                                .get("name")
                                .and_then(Value::as_str)
                                .filter(|v| !v.is_empty())
                                .ok_or("Form fields require names")?;
                            if !names.insert(name) {
                                return Err("Form field names must be unique".into());
                            }
                        }
                    }
                    ControlType::Kit(kind.clone(), props.clone())
                }
            };
            crate::kit::validate_style(&node.style)?;
            if node.id == 0 || out.insert(node.id, control).is_some() {
                return Err(format!(
                    "control IDs must be positive and unique: {}",
                    node.id
                ));
            }
            if out.len() > 10_000 {
                return Err("tree exceeds 10,000 controls".into());
            }
            if let Control::Column { children } | Control::Kit { children, .. } = &node.control {
                visit(children, out, depth + 1)?;
            }
        }
        Ok(())
    }
    let mut out = HashMap::new();
    visit(nodes, &mut out, 0)?;
    crate::commands::add_schema(config, &mut out, nodes)?;
    Ok(out)
}

pub(crate) fn validate_roots(nodes: &[Node], roots: &[u64]) -> Result<(), String> {
    let mut seen = HashSet::new();
    let mut overlays = HashMap::<String, usize>::new();
    fn count(node: &Node, overlays: &mut HashMap<String, usize>) {
        if let Control::Kit { kind, .. } = &node.control
            && matches!(kind.as_str(), "dialog" | "sheet")
        {
            *overlays.entry(kind.clone()).or_default() += 1;
        }
        if let Control::Column { children } | Control::Kit { children, .. } = &node.control {
            for child in children {
                count(child, overlays);
            }
        }
    }
    for id in roots {
        let node = nodes
            .iter()
            .find(|node| node.id == *id)
            .ok_or_else(|| format!("root {id} must be an unparented control"))?;
        if !seen.insert(id) {
            return Err("root IDs must be unique".into());
        }
        count(node, &mut overlays);
    }
    for (kind, count) in overlays {
        if count > 1 {
            return Err(format!("one {kind} per window is currently supported"));
        }
    }
    Ok(())
}

/// Existing IDs describe retained handles, not requests to rebuild their state.
pub(crate) fn validate_identity(old: &ControlType, new: &ControlType) -> bool {
    match (old, new) {
        (ControlType::Kit(kind, initial), ControlType::Kit(next_kind, next))
            if kind == next_kind =>
        {
            initial.iter().all(|(key, value)| {
                crate::kit::validate_property(kind, initial, key, value)
                    || next.get(key) == Some(value)
            })
        }
        _ => old == new,
    }
}

pub(crate) fn validate_batch(
    patches: &[Patch],
    schema: &HashMap<u64, ControlType>,
) -> Result<(), String> {
    if patches.len() > 10_000 {
        return Err("batch exceeds 10,000 updates".into());
    }
    let mut final_schema = schema.clone();
    apply_schema_patches(patches, &mut final_schema);
    for patch in patches {
        let control = schema
            .get(&patch.id)
            .ok_or_else(|| format!("unknown control {}", patch.id))?;
        let valid = if let ControlType::Action { .. } = control {
            matches!(patch.property.as_str(), "enabled" | "checked") && patch.value.is_boolean()
        } else if patch.property == "context_menu" {
            patch.value.is_null()
                || serde_json::from_value::<ContextMenuSpec>(patch.value.clone())
                    .is_ok_and(|menu| crate::commands::validate_items(&menu.items, schema).is_ok())
        } else if patch.property == "visible" {
            patch.value.is_boolean()
        } else if patch.property == "style" {
            patch
                .value
                .as_object()
                .is_some_and(|style| crate::kit::validate_style(style).is_ok())
        } else {
            match (control, patch.property.as_str()) {
                (ControlType::Label | ControlType::Button { .. }, "text")
                | (ControlType::Input, "value" | "placeholder" | "prefix" | "suffix") => {
                    patch.value.is_string()
                }
                (ControlType::Input, "disabled" | "read_only" | "password" | "clearable") => {
                    patch.value.is_boolean()
                }
                (ControlType::Button { .. } | ControlType::DropdownMenu, "disabled") => {
                    patch.value.is_boolean()
                }
                (ControlType::DropdownMenu, "text") => patch.value.is_string(),
                (ControlType::DropdownMenu, "items") => {
                    serde_json::from_value::<Vec<MenuEntry>>(patch.value.clone())
                        .is_ok_and(|items| crate::commands::validate_items(&items, schema).is_ok())
                }
                (ControlType::Kit(kind, initial), property) => {
                    crate::kit::validate_property(kind, initial, property, &patch.value)
                }
                _ => false,
            }
        };
        if !valid {
            return Err(format!(
                "invalid property or value for {}.{}",
                patch.id, patch.property
            ));
        }
    }
    for id in patches.iter().map(|patch| patch.id).collect::<HashSet<_>>() {
        if let Some(ControlType::Kit(kind, props)) = final_schema.get(&id) {
            crate::kit::validate(kind, props)
                .map_err(|error| format!("invalid property batch for {id}: {error}"))?;
            if kind == "command_palette" {
                validate_palette(props, &final_schema)?;
            }
        }
    }
    Ok(())
}

fn validate_palette(
    props: &serde_json::Map<String, Value>,
    schema: &HashMap<u64, ControlType>,
) -> Result<(), String> {
    let mut seen = HashSet::new();
    for item in props["items"].as_array().unwrap() {
        let id = item.as_u64().unwrap();
        if !seen.insert(id) || !matches!(schema.get(&id), Some(ControlType::Action { .. })) {
            return Err("palette requires unique registered command IDs".into());
        }
    }
    Ok(())
}

pub(crate) fn validate_palettes(schema: &HashMap<u64, ControlType>) -> Result<(), String> {
    for control in schema.values() {
        if let ControlType::Kit(kind, props) = control
            && kind == "command_palette"
        {
            validate_palette(props, schema)?;
        }
    }
    Ok(())
}

pub(crate) fn apply_schema_patches(patches: &[Patch], schema: &mut HashMap<u64, ControlType>) {
    for patch in patches {
        if let Some(ControlType::Kit(_, props)) = schema.get_mut(&patch.id)
            && props.contains_key(&patch.property)
        {
            props.insert(patch.property.clone(), patch.value.clone());
        }
    }
}
