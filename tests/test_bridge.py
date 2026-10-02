import json
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from gpyui import Application, Label
from gpyui._core import GPUI_KIT_REVISION, GPUI_VERSION, Bridge


def test_dependency_identity():
    assert GPUI_VERSION == "0.3.7"
    assert GPUI_KIT_REVISION == "3a142844d3661159964dce9e5512ca9a40286160"


@pytest.mark.parametrize(
    "tree",
    [
        [{"id": 0, "type": "label", "text": "invalid"}],
        [{"id": 1, "type": "column", "children": [{"id": 1, "type": "label", "text": "duplicate"}]}],
        [{"id": 1, "type": "imaginary"}],
        [{"id": 1, "type": "label", "text": 5}],
    ],
)
def test_native_tree_validation(tree):
    with pytest.raises(ValueError):
        Bridge(json.dumps(tree))


def test_whole_batch_validated_before_enqueue():
    bridge = Bridge('[{"id":1,"type":"label","text":"original"}]')
    with pytest.raises(ValueError, match="unknown control"):
        bridge.submit(
            '[{"id":1,"property":"text","value":"valid"},{"id":2,"property":"text","value":"invalid"}]'
        )
    with pytest.raises(ValueError, match="invalid property"):
        bridge.submit('[{"id":1,"property":"text","value":false}]')
    bridge.submit('[{"id":1,"property":"text","value":"valid"}]')
    bridge.finish()
    with pytest.raises(RuntimeError, match="queue unavailable"):
        bridge.submit('[{"id":1,"property":"text","value":"closed"}]')


def test_blocked_event_reader_releases_gil_and_wakes_on_finish():
    bridge = Bridge("[]")
    with ThreadPoolExecutor(max_workers=1) as pool:
        reader = pool.submit(bridge.next_events)
        bridge.finish()
        assert json.loads(reader.result(timeout=2)) == [{"event": "closed"}]


def test_command_overload_is_explicit():
    bridge = Bridge("[]")
    try:
        for token in range(1024):
            bridge.snapshot(token)
        with pytest.raises(RuntimeError, match="queue unavailable"):
            bridge.snapshot(1024)
    finally:
        bridge.finish()


@pytest.mark.skipif(sys.platform != "linux", reason="X11/Wayland display validation is Linux-specific")
def test_missing_display_cleans_up_python_worker(monkeypatch):
    import threading

    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    app = Application(Label("No display"))
    with pytest.raises(RuntimeError, match="requires an X11 or Wayland display"):
        app.run()
    assert not any(t.name == "gpyui-asyncio" or t.name.startswith("asyncio_") for t in threading.enumerate())
    with pytest.raises(RuntimeError, match="only be called once"):
        app.run()
