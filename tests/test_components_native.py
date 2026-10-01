import json
import os
import shutil
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


def state_until(directory, process, predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = wait_file(directory / "state.json", process)
        if predicate(state):
            return state
        time.sleep(0.05)
    pytest.fail(f"native state did not converge: {state}")


@pytest.mark.parametrize(
    "mode,theme", [("workspace", "light"), ("workspace", "dark"), ("gallery", "light"), ("overlays", "light")]
)
def test_native_examples_and_python_order(tmp_path, mode, theme):
    ARTIFACTS.mkdir(exist_ok=True)
    log_path = ARTIFACTS / f"{mode}-{theme}.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).with_name("native_catalog.py")), str(tmp_path), mode, theme],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            ready = wait_file(tmp_path / "ready.json", process)
            name = {"workspace": "Paper trading", "gallery": "Component gallery", "overlays": "Overlay test"}[
                mode
            ]
            window = xdo("search", "--onlyvisible", "--name", name).splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            time.sleep(0.3)
            if shutil.which("import"):
                subprocess.run(
                    ["import", "-window", window, str(ARTIFACTS / f"{mode}-{theme}.png")],
                    check=True,
                    timeout=10,
                )
            if mode == "workspace":
                # Native Kit order button in the right pane; no callback injection.
                xdo("mousemove", "--window", window, 1030, 470, "click", 1)
                state = state_until(
                    tmp_path,
                    process,
                    lambda s: any(n.get("text") == "Filled: Buy 10 NVDA" for n in s.values()),
                )
                orders = next(
                    n for n in state.values() if n.get("columns") == ["Symbol", "Side", "Quantity", "Price"]
                )
                assert orders["rows"][-1] == ["NVDA", "Buy", "10", "$192.60"]
            elif mode == "gallery":
                types = {n["type"] for n in ready.values()}
                assert {
                    "checkbox",
                    "slider",
                    "select",
                    "combobox",
                    "table",
                    "calendar",
                    "color_picker",
                    "textarea",
                    "number_input",
                    "otp_input",
                    "carousel",
                    "dialog",
                    "sheet",
                    "line_chart",
                    "area_chart",
                    "bar_chart",
                    "pie_chart",
                    "candlestick_chart",
                } <= types
            else:
                for kind, y in [("dialog", 72), ("sheet", 116)]:
                    xdo("mousemove", "--window", window, 90, y, "click", 1)
                    state_until(
                        tmp_path,
                        process,
                        lambda s, kind=kind: any(
                            n.get("type") == kind and n.get("value") is True for n in s.values()
                        ),
                    )
                    time.sleep(0.2)
                    xdo("key", "Escape")
                    state_until(
                        tmp_path,
                        process,
                        lambda s, kind=kind: any(
                            n.get("type") == kind and n.get("value") is False for n in s.values()
                        ),
                    )
            time.sleep(0.4)
            if shutil.which("import"):
                subprocess.run(
                    ["import", "-window", window, str(ARTIFACTS / f"{mode}-{theme}-after.png")],
                    check=True,
                    timeout=10,
                )
            close_window(window)
            assert process.wait(timeout=10) == 0, log_path.read_text()
            assert json.loads((tmp_path / "closed.json").read_text())["errors"] == []
            assert not (tmp_path / "error.json").exists()
        except BaseException:
            print(log_path.read_text())
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
