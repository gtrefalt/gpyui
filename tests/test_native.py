"""Real GPUI windows, XTest keyboard/mouse events and native state barriers.

Coordinates are a fallback on bare Xvfb, where no AT-SPI desktop bus is running.
Screenshots are captured for inspection; text outcomes are asserted in Rust state.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.native,
    pytest.mark.skipif(
        os.environ.get("GPYUI_NATIVE_TESTS") != "1", reason="set GPYUI_NATIVE_TESTS=1 on a native display"
    ),
]
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


def wait_file(path, process, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text())
        if process.poll() is not None:
            pytest.fail(f"native process exited {process.returncode} before {path.name}")
        time.sleep(0.05)
    pytest.fail(f"timed out waiting for {path}")


def xdo(*args):
    return subprocess.check_output(["xdotool", *map(str, args)], text=True, timeout=10).strip()


def close_window(window):
    # Send WM_DELETE_WINDOW, the same close request issued by a window manager.
    # xdotool windowclose destroys the X resource directly, so use python Xlib.
    from Xlib import X, display
    from Xlib.protocol.event import ClientMessage

    connection = display.Display()
    resource = connection.create_resource_object("window", int(window))
    event = ClientMessage(
        window=resource,
        client_type=connection.intern_atom("WM_PROTOCOLS"),
        data=(32, [connection.intern_atom("WM_DELETE_WINDOW"), X.CurrentTime, 0, 0, 0]),
    )
    resource.send_event(event, event_mask=0)
    connection.sync()
    connection.close()


@pytest.mark.parametrize(
    "mode,activation",
    [
        ("sync", "mouse"),
        ("async", "keyboard"),
        ("cancel", "mouse"),
        ("error", "mouse"),
        ("history", "mouse"),
        ("queued", "mouse"),
    ],
)
def test_native_python_callback_and_lifecycle(tmp_path, mode, activation):
    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / f"{mode}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_app.py")), str(tmp_path), mode],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            ready = wait_file(tmp_path / "ready.json", process)
            window = xdo("search", "--onlyvisible", "--name", f"^gpyui native test {mode}$").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            # The fixture uses the public default layout: Name, Input, Label, Button.
            xdo("mousemove", "--window", window, 80, 70, "click", 1)
            xdo("type", "--clearmodifiers", "--delay", 20, "X" if mode == "history" else "Ada")
            if activation == "keyboard":
                xdo("key", "Tab", "space")
            else:
                xdo("mousemove", "--window", window, 100, 148, "click", 1)
            if mode == "queued":
                xdo("mousemove", "--window", window, 80, 70, "click", 1)
                xdo("key", "ctrl+a")
                xdo("type", "--clearmodifiers", "--delay", 0, "Grace")
                xdo("mousemove", "--window", window, 100, 148, "click", 1)
                assert wait_file(tmp_path / "activation-1.json", process)["value"] == "Ada"
                assert wait_file(tmp_path / "activation-2.json", process)["value"] == "Grace"
            if mode == "error":
                error = wait_file(tmp_path / "error.json", process)
                assert error == {"type": "ValueError", "message": "callback failure test"}
            elif mode == "cancel":
                waiting = wait_file(tmp_path / "waiting.json", process)
                assert waiting[str(ready["button"])]["disabled"] is True
                close_window(window)
                wait_file(tmp_path / "cancelled.json", process)
            else:
                result = wait_file(
                    tmp_path / ("result-2.json" if mode == "queued" else "result.json"), process
                )
                expected = "AdaX" if mode == "history" else "Grace" if mode == "queued" else "Ada"
                if mode != "queued":
                    assert result["callback_thread"] == "gpyui-asyncio"
                assert result["input_value"] == result["state_value"] == expected
                assert result["snapshot"][str(ready["input"])]["value"] == expected
                assert result["snapshot"][str(ready["label"])]["text"] == f"Hello, {expected}!"
                assert result["snapshot"][str(ready["button"])]["disabled"] is False
                if mode == "history":
                    # Mirroring a Rust edit and redrawing Python's label must not reset undo.
                    xdo("mousemove", "--window", window, 80, 70, "click", 1)
                    xdo("key", "ctrl+z")
                    xdo("mousemove", "--window", window, 100, 148, "click", 1)
                    result = wait_file(tmp_path / "result-2.json", process)
                    assert result["input_value"] == result["state_value"] == "Ada"
                    assert result["snapshot"][str(ready["label"])]["text"] == "Hello, Ada!"
                if mode == "async":
                    waiting = wait_file(tmp_path / "waiting.json", process)
                    assert waiting[str(ready["label"])]["text"] == "Preparing greeting…"
                    assert waiting[str(ready["button"])]["disabled"] is True
                time.sleep(0.25)  # snapshot is a state barrier, not a presentation fence.
                if shutil.which("import"):
                    subprocess.run(
                        ["import", "-window", window, str(ARTIFACTS / f"{mode}.png")], check=True, timeout=10
                    )
                (ARTIFACTS / f"{mode}.json").write_text(json.dumps(result, indent=2) + "\n")
                close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            closed = json.loads((tmp_path / "closed.json").read_text())
            assert "gpyui-asyncio" not in closed["threads"]
            assert not any(t.startswith("asyncio_") for t in closed["threads"])
            assert closed["errors"] == (["callback failure test"] if mode == "error" else [])
        except BaseException:
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
