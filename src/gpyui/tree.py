"""Control-tree ownership shared by application roots and component containers."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING

from .controls import Column, Control

if TYPE_CHECKING:
    from .application import Application


def walk(control: Control) -> Iterator[Control]:
    yield control
    if isinstance(control, Column):
        for child in control.children:
            yield from walk(child)


def set_children(parent: Column | Application, controls: Iterable[Control]) -> None:
    children = tuple(controls)
    app = parent._app if isinstance(parent, Control) else parent
    if isinstance(parent, Control):
        parent._ensure_alive()
        if children and getattr(parent, "container", True) is False:
            raise TypeError(f"{type(parent).__name__} does not accept children")
    if app is not None and app._phase != "new":
        app._check_mutation()
    seen = set()
    for child in children:
        if not isinstance(child, Control):
            raise TypeError("containers accept Control children")
        child._ensure_alive()
        ancestor = parent
        while isinstance(ancestor, Control):
            if ancestor is child:
                raise ValueError("control tree cannot contain a cycle")
            ancestor = ancestor._parent
        if child.id in seen or child._parent not in (None, parent):
            raise ValueError("a control can have only one parent")
        if child._app is not None and child._app is not app:
            raise ValueError("a control can belong to only one application")
        seen.add(child.id)
    if app is not None:
        app._validate_tree_change(parent, children)
    if isinstance(parent, Column):
        parent._validate_children(children)
    previous = tuple(parent._children)
    if previous == children:
        return
    for child in previous:
        if child not in children:
            child._parent = None
    for child in children:
        child._parent = parent
    parent._children = list(children)
    if app is not None and app._phase != "new":
        for child in children:
            app._register(child)
        app._tree_dirty = True
        app._schedule_flush()


def dispose(control: Control) -> None:
    app = control._app
    if app is not None:
        app._check_mutation()
    if control._parent is not None:
        control._parent.remove(control)
    for node in walk(control):
        node.unbind()
        node._handlers.clear()
        node._disposed = True
        node._app = None
        if app is not None:
            app._controls.pop(node.id, None)
            for key in tuple(app._pending):
                if key[0] == node.id:
                    app._pending.pop(key)
    if app is not None:
        app._tree_dirty = True
        app._schedule_flush()
