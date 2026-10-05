//! Shared actions, Kit menus and platform application menus.
use crate::protocol::{ControlType, Node};
use gpui_kit::{
    component::menu::{AppMenuBar, PopupMenu, PopupMenuItem},
    *,
};
use serde::{Deserialize, Serialize};
use std::{
    cell::RefCell,
    collections::{HashMap, HashSet},
    rc::Rc,
};

#[derive(Clone, Debug, PartialEq, Action)]
#[action(namespace = gpyui, no_json)]
pub(crate) struct InvokeCommand {
    pub(crate) id: u64,
}

#[derive(Clone, Deserialize, Default)]
#[serde(deny_unknown_fields)]
pub(crate) struct UiConfig {
    #[serde(default)]
    pub(crate) commands: Vec<ActionSpec>,
    #[serde(default)]
    pub(crate) menus: Vec<MenuEntry>,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ActionSpec {
    pub(crate) id: u64,
    pub(crate) label: String,
    pub(crate) shortcut: String,
    pub(crate) enabled: bool,
    pub(crate) checked: bool,
}

#[derive(Clone, Deserialize, Serialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub(crate) enum MenuEntry {
    Command {
        id: u64,
    },
    Menu {
        label: String,
        items: Vec<MenuEntry>,
    },
    Separator,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ContextMenuSpec {
    pub(crate) items: Vec<MenuEntry>,
    pub(crate) native: bool,
}

pub(crate) fn validate_items(
    entries: &[MenuEntry],
    schema: &HashMap<u64, ControlType>,
) -> Result<(), String> {
    fn visit(
        entries: &[MenuEntry],
        schema: &HashMap<u64, ControlType>,
        depth: usize,
        count: &mut usize,
    ) -> Result<(), String> {
        if depth > 8 {
            return Err("menus exceed eight submenu levels".into());
        }
        for entry in entries {
            *count += 1;
            if *count > 1000 {
                return Err("menu exceeds 1,000 entries".into());
            }
            match entry {
                MenuEntry::Command { id }
                    if !matches!(schema.get(id), Some(ControlType::Action { .. })) =>
                {
                    return Err(format!("unknown command {id}"));
                }
                MenuEntry::Menu { label, items } => {
                    if label.is_empty() {
                        return Err("menu label cannot be empty".into());
                    }
                    visit(items, schema, depth + 1, count)?;
                }
                _ => {}
            }
        }
        Ok(())
    }
    visit(entries, schema, 0, &mut 0)
}

pub(crate) fn add_schema(
    config: &UiConfig,
    schema: &mut HashMap<u64, ControlType>,
    nodes: &[Node],
) -> Result<(), String> {
    if config.commands.len() > 1024 {
        return Err("application exceeds 1,024 registered commands".into());
    }
    let mut keys = HashSet::new();
    for command in &config.commands {
        if command.label.is_empty() || command.id == 0 || schema.contains_key(&command.id) {
            return Err("command IDs must be positive and unique, with nonempty labels".into());
        }
        if !command.shortcut.is_empty() {
            if command.shortcut.split_whitespace().count() != 1
                || Keystroke::parse(&command.shortcut).is_err()
            {
                return Err("invalid command shortcut".into());
            }
            if !keys.insert(&command.shortcut) {
                return Err("duplicate shortcut".into());
            }
        }
        schema.insert(
            command.id,
            ControlType::Action {
                label: command.label.clone(),
                shortcut: command.shortcut.clone(),
            },
        );
    }
    validate_items(&config.menus, schema)?;
    if config
        .menus
        .iter()
        .any(|entry| !matches!(entry, MenuEntry::Menu { .. }))
    {
        return Err("application menus require menu roots".into());
    }
    fn visit(nodes: &[Node], schema: &HashMap<u64, ControlType>) -> Result<(), String> {
        use crate::protocol::Control;
        for node in nodes {
            if let Some(menu) = &node.context_menu {
                validate_items(&menu.items, schema)?;
            }
            match &node.control {
                Control::Button {
                    command: Some(id), ..
                } if !matches!(schema.get(id), Some(ControlType::Action { .. })) => {
                    return Err(format!("unknown command {id}"));
                }
                Control::DropdownMenu { items, .. } => validate_items(items, schema)?,
                Control::Column { children } | Control::Kit { children, .. } => {
                    visit(children, schema)?
                }
                _ => {}
            }
        }
        Ok(())
    }
    visit(nodes, schema)
}

pub(crate) fn has_command(entries: &[MenuEntry], id: u64) -> bool {
    entries.iter().any(|entry| match entry {
        MenuEntry::Command { id: command } => *command == id,
        MenuEntry::Menu { items, .. } => has_command(items, id),
        _ => false,
    })
}

pub(crate) type Actions = Rc<RefCell<HashMap<u64, ActionSpec>>>;
pub(crate) type Popups = Rc<RefCell<HashMap<(u64, bool), WeakEntity<PopupMenu>>>>;

pub(crate) fn build_popup(
    mut popup: PopupMenu,
    entries: &[MenuEntry],
    actions: &Actions,
    source: u64,
    view: &WeakEntity<crate::view::NativeView>,
    window: &mut Window,
    cx: &mut Context<PopupMenu>,
) -> PopupMenu {
    for entry in entries {
        popup = match entry {
            MenuEntry::Separator => popup.separator(),
            MenuEntry::Command { id } => {
                let command = actions.borrow()[id].clone();
                let command_id = *id;
                let view = view.clone();
                popup.item(
                    PopupMenuItem::new(command.label)
                        .disabled(!command.enabled)
                        .checked(command.checked)
                        .action(Box::new(InvokeCommand { id: command_id }))
                        .on_click(move |_, _, cx| {
                            _ = view
                                .update(cx, |view, cx| view.invoke(command_id, Some(source), cx));
                        }),
                )
            }
            MenuEntry::Menu { label, items } => {
                let items = items.clone();
                let actions = actions.clone();
                let view = view.clone();
                let submenu = PopupMenu::build(window, cx, move |popup, window, cx| {
                    build_popup(popup, &items, &actions, source, &view, window, cx)
                });
                popup.item(PopupMenuItem::submenu(label.clone(), submenu))
            }
        };
    }
    popup
}

pub(crate) fn gpui_items(entries: &[MenuEntry], actions: &Actions) -> Vec<MenuItem> {
    entries
        .iter()
        .map(|entry| match entry {
            MenuEntry::Separator => MenuItem::Separator,
            MenuEntry::Menu { label, items } => {
                MenuItem::Submenu(Menu::new(label.clone()).items(gpui_items(items, actions)))
            }
            MenuEntry::Command { id } => {
                let command = actions.borrow()[id].clone();
                MenuItem::action(command.label, InvokeCommand { id: *id })
                    .checked(command.checked)
                    .disabled(!command.enabled)
            }
        })
        .collect()
}

pub(crate) fn application_menus(
    entries: &[MenuEntry],
    actions: &Actions,
    bar: &mut Option<Entity<AppMenuBar>>,
    cx: &mut Context<crate::view::NativeView>,
) {
    let menus: Vec<_> = gpui_items(entries, actions)
        .into_iter()
        .filter_map(|entry| match entry {
            MenuItem::Submenu(menu) => Some(menu),
            _ => None,
        })
        .collect();
    #[cfg(target_os = "macos")]
    cx.set_menus(menus);
    #[cfg(not(target_os = "macos"))]
    {
        gpui_kit::base::GlobalState::global_mut(cx)
            .set_app_menus(menus.into_iter().map(Menu::owned).collect());
        if entries.is_empty() {
            *bar = None;
        } else if let Some(bar) = bar {
            bar.update(cx, |bar, cx| bar.reload(cx));
        } else {
            *bar = Some(AppMenuBar::new(cx));
        }
    }
    #[cfg(target_os = "macos")]
    {
        _ = bar;
    }
}
