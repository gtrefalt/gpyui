"""Capture native catalog previews; use scripts/native-display.sh on headless Linux."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from component_catalog import SAMPLES

ROOT = Path(__file__).resolve().parents[1]


def slug(name):
    import re

    return re.sub(r"(?<!^)(?=[A-Z][a-z])", "-", name).lower()


def capture(name):
    directory = ROOT / "artifacts/docs-captures" / name
    directory.mkdir(parents=True, exist_ok=True)
    for filename in ("ready.json", "error.json", "closed.json"):
        (directory / filename).unlink(missing_ok=True)
    with (directory / "app.log").open("w") as log:
        app = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "examples/component_preview.py"),
                name,
                "--state-dir",
                str(directory),
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    try:
        deadline = time.monotonic() + 15
        while not (directory / "ready.json").exists():
            if app.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError(f"{name} failed to mount: {log.name}")
            time.sleep(0.03)
        window = subprocess.check_output(
            ["xdotool", "search", "--onlyvisible", "--name", f"^gpyui component {name}$"], text=True
        ).splitlines()[-1]
        subprocess.run(["xdotool", "windowfocus", "--sync", window], check=True)
        action = SAMPLES[name].action
        if action in {"hover", "click"}:
            subprocess.run(["xdotool", "mousemove", "--window", window, "90", "155"], check=True)
            if action == "click":
                subprocess.run(["xdotool", "click", "1"], check=True)
            time.sleep(1.2)
        else:
            time.sleep(0.15)
        output = ROOT / "docs/screenshots/components" / f"{slug(name)}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["import", "-window", window, str(output)], check=True, timeout=10)
        subprocess.run(["xdotool", "key", "Escape"], check=True)
        from Xlib import X, display, protocol

        connection = display.Display()
        resource = connection.create_resource_object("window", int(window))
        resource.send_event(
            protocol.event.ClientMessage(
                window=resource,
                client_type=connection.intern_atom("WM_PROTOCOLS"),
                data=(32, [connection.intern_atom("WM_DELETE_WINDOW"), X.CurrentTime, 0, 0, 0]),
            ),
            event_mask=0,
        )
        connection.sync()
        connection.close()
        assert app.wait(timeout=10) == 0, name
        closed = json.loads((directory / "closed.json").read_text())
        assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"], name
        assert not (directory / "error.json").exists(), name
        print(f"Captured {name}", flush=True)
    finally:
        if app.poll() is None:
            app.terminate()
            app.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("components", nargs="*", choices=list(SAMPLES))
    args = parser.parse_args()
    for name in args.components or SAMPLES:
        capture(name)
