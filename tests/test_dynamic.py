"""Structural updates must preserve ownership, batching and explicit lifetime."""

import asyncio
import json
import threading

import pytest

from gpyui import Application, Button, Checkbox, Column, Dialog, Label, Row, State, TextInput


class RecordingBridge:
    def __init__(self):
        self.calls = []

    def submit(self, patches):
        self.calls.append(("submit", json.loads(patches)))

    def reconcile(self, tree, roots, patches):
        self.calls.append(("reconcile", json.loads(tree), json.loads(roots), json.loads(patches)))


def mounted(app):
    app._phase = "running"
    app._worker_ident = threading.get_ident()
    app._loop = asyncio.get_running_loop()
    app._bridge = RecordingBridge()
    for root in app.children:
        app._register(root)
    return app._bridge


def test_reorder_and_replace_validate_before_changing_ownership():
    first, second = Label("First"), Label("Second")
    column = Column([first, second])
    column.children = [second, first]
    assert column.children == (second, first)
    with pytest.raises(ValueError, match="one parent"):
        column.set_children([first, first])
    assert column.children == (second, first)
    column.set_children([first])
    assert second._parent is None
    column.insert(0, second)
    assert column.children == (second, first)
    with pytest.raises(ValueError, match="cycle"):
        column.add(column)
    leaf = Checkbox()
    with pytest.raises(TypeError, match="does not accept children"):
        leaf.set_children([Label()])


def test_detach_move_and_reattach_keep_bindings_and_use_one_structural_batch():
    async def scenario():
        value = State("Ada")
        field = TextInput().bind_value(value)
        left, right = Column([field]), Row()
        app = Application(left, right)
        bridge = mounted(app)
        original_id = field.id
        with app.batch():
            left.remove(field)
            assert field._app is app and field._parent is None
            value.value = "Grace"
            right.add(field)
            new = Label("Added at runtime")
            left.add(new)
        assert field.id == original_id and field.value == "Grace"
        assert field._parent is right and new._app is app
        assert len(bridge.calls) == 1 and bridge.calls[0][0] == "reconcile"
        assert bridge.calls[0][2] == [left.id, right.id]
        with app.batch():
            right.clear()
        forests = bridge.calls[-1][1]
        assert field.id in [root["id"] for root in forests]  # Retained detached root.
        assert field._is_displayed() is False
        with app.batch():
            left.add(field)
        assert field._is_displayed() is True
        field.unbind()

    asyncio.run(scenario())


def test_visibility_is_independent_of_bindings_and_ancestor_visibility():
    async def scenario():
        value = State("Ada")
        field = TextInput().bind_value(value)
        parent = Column([field])
        app = Application(parent)
        bridge = mounted(app)
        with app.batch():
            parent.visible = False
            value.value = "Grace"
        assert not field._is_displayed()
        assert field.visible is True and field.value == "Grace"
        assert bridge.calls[0][0] == "submit"
        with app.batch():
            parent.visible = True
        assert field._is_displayed()
        with pytest.raises(TypeError, match="visible requires bool"):
            field.visible = "hidden"  # ty: ignore[invalid-assignment] -- runtime validation
        field.unbind()

    asyncio.run(scenario())


def test_dispose_releases_entire_subtree_and_cannot_be_reused():
    async def scenario():
        state = State("Ada")
        field = TextInput().bind_value(state)
        panel = Column([field, Button("Run", on_click=lambda: None)])
        app = Application(panel)
        bridge = mounted(app)
        with app.batch():
            field.value = "Pending"
            panel.dispose()
        assert app.children == () and app._controls == {}
        assert bridge.calls[0] == ("reconcile", [], [], [])
        assert panel.disposed and field.disposed
        assert field._bindings == [] and panel.children[1]._handlers == {}
        state.value = "After disposal"
        assert field.value == "Pending"
        panel.dispose()  # Idempotent.
        with pytest.raises(RuntimeError, match="disposed"):
            field.value = "Invalid"
        with pytest.raises(RuntimeError, match="disposed"):
            app.add(panel)
        with pytest.raises(RuntimeError, match="disposed"):
            field.visible = True

    asyncio.run(scenario())


def test_runtime_mutation_rejects_other_threads_and_foreign_applications():
    async def scenario():
        field = TextInput()
        parent = Column([field])
        app = Application(parent)
        mounted(app)
        with pytest.raises(RuntimeError, match="callback loop"):
            await asyncio.to_thread(parent.clear)
        assert parent.children == (field,)
        with app.batch():
            parent.remove(field)
        with pytest.raises(ValueError, match="one application"):
            Application().add(field)

    asyncio.run(scenario())


def test_active_overlay_limits_allow_detached_retained_dialog():
    async def scenario():
        first = Dialog("First")
        app = Application(first)
        mounted(app)
        with pytest.raises(ValueError, match="one dialog"):
            app.add(Dialog("Second"))
        assert app.children == (first,)
        with app.batch():
            app.remove(first)
            second = Dialog("Second")
            app.add(second)
        assert first._parent is None and first._app is app
        assert app.children == (second,)

    asyncio.run(scenario())


def test_runtime_context_can_wrap_a_retained_detached_control():
    async def scenario():
        field = TextInput("Keep native state")
        app = Application(field)
        bridge = mounted(app)
        with app.batch():
            app.remove(field)
            with app:
                parent = Row([field])
        assert app.children == (parent,) and parent.children == (field,)
        assert field._app is app
        assert len(bridge.calls) == 1

    asyncio.run(scenario())


def test_detached_tree_depth_is_validated_before_mutation():
    async def scenario():
        detached = Column()
        app = Application(detached)
        mounted(app)
        with app.batch():
            app.remove(detached)
        deep = Label()
        for _ in range(65):
            deep = Column([deep])
        with pytest.raises(ValueError, match="64 levels"):
            detached.add(deep)
        assert detached.children == () and deep._parent is None

    asyncio.run(scenario())
