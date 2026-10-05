"""Real pointer/keyboard menu interaction and shared command state."""

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


@pytest.mark.parametrize("mode", ["kit", "native"])
def test_shared_commands_menus_shortcuts_and_editing(tmp_path, mode):
    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / f"commands-{mode}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_commands.py")), str(tmp_path), mode],
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
            window = xdo("search", "--onlyvisible", "--name", f"^gpyui commands {mode}$").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            time.sleep(0.3)
            xdo("mousemove", "--window", window, 90, 115, "click", 1)
            xdo("key", "ctrl+End", "Left")
            xdo("type", "--clearmodifiers", "4")
            assert command("snapshot")["snapshot"][str(ready["field"])]["value"] == "1243"
            xdo("key", "ctrl+s")
            result = wait_file(tmp_path / "save-1.json", process)
            assert result["value"] == "1243" and result["thread"] == "gpyui-asyncio"
            xdo("key", "ctrl+z")
            assert command("snapshot")["snapshot"][str(ready["field"])]["value"] == "123"
            xdo("mousemove", "--window", window, 65, 160, "click", 1)
            assert wait_file(tmp_path / "save-2.json", process)["value"] == "123"
            xdo("mousemove", "--window", window, 125, 160, "click", 1)
            time.sleep(0.2)
            xdo("key", "Down", "Return")
            assert wait_file(tmp_path / "save-3.json", process)["value"] == "123"
            xdo("mousemove", "--window", window, 90, 115, "click", 3)
            time.sleep(0.2)
            xdo("key", "Down", "Return")
            assert wait_file(tmp_path / "save-4.json", process)["value"] == "123"
            xdo("mousemove", "--window", window, 40, 37, "click", 1)
            time.sleep(0.2)
            xdo("key", "Down", "Return")
            assert wait_file(tmp_path / "save-5.json", process)["value"] == "123"
            # Navigate a real nested submenu and restore the checked command
            # through its shared shortcut before the disabled-state checks.
            xdo("mousemove", "--window", window, 125, 160, "click", 1)
            time.sleep(0.2)
            xdo("key", "Down", "Down", "Right")
            time.sleep(0.2)
            xdo("key", "Down", "Return")
            time.sleep(0.2)
            assert command("snapshot")["snapshot"][str(ready["toggle"])]["checked"] is False
            xdo("key", "ctrl+shift+b")
            time.sleep(0.2)
            assert command("snapshot")["snapshot"][str(ready["toggle"])]["checked"] is True
            xdo("mousemove", "--window", window, 40, 37, "click", 1)
            time.sleep(0.2)
            disabled = command("disable")
            assert disabled["snapshot"][str(ready["save"])]["enabled"] is False
            assert disabled["snapshot"][str(ready["button"])]["disabled"] is True
            # Reloading an open application menu restores editor focus.
            xdo("key", "ctrl+s")
            time.sleep(0.2)
            assert len(command("snapshot")["calls"]) == 5
            command("enable")
            xdo("key", "ctrl+shift+b")
            snapshot = command("snapshot")["snapshot"]
            assert snapshot[str(ready["toggle"])]["checked"] is False
            assert snapshot[str(ready["sidebar"])]["visible"] is False
            if mode == "kit":
                # Rebuild an open popup from current items; execute the replacement
                # command through keyboard navigation rather than reopening it.
                xdo("mousemove", "--window", window, 125, 160, "click", 1)
                time.sleep(0.2)
                command("replace")
                time.sleep(0.2)
                xdo("key", "Down", "Return")
                time.sleep(0.2)
                assert command("snapshot")["snapshot"][str(ready["toggle"])]["checked"] is True
                # An open assigned context menu must dismiss when removed.
                xdo("mousemove", "--window", window, 90, 115, "click", 3)
                time.sleep(0.2)
                command("remove_menu")
                xdo("key", "Escape")
            command("execute")
            assert wait_file(tmp_path / "save-6.json", process)["value"] == "123"
            command("add_command")
            xdo("key", "ctrl+shift+d")
            assert wait_file(tmp_path / "dynamic.json", process)["value"] == "123"
            close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            closed = wait_file(tmp_path / "closed.json", process)
            assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"]
        except BaseException:
            if "window" in locals() and process.poll() is None:
                subprocess.run(
                    ["import", "-window", window, str(ARTIFACTS / f"commands-{mode}-failure.png")], timeout=10
                )
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
