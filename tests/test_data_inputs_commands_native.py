"""Real keyboard/pointer behavior, native values and dependent data refreshes."""

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


@pytest.mark.parametrize("mode", ["table", "inputs", "palette", "multi"])
def test_native_data_inputs_and_command_palette(tmp_path, mode):
    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / f"data-inputs-commands-{mode}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).with_name("native_data_inputs_commands.py")),
                str(tmp_path),
                mode,
            ],
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
            ids = ready["ids"]
            window = xdo(
                "search", "--onlyvisible", "--name", f"^gpyui data inputs commands {mode}$"
            ).splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            time.sleep(0.3)
            if mode == "table":
                xdo("mousemove", "--window", window, 100, 81, "click", 1)
                assert command("snapshot")["key"] == "b"  # Numeric 2 sorts ahead of 10.
                assert command("replace")["key"] == "b"
                xdo("key", "Down")
                assert command("snapshot")["key"] == "c"
                assert command("filter")["key"] == "c"
                xdo("mousemove", "--window", window, 100, 81, "click", 1)
                assert command("snapshot")["key"] == "b"
                xdo("mousemove", "--window", window, 472, 41, "click", 1)
                sort = wait_file(tmp_path / "sorted.json", process)
                assert sort == {
                    "column": -1,
                    "descending": False,
                }  # Header cycles ascending -> unsorted -> descending.
            elif mode == "inputs":
                xdo("mousemove", "--window", window, 210, 40, "click", 1)
                wait_file(tmp_path / "focused.json", process)
                xdo("key", "ctrl+a")
                xdo("type", "--clearmodifiers", "updated")
                xdo("key", "Return")
                assert wait_file(tmp_path / "submitted.json", process) == "updated"
                xdo("mousemove", "--window", window, 130, 87, "click", 1)
                wait_file(tmp_path / "blurred.json", process)
                xdo("key", "ctrl+a")
                xdo("type", "--clearmodifiers", "blocked")
                snapshot = command("snapshot")["snapshot"]
                assert snapshot[str(ids["fixed"])]["value"] == "fixed"
                xdo("mousemove", "--window", window, 513, 128, "click", 1)
                assert float(command("snapshot")["snapshot"][str(ids["number"])]["value"]) == 2
                xdo("mousemove", "--window", window, 130, 136, "click", 1)
                xdo("key", "ctrl+a")
                xdo("type", "--clearmodifiers", "9")
                xdo("mousemove", "--window", window, 210, 40, "click", 1)
                assert float(command("snapshot")["snapshot"][str(ids["number"])]["value"]) == 2
            elif mode == "palette":
                xdo("mousemove", "--window", window, 130, 91, "click", 1)
                xdo("type", "--clearmodifiers", "save")
                xdo("key", "Return")
                assert command("snapshot")["calls"] == []
                command("enable")
                xdo("key", "Return")
                assert wait_file(tmp_path / "executed-1.json", process) == {"input": "Ada", "query": "save"}
                command("disable")
                xdo("key", "ctrl+s", "Return")
                assert len(command("snapshot")["calls"]) == 1
                command("query")
                xdo("key", "Escape")
                assert wait_file(tmp_path / "cancelled.json", process) is True
            else:
                snapshot = command("options")["snapshot"]
                assert snapshot[str(ids["choice"])]["value"] == ["b"]
                snapshot = command("select")["snapshot"]
                assert snapshot[str(ids["choice"])]["value"] == ["b", "c"]
                xdo("mousemove", "--window", window, 130, 40, "click", 1)
                xdo("key", "Down", "Return")
                selected = command("snapshot")["snapshot"][str(ids["choice"])]["value"]
                assert selected != ["b", "c"] and set(selected) <= {"a", "b", "c"}
                xdo("key", "Escape")
            close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            assert wait_file(tmp_path / "closed.json", process)["errors"] == []
        except BaseException:
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
