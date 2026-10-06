//! Strict Python theme contract translated into Kit's native ThemeConfig.
use gpui_kit::{
    component::{Colorize, Theme, ThemeConfig, ThemeMode},
    *,
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{collections::BTreeMap, rc::Rc};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ThemeSpec {
    name: String,
    mode: ThemeMode,
    colors: BTreeMap<String, String>,
    radius: u8,
    radius_lg: u8,
    font_size: f32,
    font_family: Option<String>,
    mono_font_size: f32,
    mono_font_family: Option<String>,
    shadow: bool,
}

fn color_key(key: &str) -> Option<&'static str> {
    Some(match key {
        "background" => "background",
        "foreground" => "foreground",
        "primary" => "primary.background",
        "primary_foreground" => "primary.foreground",
        "primary_hover" => "primary.hover.background",
        "primary_active" => "primary.active.background",
        "secondary" => "secondary.background",
        "secondary_foreground" => "secondary.foreground",
        "muted" => "muted.background",
        "muted_foreground" => "muted.foreground",
        "border" => "border",
        "input" => "input.border",
        "ring" => "ring",
        "accent" => "accent.background",
        "accent_foreground" => "accent.foreground",
        "danger" => "danger.background",
        "danger_foreground" => "danger.foreground",
        "success" => "success.background",
        "warning" => "warning.background",
        "info" => "info.background",
        "selection" => "selection.background",
        "caret" => "caret",
        "button" => "button.background",
        "button_hover" => "button.hover.background",
        "button_active" => "button.active.background",
        "popover" => "popover.background",
        "sidebar" => "sidebar.background",
        _ => return None,
    })
}

pub(crate) fn parse(value: &str) -> Result<ThemeConfig, String> {
    let spec: ThemeSpec = serde_json::from_str(value).map_err(|e| e.to_string())?;
    if spec.name.trim().is_empty() || spec.name.len() > 64 {
        return Err("theme name requires 1–64 characters".into());
    }
    if spec.radius > 64 || spec.radius_lg > 64 {
        return Err("theme radius requires 0–64 pixels".into());
    }
    for size in [spec.font_size, spec.mono_font_size] {
        if !size.is_finite() || !(8. ..=48.).contains(&size) {
            return Err("theme font size requires 8–48 pixels".into());
        }
    }
    for family in [&spec.font_family, &spec.mono_font_family]
        .into_iter()
        .flatten()
    {
        if family.trim().is_empty() || family.chars().count() > 256 {
            return Err("theme font family requires 1–256 characters".into());
        }
    }
    let mut colors = serde_json::Map::new();
    for (key, value) in spec.colors {
        let key = color_key(&key).ok_or_else(|| format!("unknown theme color: {key}"))?;
        if !(value.len() == 7 || value.len() == 9)
            || !value.starts_with('#')
            || !value.as_bytes()[1..].iter().all(u8::is_ascii_hexdigit)
        {
            return Err("theme colors require #RRGGBB or #RRGGBBAA".into());
        }
        colors.insert(key.into(), json!(value));
    }
    // Specify every scalar, including default font families, so switching away
    // from a custom theme cannot retain that theme's typography/radius/shadows.
    let defaults = Theme::default();
    serde_json::from_value(json!({
        "name":spec.name, "mode":spec.mode, "colors":colors,
        "radius":spec.radius, "radius.lg":spec.radius_lg, "shadow":spec.shadow,
        "font.size":spec.font_size,
        "font.family":spec.font_family.unwrap_or_else(|| defaults.font_family.to_string()),
        "mono_font.size":spec.mono_font_size,
        "mono_font.family":spec.mono_font_family.unwrap_or_else(|| defaults.mono_font_family.to_string()),
    })).map_err(|e| e.to_string())
}

pub(crate) fn apply(config: ThemeConfig, cx: &mut App) {
    // update synchronizes legacy colors, component background tokens, semantic
    // tokens and the Base theme used by scrollbars, popovers and input helpers.
    Theme::update(cx, |theme| theme.apply_config(&Rc::new(config)));
}

pub(crate) fn snapshot(cx: &App) -> Value {
    let theme = Theme::global(cx);
    let base = gpui_kit::base::Theme::global(cx);
    json!({
        "name": if theme.mode.is_dark() { &theme.dark_theme.name } else { &theme.light_theme.name },
        "mode":theme.mode, "radius":f32::from(theme.radius), "radius_lg":f32::from(theme.radius_lg),
        "font_size":f32::from(theme.font_size), "font_family":theme.font_family,
        "mono_font_size":f32::from(theme.mono_font_size), "mono_font_family":theme.mono_font_family,
        "shadow":theme.shadow,
        "colors": {
            "background":theme.background.to_hex(), "foreground":theme.foreground.to_hex(),
            "primary":theme.primary.to_hex(), "primary_foreground":theme.primary_foreground.to_hex(),
            "primary_hover":theme.primary_hover.to_hex(), "primary_active":theme.primary_active.to_hex(),
            "button_primary":theme.button_primary.to_hex(),
            "button_primary_hover":theme.button_primary_hover.to_hex(),
            "button_primary_active":theme.button_primary_active.to_hex(),
            "secondary":theme.secondary.to_hex(), "secondary_foreground":theme.secondary_foreground.to_hex(),
            "muted":theme.muted.to_hex(), "muted_foreground":theme.muted_foreground.to_hex(),
            "border":theme.border.to_hex(), "input":theme.input.to_hex(), "ring":theme.ring.to_hex(),
            "selection":theme.selection.to_hex(), "caret":theme.caret.to_hex(),
            "accent":theme.accent.to_hex(), "accent_foreground":theme.accent_foreground.to_hex(),
            "danger":theme.danger.to_hex(), "danger_foreground":theme.danger_foreground.to_hex(),
            "success":theme.success.to_hex(), "warning":theme.warning.to_hex(), "info":theme.info.to_hex(),
            "button":theme.button.to_hex(), "button_hover":theme.button_hover.to_hex(),
            "button_active":theme.button_active.to_hex(), "popover":theme.popover.to_hex(),
            "sidebar":theme.sidebar.to_hex(),
        },
        "base": {"background":base.tokens.colors.background.to_hex(),
                 "primary":base.tokens.colors.primary.to_hex(), "radius":f32::from(base.tokens.radius.md)},
    })
}
