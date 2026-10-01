use serde::Deserialize;
use serde_json::Value;
use std::collections::HashMap;

#[derive(Clone, Deserialize)]
pub(crate) struct Node {
    pub(crate) id: u64,
    #[serde(flatten)]
    pub(crate) control: Control,
}

#[derive(Clone, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub(crate) enum Control {
    Column { children: Vec<Node> },
    Label { text: String },
    Input { value: String, placeholder: String },
    Button { text: String, disabled: bool },
}

#[derive(Clone, Copy)]
pub(crate) enum ControlType {
    Column,
    Label,
    Input,
    Button,
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
    Snapshot(u64),
    Close,
}

pub(crate) fn schema(nodes: &[Node]) -> Result<HashMap<u64, ControlType>, String> {
    fn visit(nodes: &[Node], out: &mut HashMap<u64, ControlType>) -> Result<(), String> {
        for node in nodes {
            let control = match &node.control {
                Control::Column { .. } => ControlType::Column,
                Control::Label { .. } => ControlType::Label,
                Control::Input { .. } => ControlType::Input,
                Control::Button { .. } => ControlType::Button,
            };
            if node.id == 0 || out.insert(node.id, control).is_some() {
                return Err(format!(
                    "control IDs must be positive and unique: {}",
                    node.id
                ));
            }
            if out.len() > 10_000 {
                return Err("tree exceeds 10,000 controls".into());
            }
            if let Control::Column { children } = &node.control {
                visit(children, out)?;
            }
        }
        Ok(())
    }
    let mut out = HashMap::new();
    visit(nodes, &mut out)?;
    Ok(out)
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
        let valid = match (control, patch.property.as_str()) {
            (ControlType::Label | ControlType::Button, "text")
            | (ControlType::Input, "value" | "placeholder") => patch.value.is_string(),
            (ControlType::Button, "disabled") => patch.value.is_boolean(),
            _ => false,
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
