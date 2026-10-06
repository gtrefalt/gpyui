import asyncio
import json
import threading
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace

import pytest
from image_helpers import png

from gpyui import Application, Image, ImageSource


def test_image_sources_have_explicit_native_meanings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = Image("photo.png")
    assert image.source == ImageSource("file", str(tmp_path / "photo.png"))
    monkeypatch.chdir(tmp_path.parent)
    assert image.source.value == str(tmp_path / "photo.png")
    image.source = Path("photo.png")
    assert image.source is not None
    assert image.source.kind == "file"
    image.source = "https://example.com/photo.png"
    assert image.source is not None
    assert image.source.kind == "url"
    image.source = ImageSource.asset("icons/inbox.svg")
    assert image.source is not None
    assert image.source.kind == "asset"
    image.source = png()
    assert image.source is not None
    assert image.source.value == png()
    with pytest.raises(FrozenInstanceError):
        setattr(image.source, "value", "changed")  # noqa: B010 -- exercise the generated frozen setter
    image.source = None
    assert image.source is None


@pytest.mark.parametrize(
    "source",
    [
        "",
        "bad\0path",
        b"",
        42,
        bytearray(b"PNG"),
        "ftp://example.com/a.png",
        "https://",
        "https://user:secret@example.com/a",
        "http://localhost:99999/a",
    ],
)
def test_invalid_image_sources_fail_before_attachment(source):
    with Application() as app:
        with pytest.raises((ValueError, TypeError)):
            Image(source)
    assert not app.children


def test_source_and_reload_are_batched_without_replacing_the_control():
    image = Image(png())
    calls = []
    image._app = type(  # ty: ignore[invalid-assignment] -- queue test double
        "Mounted", (), {"_check_mutation": lambda _: None, "_queue": lambda _, *args: calls.append(args)}
    )()
    image.source = "photo.png"
    assert [c[1] for c in calls] == ["source", "_revision"]
    assert calls[0][2]["kind"] == "file" and calls[1][2] == 1
    assert not image._accept_image_event(0) and image._accept_image_event(1)
    image.source = "photo.png"
    assert len(calls) == 2
    image.reload()
    assert calls[-1] == (image.id, "_revision", 2)
    with pytest.raises(AttributeError):
        image._revision = 0


def test_image_bridge_validates_both_initial_and_update_sources():
    Bridge = pytest.importorskip("gpyui._core").Bridge
    control = Image(png(), fit="cover").style(width=200, height=100, radius=8)
    spec = control._spec()
    assert spec["props"]["source"]["kind"] == "bytes"
    invalid = [
        {"kind": "bytes", "value": "invalid!"},
        {"kind": "bytes", "value": ""},
        {"kind": "video", "value": "a.mp4"},
        {"kind": "url", "value": "file:///tmp/a.png"},
        {"kind": "url", "value": "https://user:password@example.com/a.png"},
        {"kind": "file", "value": "bad\0path"},
        {"kind": "file", "value": "a", "extra": True},
    ]
    bridge = Bridge(json.dumps([spec]))
    try:
        for source in invalid:
            with pytest.raises(ValueError):
                bridge.submit(json.dumps([{"id": control.id, "property": "source", "value": source}]))
            broken = control._spec()
            broken["props"]["source"] = source
            with pytest.raises(ValueError):
                Bridge(json.dumps([broken]))
        control.source = None
        bridge.submit(json.dumps([{"id": control.id, "property": "source", "value": None}]))
    finally:
        bridge.finish()


@pytest.mark.parametrize("properties", [{"fit": "stretch"}, {"aspect_ratio": -1}, {"grayscale": 1}])
def test_image_layout_properties_are_validated(properties):
    with pytest.raises((ValueError, TypeError)):
        Image(**properties)


@pytest.mark.parametrize("hidden", [False, True])
def test_async_image_events_drop_old_revisions_and_hidden_controls(hidden):
    async def scenario():
        received = []

        async def loaded(event):
            received.append((event.name, event.value))

        with Application() as app:
            image = Image(png(), on_load=loaded, on_error=loaded)
        app._controls[image.id] = image
        image.reload()
        image._app = app
        image._visible = not hidden
        events = [
            {"event": "load", "id": image.id, "revision": 0, "value": "stale"},
            {"event": "error", "id": image.id, "revision": 1, "value": "missing"},
            {
                "event": "load",
                "id": image.id,
                "revision": 1,
                "value": {"width": 200, "height": 100, "frames": 1},
            },
            {"event": "closed"},
        ]
        app._bridge = SimpleNamespace(next_events=lambda: json.dumps(events))
        await app._events(threading.Event())
        expected = [("error", "missing"), ("load", {"width": 200, "height": 100, "frames": 1})]
        assert received == ([] if hidden else expected)

    asyncio.run(scenario())
