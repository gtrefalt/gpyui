"""Immutable native theme presets. Component styles continue to use semantic colors."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any

# Keep this vocabulary aligned with src/theme.rs, which maps it to Kit ThemeConfig.
COLOR_TOKENS = (
    "background",
    "foreground",
    "primary",
    "primary_foreground",
    "primary_hover",
    "primary_active",
    "secondary",
    "secondary_foreground",
    "muted",
    "muted_foreground",
    "border",
    "input",
    "ring",
    "accent",
    "accent_foreground",
    "danger",
    "danger_foreground",
    "success",
    "warning",
    "info",
    "selection",
    "caret",
    "button",
    "button_hover",
    "button_active",
    "popover",
    "sidebar",
    "control_background",
    "switch",
    "switch_thumb",
    "switch_checked",
    "slider",
    "slider_thumb",
)
PRESETS = ("default", "macos", "windows", "shadcn-zinc", "shadcn-blue")


def _palette(preset: str, mode: str) -> dict[str, str]:
    dark = mode == "dark"
    if preset == "default":
        return {}
    if preset == "macos":
        colors = (
            [
                "#1c1c1e",
                "#f5f5f7",
                "#0a84ff",
                "#001d3b",
                "#409cff",
                "#178aff",
                "#3a3a3c",
                "#2c2c2e",
                "#a1a1a6",
                "#48484a",
                "#183859",
                "#ff6961",
                "#6cdd85",
                "#ffd60a",
                "#64d2ff",
            ]
            if dark
            else [
                "#ececec",
                "#1d1d1f",
                "#006fdb",
                "#ffffff",
                "#006be0",
                "#005ec4",
                "#e8e8ed",
                "#ededf0",
                "#636366",
                "#c7c7cc",
                "#e4efff",
                "#d70015",
                "#248a3d",
                "#8a5700",
                "#0069d9",
            ]
        )
    elif preset == "windows":
        colors = (
            [
                "#202020",
                "#ffffff",
                "#60cdff",
                "#002b42",
                "#7bd6ff",
                "#4cc2f1",
                "#373737",
                "#2d2d2d",
                "#ababab",
                "#5b5b5b",
                "#163e52",
                "#ff99a4",
                "#6ccb5f",
                "#fce100",
                "#60cdff",
            ]
            if dark
            else [
                "#f3f3f3",
                "#1b1b1b",
                "#005fb8",
                "#ffffff",
                "#00539f",
                "#004782",
                "#f0f0f0",
                "#f3f3f3",
                "#606060",
                "#d1d1d1",
                "#e5f1fb",
                "#b10e1e",
                "#0f7b0f",
                "#8a5800",
                "#005fb8",
            ]
        )
    else:
        colors = (
            [
                "#09090b",
                "#fafafa",
                "#fafafa",
                "#18181b",
                "#e4e4e7",
                "#d4d4d8",
                "#27272a",
                "#27272a",
                "#a1a1aa",
                "#3f3f46",
                "#27272a",
                "#ff6467",
                "#4ade80",
                "#facc15",
                "#60a5fa",
            ]
            if dark
            else [
                "#ffffff",
                "#09090b",
                "#18181b",
                "#fafafa",
                "#27272a",
                "#3f3f46",
                "#f4f4f5",
                "#f4f4f5",
                "#6b6b74",
                "#e4e4e7",
                "#f4f4f5",
                "#dc2626",
                "#15803d",
                "#a16207",
                "#2563eb",
            ]
        )
    keys = (
        "background",
        "foreground",
        "primary",
        "primary_foreground",
        "primary_hover",
        "primary_active",
        "secondary",
        "muted",
        "muted_foreground",
        "border",
        "accent",
        "danger",
        "success",
        "warning",
        "info",
    )
    palette = dict(zip(keys, colors, strict=True))
    if preset == "shadcn-blue":
        palette.update(
            primary="#2563eb",
            primary_foreground="#ffffff",
            primary_hover="#1d4ed8",
            primary_active="#1e40af",
        )
    palette.update(
        secondary_foreground=palette["foreground"],
        accent_foreground=palette["foreground"],
        danger_foreground="#09090b" if dark else "#ffffff",
        input=palette["border"],
        ring=palette["primary"],
        caret=palette["primary"],
        selection=palette["primary"] + "33",
        button=palette["secondary"] if dark else "#ffffff",
        button_hover=palette["muted"],
        button_active=palette["border"],
        popover=palette["background"],
        sidebar=palette["muted"],
    )
    if preset == "macos":
        palette.update(
            control_background="#343434" if dark else "#ffffff",
            popover="#2c2c2e" if dark else "#ffffff",
            sidebar="#252527" if dark else "#e3e3e5",
            switch="#626264" if dark else "#b8b8bb",
            switch_thumb="#ffffff",
            switch_checked="#30d158" if dark else "#34c759",
            slider=palette["primary"],
            slider_thumb="#ffffff",
            button="#454547" if dark else "#ffffff",
            button_hover="#525254" if dark else "#f5f5f5",
            button_active="#38383a" if dark else "#e4e4e4",
        )
    elif preset == "windows":
        palette.update(
            control_background="#292929" if dark else "#ffffff",
            popover="#2c2c2c" if dark else "#ffffff",
            sidebar="#262626" if dark else "#ebebeb",
            switch="#666666" if dark else "#8a8a8a",
            switch_thumb="#ffffff",
            switch_checked=palette["primary"],
            slider=palette["primary"],
            slider_thumb=palette["primary"],
        )
    return palette


@dataclass(frozen=True)
class Theme:
    """A preset with optional semantic color, radius, typography and shadow overrides.

    Use Theme("macos") or Theme("windows", mode="dark"). Fonts default to Kit's
    platform fonts. Explicit font families must be installed on the target desktop.
    """

    preset: str = "default"
    mode: str = "light"
    colors: Mapping[str, str] | None = None
    radius: int | None = None
    radius_lg: int | None = None
    font_size: float | None = None
    font_family: str | None = None
    mono_font_size: float = 13
    mono_font_family: str | None = None
    shadow: bool = True

    def __post_init__(self) -> None:
        if self.preset not in PRESETS:
            raise ValueError(f"preset requires one of {PRESETS}")
        if self.mode not in ("light", "dark"):
            raise ValueError("mode requires 'light' or 'dark'")
        if self.colors is not None and not isinstance(self.colors, Mapping):
            raise TypeError("colors requires a mapping of semantic tokens to hex colors")
        overrides = dict(self.colors or {})
        for token, color in overrides.items():
            if token not in COLOR_TOKENS:
                raise ValueError(f"unknown theme color: {token}")
            if (
                not isinstance(color, str)
                or re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", color) is None
            ):
                raise ValueError(f"{token} requires #RRGGBB or #RRGGBBAA")
        for key in ("radius", "radius_lg"):
            value = getattr(self, key)
            if value is not None and (type(value) is not int or not 0 <= value <= 64):
                raise ValueError(f"{key} requires an integer between 0 and 64 pixels")
        for key in ("font_size", "mono_font_size"):
            value = getattr(self, key)
            if (value is None and key == "mono_font_size") or (
                value is not None and (type(value) not in (int, float) or not 8 <= value <= 48)
            ):
                raise ValueError(f"{key} requires a finite number between 8 and 48 pixels")
        for key in ("font_family", "mono_font_family"):
            value = getattr(self, key)
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 256):
                raise ValueError(f"{key} requires a nonempty installed font family of at most 256 characters")
        if type(self.shadow) is not bool:
            raise TypeError("shadow requires bool")
        object.__setattr__(self, "colors", MappingProxyType(overrides))

    def customize(self, **overrides: Any) -> Theme:
        """Return a new theme. Color overrides merge with previous custom colors."""
        if "colors" in overrides:
            colors = overrides["colors"]
            if not isinstance(colors, Mapping):
                raise TypeError("colors requires a mapping")
            overrides["colors"] = dict(self.colors or {}) | dict(colors)
        return replace(self, **overrides)

    def _spec(self) -> dict[str, Any]:
        palette = _palette(self.preset, self.mode)
        overrides = dict(self.colors or {})
        # Derive hover/active/ring/caret from a replaced brand color, unless explicit.
        if "primary" in overrides:
            for key in ("primary_hover", "primary_active", "ring", "caret", "slider"):
                palette.pop(key, None)
            if self.preset == "windows":
                palette.pop("switch_checked", None)
                palette.pop("slider_thumb", None)
            palette["selection"] = overrides["primary"][:7] + "33"
        if "border" in overrides:
            palette.pop("input", None)
        palette.update(overrides)
        return {
            "name": self.preset,
            "mode": self.mode,
            "colors": palette,
            "radius": self.radius
            if self.radius is not None
            else (4 if self.preset == "windows" else 5 if self.preset == "macos" else 6),
            "radius_lg": self.radius_lg
            if self.radius_lg is not None
            else (10 if self.preset == "macos" else 8),
            "font_size": self.font_size
            if self.font_size is not None
            else (13 if self.preset == "macos" else 14 if self.preset == "windows" else 16),
            "font_family": self.font_family,
            "mono_font_size": self.mono_font_size,
            "mono_font_family": self.mono_font_family,
            "shadow": self.shadow,
        }


def _resolve_theme(value: str | Theme) -> Theme:
    if isinstance(value, Theme):
        return value
    if isinstance(value, str):
        if value in ("light", "dark"):
            return Theme(mode=value)
        return Theme(value)
    raise TypeError("theme requires a Theme or preset/appearance string")
