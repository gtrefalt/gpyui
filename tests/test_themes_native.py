"""Observe applied native tokens and actual editing across live theme changes."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_native import ARTIFACTS, close_window, wait_file, xdo

from gpyui import Theme

pytestmark = [
    pytest.mark.native,
    pytest.mark.skipif(os.environ.get("GPYUI_NATIVE_TESTS") != "1", reason="requires a native display"),
]


def rgb(hex_color):
    return [int(hex_color[index : index + 2], 16) for index in (1, 3, 5)]


def assert_color(actual, expected):
    # Kit's HSL conversion can truncate a channel by one on serialization.
    assert all(abs(a - b) <= 1 for a, b in zip(rgb(actual), rgb(expected), strict=True)), (actual, expected)


def assert_theme(actual, theme):
    spec = theme._spec()
    for key in ("name", "mode", "radius", "radius_lg", "font_size", "mono_font_size", "shadow"):
        assert actual[key] == spec[key], key
    for key, color in spec["colors"].items():
        assert_color(actual["colors"][key], color)
    assert_color(actual["colors"]["button_primary"], actual["colors"]["primary"])
    assert_color(actual["colors"]["button_primary_hover"], actual["colors"]["primary_hover"])
    assert_color(actual["colors"]["button_primary_active"], actual["colors"]["primary_active"])
    assert_color(actual["base"]["primary"], actual["colors"]["primary"])
    assert_color(actual["base"]["background"], actual["colors"]["background"])
    assert actual["base"]["radius"] == actual["radius"]


@pytest.mark.parametrize(
    "preset,mode", [("macos", "light"), ("macos", "dark"), ("windows", "light"), ("windows", "dark")]
)
def test_native_presets_live_switching_selection_and_undo(tmp_path, preset, mode):
    ARTIFACTS.mkdir(exist_ok=True)
    with (ARTIFACTS / f"themes-{preset}-{mode}.log").open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_themes.py")), str(tmp_path), preset, mode],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        sequence = 0

        def command(action="snapshot", **kwargs):
            nonlocal sequence
            sequence += 1
            name = f"result-{sequence}"
            temporary = tmp_path / "command.tmp"
            temporary.write_text(json.dumps({"action": action, "name": name, **kwargs}))
            temporary.replace(tmp_path / "command.json")
            return wait_file(tmp_path / f"{name}.json", process)

        def switch(theme):
            result = command(
                "theme",
                theme={key: value for key, value in vars(theme).items() if key != "colors"}
                | {"colors": dict(theme.colors or {})},
            )
            assert_theme(result["theme"], theme)
            return result

        def expect_node(control, property, value):
            # XTest input, bridge snapshots and Python callbacks have separate
            # queues. A snapshot does not fence an earlier external key event.
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                actual = command()["nodes"][str(ready[control])][property]
                if actual == value:
                    return
                time.sleep(0.03)
            assert actual == value

        try:
            ready = wait_file(tmp_path / "ready.json", process)
            assert_theme(ready["theme"], Theme(preset, mode=mode))
            window = xdo("search", "--onlyvisible", "--name", "^gpyui theme regression$").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            time.sleep(0.2)
            xdo("mousemove", "--window", window, 90, 68, "click", 1)
            xdo("key", "ctrl+End", "Left")
            switch(
                Theme(
                    "windows" if preset == "macos" else "macos", mode="dark" if mode == "light" else "light"
                )
            )
            xdo("type", "--clearmodifiers", "4")
            expect_node("field", "value", "1243")
            xdo("key", "ctrl+z")
            expect_node("field", "value", "123")
            # Select a native character, then change palette/radius/typography.
            xdo("key", "ctrl+End", "Left", "shift+Left")
            switch(
                Theme(
                    "shadcn-blue",
                    mode="dark",
                    radius=9,
                    font_size=16,
                    shadow=False,
                    colors={
                        "primary": "#7c3aed",
                        "primary_foreground": "#ffffff",
                        "control_background": "#21152e",
                        "switch_checked": "#b94bee",
                        "switch_thumb": "#f4f4f5",
                        "slider_thumb": "#e4e4e7",
                    },
                )
            )
            xdo("type", "--clearmodifiers", "5")
            expect_node("field", "value", "153")
            xdo("key", "ctrl+z")
            expect_node("field", "value", "123")
            # The multiline editor also retains native selection and undo.
            xdo("mousemove", "--window", window, 90, 340, "click", 1)
            xdo("key", "ctrl+End", "Left", "shift+Left")
            switch(Theme("shadcn-zinc"))
            xdo("type", "--clearmodifiers", "6")
            expect_node("area", "value", "163")
            xdo("key", "ctrl+z")
            expect_node("area", "value", "123")
            default = switch(Theme())
            assert default["theme"]["radius"] == 6 and default["theme"]["shadow"] is True
            assert default["theme"]["font_size"] == 16  # No leaked custom scalars.
            assert default["theme"]["colors"]["primary"] != "#7C3AED"
            assert_color(
                default["theme"]["colors"]["control_background"], default["theme"]["colors"]["background"]
            )
            assert_color(default["theme"]["colors"]["switch_checked"], default["theme"]["colors"]["primary"])
            # The presentation frame must keep Kit's keyboard traversal/activation.
            switch(Theme(preset, mode=mode))
            xdo("mousemove", "--window", window, 90, 68, "click", 1)
            xdo("key", "Tab", "space")  # single-line editor -> primary button
            expect_node("clicks", "text", "Clicked from Python")
            xdo("key", "Tab", "space")
            expect_node("checkbox", "value", True)
            xdo("key", "Tab", "space")
            expect_node("switch", "value", True)
            xdo("key", "Tab", "Return", "Down", "Return")
            expect_node("select", "value", "Two")
            subprocess.run(
                ["import", "-window", window, str(ARTIFACTS / f"themes-{preset}-{mode}.png")], check=True
            )
            close_window(window)
            assert process.wait(timeout=10) == 0
            closed = wait_file(tmp_path / "closed.json", process)
            assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"]
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
