"""Capture real native appearance previews on an X11 desktop (or under Xvfb)."""

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from appearance import build_app  # noqa: E402 -- import the checkout example


def preview(preset, mode, directory):
    async def started():
        await asyncio.sleep(0.5)
        (directory / "ready.json").write_text(json.dumps(await app.theme_snapshot()))

    app, _ = build_app(preset, mode, on_start=started)
    app.run()
    (directory / "closed.json").write_text(json.dumps({"errors": [str(error) for error in app.errors]}))


def capture(preset, mode):
    with tempfile.TemporaryDirectory(prefix="gpyui-theme-") as temporary:
        directory = Path(temporary)
        with (directory / "native.log").open("w") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__)),
                    "--preview",
                    preset,
                    "--mode",
                    mode,
                    "--state-dir",
                    str(directory),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        try:
            deadline = time.monotonic() + 20
            while not (directory / "ready.json").exists():
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError((directory / "native.log").read_text())
                time.sleep(0.03)
            theme = json.loads((directory / "ready.json").read_text())
            assert theme["name"] == preset and theme["mode"] == mode
            window = subprocess.check_output(
                [
                    "xdotool",
                    "search",
                    "--onlyvisible",
                    "--name",
                    "^Appearance",
                ],
                text=True,
            ).splitlines()[-1]
            subprocess.run(["xdotool", "windowfocus", "--sync", window], check=True)
            if preset in ("macos", "windows"):
                # Show the preset's real editor focus treatment on the common profile.
                subprocess.run(
                    ["xdotool", "mousemove", "--window", window, "340", "200", "click", "1"], check=True
                )
            subprocess.run(["xdotool", "mousemove", "0", "0"], check=True)
            time.sleep(0.2)
            output = ROOT / "docs/screenshots/themes" / f"{preset}-{mode}.png"
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["import", "-window", window, str(output)], check=True, timeout=10)
            from Xlib import X, display
            from Xlib.protocol.event import ClientMessage

            connection = display.Display()
            resource = connection.create_resource_object("window", int(window))
            resource.send_event(
                ClientMessage(
                    window=resource,
                    client_type=connection.intern_atom("WM_PROTOCOLS"),
                    data=(32, [connection.intern_atom("WM_DELETE_WINDOW"), X.CurrentTime, 0, 0, 0]),
                ),
                event_mask=0,
            )
            connection.sync()
            connection.close()
            assert process.wait(timeout=10) == 0, (directory / "native.log").read_text()
            assert json.loads((directory / "closed.json").read_text())["errors"] == []
            print(f"Captured {preset} {mode}: {output.relative_to(ROOT)}", flush=True)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview")
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    if args.preview:
        preview(args.preview, args.mode, args.state_dir)
    else:
        for preset in ("macos", "windows", "shadcn-zinc", "shadcn-blue"):
            for mode in ("light", "dark"):
                capture(preset, mode)
