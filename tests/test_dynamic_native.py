"""Caret, selection and undo must survive runtime tree edits in real native inputs."""

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


@pytest.mark.parametrize("kind", ["input", "textarea", "editor"])
def test_editing_survives_structural_updates_and_visibility(tmp_path, kind):
    import json

    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / f"dynamic-{kind}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_dynamic.py")), str(tmp_path), kind],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        sequence = 0

        def command(action):
            nonlocal sequence
            sequence += 1
            name = f"result-{sequence}"
            temporary = tmp_path / "command.tmp"
            temporary.write_text(json.dumps({"action": action, "name": name}))
            temporary.replace(tmp_path / "command.json")
            return wait_file(tmp_path / f"{name}.json", process)

        try:
            ready = wait_file(tmp_path / "ready.json", process)
            field_id = str(ready["field"])
            window = xdo("search", "--onlyvisible", "--name", f"^gpyui dynamic {kind}$").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            time.sleep(0.3)
            xdo("mousemove", "--window", window, 90, 75, "click", 1)
            xdo("key", "ctrl+End", "Left")
            xdo("type", "--clearmodifiers", "4")
            assert command("snapshot")["value"] == "1243"
            xdo("key", "Left", "Right")  # Native navigation ends the typing transaction.
            inserted = command("insert")
            assert inserted["snapshot"][field_id]["value"] == "1243"
            xdo("type", "--clearmodifiers", "5")
            assert command("snapshot")["value"] == "12453"  # Caret and focus retained.
            xdo("key", "ctrl+z")
            assert command("snapshot")["value"] == "1243"
            command("reorder")
            xdo("key", "ctrl+z")
            assert command("snapshot")["value"] == "123"  # Original undo history retained.
            xdo("key", "ctrl+End", "shift+Left")  # Select the final digit.
            command("move")
            xdo("type", "--clearmodifiers", "6")
            assert command("snapshot")["value"] == "126"  # Selection survived reparenting.
            hidden = command("hide")
            assert hidden["snapshot"][field_id]["visible"] is False
            assert hidden["snapshot"][field_id]["displayed"] is False
            xdo("type", "--clearmodifiers", "7")
            assert command("snapshot")["value"] == "126"  # Hidden input cannot keep editing.
            command("show")
            xdo("mousemove", "--window", window, 380, 75, "click", 1)
            xdo("key", "ctrl+z")
            assert command("snapshot")["value"] == "123"  # Hide/show kept undo history.
            hidden_parent = command("hide_parent")
            assert hidden_parent["snapshot"][field_id]["visible"] is True
            assert hidden_parent["snapshot"][field_id]["displayed"] is False
            command("show_parent")
            detached = command("detach")
            assert detached["snapshot"][field_id]["attached"] is False
            attached = command("reattach")
            assert attached["snapshot"][field_id]["attached"] is True
            xdo("mousemove", "--window", window, 380, 75, "click", 1)
            xdo("key", "ctrl+End")
            xdo("type", "--clearmodifiers", "8")
            assert command("snapshot")["value"] == "1238"
            command("add_button")
            y = 122 if kind == "input" else 178
            xdo("mousemove", "--window", window, 380, y, "click", 1)
            assert wait_file(tmp_path / "click.json", process)["values"] == ["1238"]
            replaced = command("replace")
            assert replaced["snapshot"][field_id]["attached"] is False
            disposed = command("dispose")
            assert field_id not in disposed["snapshot"]
            close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            closed = wait_file(tmp_path / "closed.json", process)
            assert closed["errors"] == []
            assert not any(t == "gpyui-asyncio" or t.startswith("asyncio_") for t in closed["threads"])
        except BaseException:
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
