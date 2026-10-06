"""Themes validate before mutation and respect the application's lifecycle."""

import asyncio
import json
import runpy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from test_dynamic import mounted

from gpyui import Application, ApplicationClosedError, Theme
from gpyui.themes import COLOR_TOKENS, PRESETS


@pytest.mark.parametrize("preset", PRESETS)
@pytest.mark.parametrize("mode", ("light", "dark"))
def test_presets_serialize_and_construct_without_native_extension(preset, mode):
    theme = Theme(preset, mode=mode)
    app = Application(theme=theme)
    assert app.theme is theme and app.theme.mode == mode
    spec = json.loads(json.dumps(theme._spec()))
    assert spec["name"] == preset and spec["mode"] == mode
    assert spec["colors"].keys() <= set(COLOR_TOKENS)
    assert spec["font_family"] is None  # Resolve platform fonts natively.


@pytest.mark.parametrize("value", ["light", "dark", "macos", "windows", "shadcn-blue", "shadcn-zinc"])
def test_application_accepts_appearance_and_preset_strings(value):
    app = Application(theme=value)
    assert isinstance(app.theme, Theme)
    app.theme = "windows"
    assert app.theme.preset == "windows"


@pytest.mark.parametrize("preset", PRESETS[1:])
@pytest.mark.parametrize("mode", ("light", "dark"))
def test_preset_text_contrast_in_primary_states_and_muted_surfaces(preset, mode):
    def luminance(color):
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels
        ]
        return sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear, strict=True))

    colors = Theme(preset, mode=mode)._spec()["colors"]
    for background, foreground in (
        ("primary", "primary_foreground"),
        ("primary_hover", "primary_foreground"),
        ("primary_active", "primary_foreground"),
        ("background", "foreground"),
        ("muted", "muted_foreground"),
        ("secondary", "secondary_foreground"),
    ):
        high, low = sorted((luminance(colors[background]), luminance(colors[foreground])), reverse=True)
        assert (high + 0.05) / (low + 0.05) >= 4.5, (preset, mode, background, foreground)


def test_theme_owns_an_immutable_copy_and_customization_keeps_original():
    colors = {"primary": "#7c3aed", "primary_foreground": "#ffffff"}
    theme = Theme("windows", colors=colors)
    colors["primary"] = "#000000"
    assert theme._spec()["colors"]["primary"] == "#7c3aed"
    with pytest.raises(TypeError):
        theme.colors["primary"] = "#000000"  # ty: ignore[invalid-assignment]
    with pytest.raises(FrozenInstanceError):
        theme.mode = "dark"  # ty: ignore[invalid-assignment]
    customized = theme.customize(colors={"background": "#ffffff"}, radius=9)
    assert customized._spec()["radius"] == 9 and theme._spec()["radius"] == 4
    assert customized._spec()["colors"]["primary"] == "#7c3aed"
    assert "primary_hover" not in customized._spec()["colors"]  # Let Kit derive brand states.
    assert "ring" not in customized._spec()["colors"]
    assert customized._spec()["colors"]["selection"] == "#7c3aed33"
    assert (
        theme.customize(colors={"primary_hover": "#6d28d9"})._spec()["colors"]["primary_hover"] == "#6d28d9"
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"preset": "bad"},
        {"mode": "system"},
        {"colors": {"not_a_color": "#ffffff"}},
        {"colors": {"primary": "red"}},
        {"colors": {"primary": "#abc"}},
        {"colors": {"primary": "#1234567"}},
        {"colors": {"primary": 4}},
        {"colors": []},
        {"radius": -1},
        {"radius": 65},
        {"radius": True},
        {"radius": 4.5},
        {"radius_lg": 65},
        {"font_size": float("nan")},
        {"font_size": float("inf")},
        {"font_size": 7},
        {"mono_font_size": 49},
        {"mono_font_size": None},
        {"font_family": " "},
        {"mono_font_family": "x" * 257},
        {"shadow": 1},
    ],
)
def test_invalid_overrides_fail_before_native_start(overrides):
    with pytest.raises((TypeError, ValueError)):
        Theme(**overrides)


def test_runtime_themes_coalesce_without_structural_updates_and_reject_wrong_thread():
    async def scenario():
        app = Application(theme="macos")
        bridge = mounted(app)
        bridge.set_theme = lambda value: bridge.calls.append(("theme", json.loads(value)))
        with app.batch():
            app.theme = "shadcn-zinc"
            app.theme = Theme("windows", mode="dark")
        assert len(bridge.calls) == 1 and bridge.calls[0][0] == "theme"
        assert bridge.calls[0][1]["name"] == "windows"
        with pytest.raises(ValueError):
            app.theme = "invalid"
        assert app.theme.preset == "windows" and len(bridge.calls) == 1
        with pytest.raises(RuntimeError, match="callback loop"):
            await asyncio.to_thread(setattr, app, "theme", "macos")
        assert app.theme.preset == "windows"
        app._phase = "closed"
        with pytest.raises(ApplicationClosedError):
            app.theme = "macos"

    asyncio.run(scenario())


def test_enqueue_failure_keeps_theme_pending_for_retry():
    async def scenario():
        app = Application()
        bridge = mounted(app)

        def fail(_):
            raise RuntimeError("queue full")

        bridge.set_theme = fail
        app.theme = "macos"
        with pytest.raises(RuntimeError, match="queue full"):
            app.update()
        assert app._theme_dirty
        bridge.set_theme = lambda value: bridge.calls.append(("theme", json.loads(value)))
        app.update()
        assert not app._theme_dirty and len(bridge.calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("preset", ("macos", "windows"))
def test_appearance_example_constructs_and_switches_existing_controls(preset):
    example = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/appearance.py"))
    app, controls = example["build_app"](preset)
    field = controls["name"]
    field.value = "Retain me"
    controls["dark"].value = True
    controls["dark"]._handlers["change"](None)
    assert app.theme.mode == "dark" and controls["name"] is field and field.value == "Retain me"
