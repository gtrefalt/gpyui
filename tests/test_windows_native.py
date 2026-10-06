"""Observe actual X11 geometry, minimum hints, fixed sizing and native editing."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_native import ARTIFACTS, close_window, wait_file, xdo

pytestmark = [
    pytest.mark.native,
    pytest.mark.skipif(os.environ.get("GPYUI_NATIVE_TESTS") != "1", reason="requires native display"),
]


@pytest.mark.parametrize("resizable", (False, True))
def test_window_geometry_policy_live_title_resize_caret_and_undo(tmp_path, resizable):
    ARTIFACTS.mkdir(exist_ok=True)
    with (ARTIFACTS / f"window-{resizable}.log").open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).with_name("native_windows.py")),
                str(tmp_path),
                str(resizable).lower(),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    sequence = 0

    def command(action="snapshot", **args):
        nonlocal sequence
        sequence += 1
        name = f"result-{sequence}"
        path = tmp_path / "command.tmp"
        path.write_text(json.dumps({"action": action, "name": name, **args}))
        path.replace(tmp_path / "command.json")
        return wait_file(tmp_path / f"{name}.json", process)

    def expect(width, height, value=None):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = command()
            if (result["window"]["width"], result["window"]["height"]) == (width, height):
                if value is None or result["nodes"][str(ready["field"])]["value"] == value:
                    return result
        pytest.fail(f"unexpected window/editor state: {result}")

    try:
        ready = wait_file(tmp_path / "ready.json", process)
        assert ready["window"]["resizable"] is resizable
        assert (ready["window"]["x"], ready["window"]["y"]) == (100, 80)
        assert ready["window"]["min_width"] == 300 and ready["window"]["min_height"] == 200
        window = xdo("search", "--onlyvisible", "--name", "^gpyui window regression$").splitlines()[-1]
        from Xlib import display

        connection = display.Display()
        resource = connection.create_resource_object("window", int(window))
        hints = resource.get_wm_normal_hints()
        assert (hints.min_width, hints.min_height) == (300, 200)
        connection.close()
        expect(480, 300)
        xdo("windowfocus", "--sync", window)
        xdo("mousemove", "--window", window, 80, 68, "click", 1)
        xdo("key", "ctrl+End", "Left")
        command("title", title="Renamed window")
        assert xdo("getwindowname", window) == "Renamed window"
        command("resize", width=520, height=340)
        expect(520, 340)
        xdo("windowsize", window, 640, 420)
        expect(640, 420) if resizable else expect(520, 340)
        xdo("type", "--clearmodifiers", "4")
        expect(640 if resizable else 520, 420 if resizable else 340, "1243")
        xdo("key", "ctrl+z")
        expect(640 if resizable else 520, 420 if resizable else 340, "123")
        command("resize", width=540.5, height=360.5)
        # GPUI/native surfaces round logical sizes to device pixels. A fixed
        # policy must settle without a notification/resize feedback loop.
        time.sleep(0.1)
        fractional = command()["window"]
        assert abs(fractional["width"] - 540.5) < 1
        assert abs(fractional["height"] - 360.5) < 1
        close_window(window)
        assert process.wait(timeout=10) == 0
        closed = wait_file(tmp_path / "closed.json", process)
        assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"]
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
