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
    "alteration",
    [
        {"unknown": True},
        {"radius": 65},
        {"font_size": 0},
        {"shadow": "false"},
        {"font_family": " "},
        {"mode": "system"},
        {"colors": {"not_a_color": "#ffffff"}},
        {"colors": {"background": "#abc"}},
        {"colors": {"background": "red"}},
        {"colors": {"background": "#zzzzzz"}},
        {"colors": {"control_background": "#bad"}},
        {"colors": {"switch_checked": "green"}},
    ],
)
def test_native_theme_validation_before_enqueue_or_start(alteration):
    from gpyui import Theme

    bridge = Bridge("[]")
    invalid = json.dumps(Theme("macos")._spec() | alteration)
    try:
        with pytest.raises(ValueError):
            bridge.set_theme(invalid)
        with pytest.raises(ValueError):
            bridge.run("Invalid theme", 600, 400, "light", invalid)
        # Invalid changes consumed no queue slots and did not claim native startup.
        bridge.set_theme(json.dumps(Theme("windows", mode="dark")._spec()))
        for token in range(1023):
            bridge.theme_snapshot(token)
        with pytest.raises(RuntimeError, match="queue unavailable"):
            bridge.theme_snapshot(1024)
    finally:
        bridge.finish()


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


def test_reconciliation_validates_new_controls_before_changing_schema():
    bridge = Bridge('[{"id":1,"type":"column","children":[]}]')
    tree = '[{"id":1,"type":"column","children":[{"id":2,"type":"input","value":"Ada","placeholder":""}]}]'
    with pytest.raises(ValueError, match="invalid property"):
        bridge.reconcile(tree, "[1]", '[{"id":2,"property":"visible","value":"invalid"}]')
    with pytest.raises(ValueError, match="unknown control"):
        bridge.submit('[{"id":2,"property":"value","value":"Not mounted"}]')
    bridge.reconcile(tree, "[1]", '[{"id":2,"property":"visible","value":false}]')
    bridge.submit('[{"id":2,"property":"value","value":"Grace"}]')
    bridge.finish()


@pytest.mark.parametrize(
    "invalid_tree, roots, message",
    [
        ('[{"id":1,"type":"label","text":"Changed type"}]', "[1]", "changed type"),
        ('[{"id":1,"type":"column","children":[]}]', "[2]", "unparented"),
        ('[{"id":1,"type":"column","children":[]}]', "[1,1]", "unique"),
        (
            '[{"id":1,"type":"column","children":[{"id":1,"type":"label","text":"Duplicate"}]}]',
            "[1]",
            "unique",
        ),
    ],
)
def test_reconciliation_rejects_identity_and_topology_errors(invalid_tree, roots, message):
    bridge = Bridge('[{"id":1,"type":"column","children":[]}]')
    with pytest.raises(ValueError, match=message):
        bridge.reconcile(invalid_tree, roots, "[]")
    bridge.submit('[{"id":1,"property":"visible","value":false}]')
    bridge.finish()


def test_disposed_ids_are_rejected_but_detached_controls_remain_registered():
    tree = '[{"id":1,"type":"column","children":[]},{"id":2,"type":"input","value":"Ada","placeholder":""}]'
    bridge = Bridge(tree)
    bridge.reconcile(tree, "[1]", "[]")
    bridge.submit('[{"id":2,"property":"value","value":"Detached update"}]')
    bridge.reconcile('[{"id":1,"type":"column","children":[]}]', "[1]", "[]")
    with pytest.raises(ValueError, match="disposed"):
        bridge.reconcile(tree, "[1,2]", "[]")
    bridge.finish()


def test_failed_enqueue_does_not_commit_future_tree_schema():
    bridge = Bridge('[{"id":1,"type":"column","children":[]}]')
    try:
        for token in range(1024):
            bridge.snapshot(token)
        with pytest.raises(RuntimeError, match="queue unavailable"):
            bridge.reconcile('[{"id":2,"type":"label","text":"New"}]', "[2]", "[]")
        with pytest.raises(ValueError, match="unknown control"):
            bridge.submit('[{"id":2,"property":"text","value":"New schema was not committed"}]')
    finally:
        bridge.finish()


def test_command_schema_validates_references_and_readonly_fields():
    from gpyui import Button, Command, Menu
    from gpyui.commands import menu_specs

    command = Command("Save", lambda: None, shortcut="mod+s")
    tree = json.dumps([Button(command=command)._spec()])
    config = json.dumps({"commands": [command._spec()], "menus": menu_specs([Menu("File", [command])])})
    bridge = Bridge(tree, config)
    bridge.submit(
        json.dumps(
            [
                {"id": command.id, "property": "enabled", "value": False},
                {"id": command.id, "property": "checked", "value": True},
            ]
        )
    )
    for property in ["label", "shortcut", "visible", "style"]:
        with pytest.raises(ValueError, match="invalid property"):
            bridge.submit(json.dumps([{"id": command.id, "property": property, "value": True}]))
    invalid = command._spec() | {"shortcut": "bogus-s"}
    with pytest.raises(ValueError, match="invalid command shortcut"):
        Bridge("[]", json.dumps({"commands": [invalid]}))
    with pytest.raises(ValueError, match="unknown command"):
        Bridge(tree)
    bridge.finish()


def test_command_config_queue_overload_is_atomic():
    from gpyui import Command

    first = Command("First", lambda: None)
    second = Command("Second", lambda: None)
    bridge = Bridge("[]", json.dumps({"commands": [first._spec()]}))
    for token in range(1024):
        bridge.snapshot(token)
    with pytest.raises(RuntimeError, match="queue unavailable"):
        bridge.reconcile("[]", "[]", "[]", json.dumps({"commands": [first._spec(), second._spec()]}))
    with pytest.raises(ValueError, match="unknown control"):
        bridge.submit(json.dumps([{"id": second.id, "property": "enabled", "value": False}]))
    bridge.finish()


def test_invalid_menu_and_command_identity_do_not_commit_schema():
    from gpyui import Command

    command = Command("Save", lambda: None, shortcut="mod+s")
    bridge = Bridge("[]", json.dumps({"commands": [command._spec()]}))
    invalid = command._spec() | {"label": "Changed identity"}
    with pytest.raises(ValueError, match="constructor-only"):
        bridge.reconcile("[]", "[]", "[]", json.dumps({"commands": [invalid]}))
    with pytest.raises(ValueError, match="unknown command"):
        bridge.reconcile(
            "[]",
            "[]",
            "[]",
            json.dumps(
                {
                    "commands": [command._spec()],
                    "menus": [
                        {"type": "menu", "label": "File", "items": [{"type": "command", "id": 999999}]}
                    ],
                }
            ),
        )
    bridge.submit(json.dumps([{"id": command.id, "property": "enabled", "value": False}]))
    bridge.finish()
