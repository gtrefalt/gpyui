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
    },
    Button {
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
    Button { variant: String, icon: String },
    Kit(String, serde_json::Map<String, Value>),
}

#[derive(Deserialize)]
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
    },
    Snapshot(u64),
    Close,
    Notify {
        message: String,
        title: String,
        variant: String,
    },
}

pub(crate) fn schema(nodes: &[Node]) -> Result<HashMap<u64, ControlType>, String> {
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
                Control::Button { variant, icon, .. } => ControlType::Button {
                    variant: variant.clone(),
                    icon: icon.clone(),
                },
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
                        )
                    {
                        return Err(format!("{kind} does not accept children"));
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
    for patch in patches {
        let control = schema
            .get(&patch.id)
            .ok_or_else(|| format!("unknown control {}", patch.id))?;
        let valid = if patch.property == "visible" {
            patch.value.is_boolean()
        } else if patch.property == "style" {
            patch
                .value
                .as_object()
                .is_some_and(|style| crate::kit::validate_style(style).is_ok())
        } else {
            match (control, patch.property.as_str()) {
                (ControlType::Label | ControlType::Button { .. }, "text")
                | (ControlType::Input, "value" | "placeholder") => patch.value.is_string(),
                (ControlType::Button { .. }, "disabled") => patch.value.is_boolean(),
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
    Ok(())
}
