"""Record the real native streaming example with X11, xdotool and FFmpeg.

Run with `uv run python scripts/record-workspace.py`. A free Xvfb display is
started when DISPLAY is unset. Requires the development dependencies, Xvfb,
xdotool, FFmpeg and a working Vulkan driver. Nothing is rendered in Python.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def observe(path: Path, process: subprocess.Popen, predicate=lambda _: True, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Native app exited early ({process.returncode}); see artifacts/recording/app.log"
            )
        if path.exists():
            state = json.loads(path.read_text())
            if predicate(state):
                return state
        time.sleep(0.03)
    raise TimeoutError(f"Timed out waiting for {path}")


def xdo(*args):
    return subprocess.check_output(["xdotool", *map(str, args)], text=True, timeout=10).strip()


def close_window(window):
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


def record(theme: str, output: Path) -> None:
    directory = ROOT / "artifacts" / "recording"
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("ready.json", "state.json", "closed.json", "error.json", "display"):
        (directory / name).unlink(missing_ok=True)
    runtime = directory / "runtime"
    runtime.mkdir(exist_ok=True, mode=0o700)
    os.environ.setdefault("XDG_RUNTIME_DIR", str(runtime))
    sysroot = Path(os.environ.get("GPYUI_SYSROOT", "/workspace/native/sysroot"))
    manifest = sysroot / "usr/share/vulkan/icd.d/lvp_icd.json"
    if manifest.exists() and "VK_DRIVER_FILES" not in os.environ:
        driver = json.loads(manifest.read_text())
        driver["ICD"]["library_path"] = str(sysroot / "usr/lib/x86_64-linux-gnu/libvulkan_lvp.so")
        (directory / "driver.json").write_text(json.dumps(driver))
        os.environ["VK_DRIVER_FILES"] = str(directory / "driver.json")

    xvfb = app = video = None
    try:
        if not os.environ.get("DISPLAY"):
            with (directory / "display").open("w") as display_fd, (directory / "xvfb.log").open("w") as log:
                xvfb = subprocess.Popen(
                    [
                        "Xvfb",
                        "-displayfd",
                        str(display_fd.fileno()),
                        "-screen",
                        "0",
                        "1600x1100x24",
                        "-nolisten",
                        "tcp",
                    ],
                    pass_fds=(display_fd.fileno(),),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            deadline = time.monotonic() + 10
            while not (number := (directory / "display").read_text().strip()).isdigit():
                if xvfb.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Xvfb did not start; see artifacts/recording/xvfb.log")
                time.sleep(0.05)
            os.environ["DISPLAY"] = f":{number}"
        with (directory / "app.log").open("w") as log:
            app = subprocess.Popen(
                [sys.executable, str(ROOT / "tests/native_catalog.py"), str(directory), "stream", theme],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        initial = observe(directory / "ready.json", app)
        window = xdo("search", "--onlyvisible", "--name", "Paper trading").splitlines()[-1]
        xdo("windowmove", window, 0, 0)
        xdo("windowfocus", "--sync", window)
        xdo("mousemove", "--window", window, 1160, 760)
        geometry = dict(
            line.split("=", 1) for line in xdo("getwindowgeometry", "--shell", window).splitlines()
        )
        time.sleep(0.25)
        movie = directory / "workspace.mkv"
        with (directory / "ffmpeg.log").open("w") as log:
            video = subprocess.Popen(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "warning",
                    "-f",
                    "x11grab",
                    "-framerate",
                    "10",
                    "-video_size",
                    f"{geometry['WIDTH']}x{geometry['HEIGHT']}",
                    "-i",
                    f"{os.environ['DISPLAY']}+{geometry['X']},{geometry['Y']}",
                    "-t",
                    "12",
                    "-c:v",
                    "ffv1",
                    "-threads",
                    "2",
                    str(movie),
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        start = time.monotonic()
        for at, action in [(1.8, "buy"), (5.4, "sell"), (8.4, "symbol")]:
            time.sleep(max(0, start + at - time.monotonic()))
            if action == "symbol":
                xdo("mousemove", "--window", window, 80, 248, "click", 1)
            else:
                if action == "sell":
                    xdo("mousemove", "--window", window, 978, 252, "click", 1)
                    xdo("mousemove", "--window", window, 1030, 320, "click", 1)
                    xdo("key", "ctrl+a")
                    xdo("type", "--clearmodifiers", "5")
                xdo("mousemove", "--window", window, 1030, 470, "click", 1)
            xdo("mousemove", "--window", window, 1160, 760)
        if video.wait(timeout=20) != 0:
            raise RuntimeError("Capture failed; see artifacts/recording/ffmpeg.log")
        final = observe(
            directory / "state.json",
            app,
            lambda s: any(
                n.get("columns") == ["Symbol", "Side", "Quantity", "Price"] and len(n["rows"]) == 4
                for n in s.values()
            ),
        )
        orders = next(
            n["rows"] for n in final.values() if n.get("columns") == ["Symbol", "Side", "Quantity", "Price"]
        )
        assert [row[:3] for row in orders[-2:]] == [["NVDA", "Buy", "10"], ["NVDA", "Sell", "5"]]
        assert any(n.get("type") == "select" and n.get("value") == "AAPL" for n in final.values())
        initial_chart = next(n["data"] for n in initial.values() if n["type"] == "line_chart")
        assert next(n["data"] for n in final.values() if n["type"] == "line_chart") != initial_chart
        close_window(window)
        if app.wait(timeout=10) != 0:
            raise RuntimeError("Native app did not shut down cleanly")
        closed = json.loads((directory / "closed.json").read_text())
        assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"]
        assert not (directory / "error.json").exists()
        (directory / "verified.json").write_text(json.dumps({"orders": orders, "closed": closed}, indent=2))
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "warning",
                "-threads",
                "2",
                "-i",
                str(movie),
                "-filter_complex",
                "[0:v]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
                "-filter_complex_threads",
                "1",
                "-loop",
                "0",
                str(output),
            ],
            check=True,
        )
        print(f"Recorded and verified native simulation: {output} ({output.stat().st_size:,} bytes)")
    finally:
        for process in (video, app, xvfb):
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("light", "dark"), default="dark")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/screenshots/workspace-stream.gif")
    args = parser.parse_args()
    record(args.theme, args.output.resolve())
