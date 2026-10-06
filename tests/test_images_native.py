import functools
import http.server
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from image_helpers import animated_gif, png
from test_native import ARTIFACTS, close_window, wait_file, xdo

pytestmark = [
    pytest.mark.native,
    pytest.mark.skipif(os.environ.get("GPYUI_NATIVE_TESTS") != "1", reason="requires a native display"),
]


def test_native_image_sources_retry_animation_and_lifecycle(tmp_path):
    (tmp_path / "sample.png").write_bytes(png())
    (tmp_path / "image.png").write_bytes(png((20, 90, 220)))
    (tmp_path / "animated.gif").write_bytes(animated_gif())
    entered = threading.Event()
    release = threading.Event()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/slow.png":
                entered.set()
                release.wait(5)
                self.path = "/image.png"
            super().do_GET()

        def log_message(self, format, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=tmp_path))
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    ARTIFACTS.mkdir(exist_ok=True)
    with (ARTIFACTS / "images.log").open("w") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(__file__).with_name("native_images.py")),
                str(tmp_path),
                f"http://127.0.0.1:{server.server_port}",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        sequence = 0

        def command(action="snapshot", **properties):
            nonlocal sequence
            sequence += 1
            name = f"result-{sequence}"
            temporary = tmp_path / "command.tmp"
            temporary.write_text(json.dumps({"action": action, "name": name, **properties}))
            temporary.replace(tmp_path / "command.json")
            return wait_file(tmp_path / f"{name}.json", process)

        def until(predicate, timeout=10):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                state = command()
                if predicate(state):
                    return state
                time.sleep(0.04)
            pytest.fail(f"image state did not converge: {state}")

        def status(expected, count=None):
            return until(
                lambda s: (
                    s["nodes"][image_id]["image"]["status"] == expected
                    and (count is None or len(s["events"]) >= count)
                )
            )

        def pixel(x=160, y=125):
            output = ARTIFACTS / "image-pixel.png"
            subprocess.run(["import", "-window", window, str(output)], check=True, timeout=10)
            return subprocess.check_output(
                ["convert", str(output), "-crop", f"1x1+{x}+{y}", "-depth", "8", "rgb:-"]
            )

        try:
            ready = wait_file(tmp_path / "ready.json", process)
            image_id, editor_id = str(ready["image"]), str(ready["editor"])
            window = xdo("search", "--onlyvisible", "--name", "^gpyui image test$").splitlines()[-1]
            xdo("windowfocus", "--sync", window)
            state = status("loaded", 1)
            assert state["nodes"][image_id]["image"] == {
                "status": "loaded",
                "width": 200,
                "height": 100,
                "frames": 1,
            }
            assert state["events"][0]["thread"] == "gpyui-asyncio"
            xdo("mousemove", "--window", window, 70, 32, "click", 1)
            xdo("key", "End")
            xdo("type", "--clearmodifiers", " X")
            until(lambda s: s["nodes"][editor_id]["value"] == "Keep editing X")
            if shutil.which("import") and shutil.which("convert"):
                time.sleep(0.15)
                assert pixel()[0] > 180 and pixel()[1] < 80
            for fit in ["cover", "fill", "scale_down", "none", "contain"]:
                command("fit", fit=fit)
                if shutil.which("import") and shutil.which("convert"):
                    time.sleep(0.08)
                    sample = (
                        pixel(160, 76)
                        if fit in {"cover", "fill"}
                        else pixel(290 if fit == "none" else 55, 125)
                    )
                    if fit in {"cover", "fill", "contain"}:
                        assert sample[0] > 180 and sample[1] < 80, fit
                    else:
                        assert sample[1] > 100, fit  # Intrinsic-size image leaves a side margin.
            command("bytes")
            status("loaded", 2)
            if shutil.which("import") and shutil.which("convert"):
                time.sleep(0.1)
                assert pixel()[2] > 180 and pixel()[0] < 80
                command("fit", fit="cover", grayscale=True)
                time.sleep(0.15)
                gray = pixel()
                assert max(gray) - min(gray) <= 2
                command("fit", fit="contain")
            command("invalid")
            failed = status("error", 3)
            assert failed["events"][-1]["name"] == "error"
            # Fix an unchanged path, then activate the actual native Retry button.
            command("file", file="retry.png")
            status("error", 4)
            (tmp_path / "retry.png").write_bytes(png())
            xdo("mousemove", "--window", window, 75, 267, "click", 1)
            status("loaded", 5)
            for action, kwargs in [
                ("asset", {}),
                ("url", {}),
                ("gif", {}),
                ("file", {"file": "animated.gif"}),
            ]:
                before = len(command()["events"])
                command(action, **kwargs)
                state = status("loaded", before + 1)
                assert state["events"][-1]["name"] == "load"
                if action == "gif" or kwargs.get("file") == "animated.gif":
                    assert state["nodes"][image_id]["image"]["frames"] == 2
            if shutil.which("import") and shutil.which("convert"):
                observed = set()
                deadline = time.monotonic() + 3
                while len(observed) < 2 and time.monotonic() < deadline:
                    observed.add(pixel())
                    time.sleep(0.12)
                assert len(observed) == 2, "native GIF did not advance frames"
            # Source replacement while a request is pending discards its callback.
            count = len(command()["events"])
            command("url", path="/slow.png")
            assert entered.wait(5)
            command("bytes")
            status("loaded", count + 1)
            release.set()
            time.sleep(0.3)
            assert len(command()["events"]) == count + 1
            command("hide")
            assert not command()["nodes"][image_id]["displayed"]
            command("show")
            command("move")
            assert command()["nodes"][image_id]["displayed"]
            # Native editor selection/caret/undo survives all image changes.
            xdo("mousemove", "--window", window, 70, 32, "click", 1)
            xdo("key", "ctrl+z")
            until(lambda s: s["nodes"][editor_id]["value"] == "Keep editing")
            command("empty")
            status("empty")
            count = len(command()["events"])
            command("bytes")
            status("loaded", count + 1)
            command("dispose")
            assert image_id not in command()["nodes"]
            # Dispose a separate control while its network request is pending.
            release.clear()
            entered.clear()
            count = len(command()["events"])
            command("add_pending")
            assert entered.wait(5)
            command("dispose_pending")
            release.set()
            time.sleep(0.2)
            assert len(command()["events"]) == count
            close_window(window)
            assert process.wait(timeout=10) == 0
            closed = wait_file(tmp_path / "closed.json", process)
            assert closed["errors"] == [] and "gpyui-asyncio" not in closed["threads"]
        finally:
            release.set()
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
