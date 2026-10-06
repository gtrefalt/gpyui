"""Actual Kit forms, native editing history, async save/retry and shutdown."""

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
    pytest.mark.skipif(os.environ.get("GPYUI_NATIVE_TESTS") != "1", reason="requires a native display"),
]


def test_settings_form_native_editing_validation_save_retry_and_shutdown(tmp_path):
    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / "forms-native.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_forms.py")), str(tmp_path)],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        sequence = 0

        def command(action="snapshot"):
            nonlocal sequence
            sequence += 1
            name = f"result-{sequence}"
            temporary = tmp_path / "command.tmp"
            temporary.write_text(json.dumps({"action": action, "name": name}))
            temporary.replace(tmp_path / "command.json")
            return wait_file(tmp_path / f"{name}.json", process)

        def until(predicate):
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                result = command()
                if predicate(result):
                    return result
                time.sleep(0.05)
            pytest.fail("Native form did not reach the expected state")

        def capture(name):
            time.sleep(0.15)
            output = ARTIFACTS / f"settings-{name}.png"
            subprocess.run(["import", "-window", window, str(output)], check=True, timeout=10)
            # Keep published previews opt-in; CI should verify behavior, not mutate docs.
            if os.environ.get("GPYUI_CAPTURE_SETTINGS") == "1":
                import shutil

                target = Path(__file__).resolve().parents[1] / "docs/screenshots" / output.name
                shutil.copy2(output, target)

        def value_is(expected):
            # External XTest events and snapshot commands have separate queues.
            # Wait for the edit instead of assuming a snapshot fences presentation.
            until(lambda result: result["snapshot"][str(ready["endpoint"])]["value"] == expected)

        try:
            ready = wait_file(tmp_path / "ready.json", process)
            time.sleep(0.5)
            window = xdo("search", "--onlyvisible", "--name", "Workspace settings").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            capture("light")
            initial = command()["snapshot"]
            assert initial[str(ready["command"])]["enabled"] is True
            command("invalid")
            time.sleep(0.15)
            xdo("mousemove", "--window", window, 100, 432, "click", 1)
            xdo("key", "ctrl+End", "Left")
            xdo("type", "--clearmodifiers", "X")
            value_is("abcXd")
            xdo("key", "ctrl+s")
            invalid = until(lambda result: bool(result["errors"]))
            assert invalid["errors"] == {"endpoint": "Enter a complete HTTPS URL."}
            assert invalid["attempts"] == 0 and not (tmp_path / "settings.json").exists()
            assert invalid["snapshot"][str(ready["endpoint_field"])]["error"] == invalid["errors"]["endpoint"]
            capture("validation")
            # An unchanged focus and insertion position survive the redraw.
            xdo("type", "--clearmodifiers", "Y")
            value_is("abcXYd")
            xdo("key", "ctrl+z")
            value_is("abcd")
            xdo("key", "ctrl+y")
            value_is("abcXYd")
            # Preserve a selection over validation, then replace only that selection.
            xdo("key", "ctrl+End", "Left", "shift+Left", "ctrl+s")
            time.sleep(0.15)
            until(lambda result: not result["busy"])
            xdo("type", "--clearmodifiers", "Q")
            value_is("abcXQd")
            xdo("key", "ctrl+z")
            value_is("abcXYd")
            hidden = command("hide")["snapshot"]
            assert hidden[str(ready["endpoint"])]["displayed"] is False
            shown = command("show")["snapshot"]
            assert shown[str(ready["endpoint"])]["displayed"] is True
            assert shown[str(ready["endpoint"])]["value"] == "abcXYd"
            time.sleep(0.15)
            xdo("mousemove", "--window", window, 100, 432, "click", 1)
            xdo("key", "ctrl+z")
            value_is("abcd")
            command("valid")
            xdo("key", "ctrl+s")
            busy = until(lambda result: result["busy"])
            assert busy["snapshot"][str(ready["save"])]["disabled"] is True
            assert busy["snapshot"][str(ready["retry"])]["disabled"] is True
            xdo("key", "ctrl+s", "ctrl+s")
            failed = until(lambda result: "Demo save failure" in result["error"])
            assert failed["attempts"] == 1 and not failed["busy"]
            assert failed["snapshot"][str(ready["retry"])]["visible"] is True
            assert failed["snapshot"][str(ready["save"])]["disabled"] is False
            capture("retry")
            # The real Retry button uses the same command as Save and Ctrl+S.
            xdo("mousemove", "--window", window, 185, 660, "click", 1)
            until(lambda result: result["attempts"] == 2 and not result["busy"])
            payload = json.loads((tmp_path / "settings.json").read_text())
            assert payload["endpoint"] == "https://sync.example.com" and payload["interval"] == 30
            capture("saved")
            command("save")
            until(lambda result: result["busy"] and result["attempts"] == 3)
            close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            closed = wait_file(tmp_path / "closed.json", process)
            assert closed["errors"] == [] and not closed["busy"]
            assert "gpyui-asyncio" not in closed["threads"]
            assert not any(thread.startswith("asyncio_") for thread in closed["threads"])
        except BaseException:
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
