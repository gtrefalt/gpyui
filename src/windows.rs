//! Window policy belongs to the native UI thread, independently of the control tree.
use gpui_kit::*;
use serde::Deserialize;
use serde_json::{Value, json};

#[derive(Clone, Deserialize)]
#[serde(default, deny_unknown_fields)]
pub(crate) struct WindowConfig {
    pub resizable: bool,
    pub minimizable: bool,
    pub movable: bool,
    pub min_width: f32,
    pub min_height: f32,
    pub position: Option<(f32, f32)>,
    pub state: String,
}

impl Default for WindowConfig {
    fn default() -> Self {
        Self {
            resizable: true,
            minimizable: true,
            movable: true,
            min_width: 240.,
            min_height: 160.,
            position: None,
            state: "normal".into(),
        }
    }
}

impl WindowConfig {
    pub fn parse(value: Option<&str>, width: f32, height: f32) -> Result<Self, String> {
        let config: Self = value
            .map(serde_json::from_str)
            .transpose()
            .map_err(|e| e.to_string())?
            .unwrap_or_default();
        if !config.min_width.is_finite()
            || !config.min_height.is_finite()
            || config.min_width < 1.
            || config.min_height < 1.
        {
            return Err("window minimum size requires finite positive pixels".into());
        }
        config.validate_size(width, height)?;
        if config
            .position
            .is_some_and(|(x, y)| !x.is_finite() || !y.is_finite())
        {
            return Err("window position requires finite coordinates".into());
        }
        if !matches!(config.state.as_str(), "normal" | "maximized" | "fullscreen") {
            return Err("window state requires normal, maximized or fullscreen".into());
        }
        if !config.resizable && config.state == "maximized" {
            return Err("a fixed-size window cannot start maximized".into());
        }
        Ok(config)
    }

    pub fn validate_size(&self, width: f32, height: f32) -> Result<(), String> {
        if !width.is_finite()
            || !height.is_finite()
            || width < self.min_width
            || height < self.min_height
        {
            return Err("window size must be finite and at least its minimum size".into());
        }
        Ok(())
    }

    pub fn options(&self, width: f32, height: f32, cx: &App) -> WindowOptions {
        let bounds = if let Some((x, y)) = self.position {
            Bounds::new(point(px(x), px(y)), size(px(width), px(height)))
        } else {
            match WindowBounds::centered(size(px(width), px(height)), cx) {
                WindowBounds::Windowed(bounds) => bounds,
                _ => unreachable!(),
            }
        };
        WindowOptions {
            window_bounds: Some(match self.state.as_str() {
                "maximized" => WindowBounds::Maximized(bounds),
                "fullscreen" => WindowBounds::Fullscreen(bounds),
                _ => WindowBounds::Windowed(bounds),
            }),
            window_min_size: Some(size(px(self.min_width), px(self.min_height))),
            is_resizable: self.resizable,
            is_minimizable: self.minimizable,
            is_movable: self.movable,
            ..Default::default()
        }
    }
}

pub(crate) enum WindowCommand {
    Title(String),
    Resize(f32, f32),
    Activate,
    Minimize,
    ToggleMaximized,
    ToggleFullscreen,
    Snapshot(u64),
}

pub(crate) struct WindowState {
    pub config: WindowConfig,
    pub title: String,
    requested_size: Size<Pixels>,
}

impl WindowState {
    pub fn new(config: WindowConfig, title: String, width: f32, height: f32) -> Self {
        Self {
            config,
            title,
            requested_size: size(px(width), px(height)),
        }
    }

    pub fn resize(&mut self, width: f32, height: f32, window: &mut Window) {
        self.requested_size = size(px(width), px(height));
        window.resize(self.requested_size);
    }

    // Pinned Linux backends do not constrain compositor resizing from
    // is_resizable. Restore the requested content size on bounds changes,
    // while leaving fullscreen presentation to the compositor.
    pub fn enforce_size(&self, window: &mut Window) {
        let actual = window.viewport_size();
        // Native surfaces round to device pixels; fractional logical sizes must
        // not cause an endless resize cycle when those notifications arrive.
        let changed = (f32::from(actual.width) - f32::from(self.requested_size.width)).abs() >= 1.
            || (f32::from(actual.height) - f32::from(self.requested_size.height)).abs() >= 1.;
        if !self.config.resizable && !window.is_fullscreen() && changed {
            window.resize(self.requested_size);
        }
    }

    pub fn snapshot(&self, window: &Window) -> Value {
        let bounds = window.bounds();
        let content = window.viewport_size();
        json!({"title":self.title, "width":f32::from(content.width),
            "height":f32::from(content.height), "x":f32::from(bounds.origin.x),
            "y":f32::from(bounds.origin.y), "resizable":window.is_resizable(),
            "minimizable":window.is_minimizable(), "movable":self.config.movable,
            "min_width":self.config.min_width, "min_height":self.config.min_height,
            "maximized":window.is_maximized(), "fullscreen":window.is_fullscreen()})
    }
}
