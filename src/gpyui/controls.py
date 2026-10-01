from __future__ import annotations

import inspect
import itertools
from collections.abc import Callable, Iterable
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .state import State

if TYPE_CHECKING:
    from .application import Application

_ids = itertools.count(1)
_containers: ContextVar[tuple[Any, ...]] = ContextVar("gpyui_containers", default=())


@dataclass(frozen=True)
class Event:
    """An activation or native value change, delivered on the Python asyncio loop."""

    sender: Control | Application
    name: str
    value: str | None = None


class Handler:
    def __init__(self, callback: Callable[..., Any]):
        if not callable(callback):
            raise TypeError("event handler must be callable")
        signature = inspect.signature(callback)
        try:
            signature.bind()
            self.arguments = False
        except TypeError:
            signature.bind(None)  # Validate exactly one event can be passed.
            self.arguments = True
        self.callback = callback

    def __call__(self, event: Event) -> Any:
        return self.callback(event) if self.arguments else self.callback()


class Control:
    """Stable Python handle; native rendering and interaction live in Rust."""

    def __init__(self, control_type: str, **properties: Any):
        self._id = next(_ids)
        self._type = control_type
        self._properties = properties
        self._parent: Column | Application | None = None
        self._app: Application | None = None
        self._bindings: list[Callable[[], None]] = []
        self._handlers: dict[str, Handler] = {}
        if stack := _containers.get():
            stack[-1].add(self)

    @property
    def id(self) -> int:
        return self._id

    def _set(self, name: str, value: Any) -> None:
        if self._app:
            self._app._check_mutation()
        if self._properties[name] == value:
            return
        self._properties[name] = value
        if self._app:
            self._app._queue(self.id, name, value)

    def _spec(self) -> dict[str, Any]:
        return {"id": self.id, "type": self._type, **self._properties}

    def update(self) -> None:
        """Flush pending application properties to the native queue."""
        if self._app:
            self._app.update()

    def unbind(self) -> None:
        """Remove this control's explicit state subscriptions."""
        for unsubscribe in self._bindings:
            unsubscribe()
        self._bindings.clear()


class Column(Control):
    """Vertical layout, composed with children or a context manager."""

    def __init__(self, children: Iterable[Control] = ()):
        self._children: list[Control] = []
        super().__init__("column")
        self.add(*children)

    @property
    def children(self) -> tuple[Control, ...]:
        return tuple(self._children)

    def add(self, *controls: Control) -> Column:
        if self._app:
            raise RuntimeError("the mounted tree is fixed for this milestone")
        for control in controls:
            if not isinstance(control, Control):
                raise TypeError("columns accept Control children")
            parent: Column | Application | None = self
            while isinstance(parent, Column):
                if parent is control:
                    raise ValueError("control tree cannot contain a cycle")
                parent = parent._parent
            if control._parent is not None or control._app is not None:
                raise ValueError("a control can have only one parent")
            control._parent = self
            self._children.append(control)
        return self

    def __enter__(self) -> Column:
        _containers.set((*_containers.get(), self))
        return self

    def __exit__(self, *_: Any) -> None:
        stack = _containers.get()
        if not stack or stack[-1] is not self:
            raise RuntimeError("unbalanced column context")
        _containers.set(stack[:-1])

    def _spec(self) -> dict[str, Any]:
        return {**super()._spec(), "children": [c._spec() for c in self.children]}


def _text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("text properties require str")
    return value


class Label(Control):
    def __init__(self, text: str = ""):
        super().__init__("label", text=_text(text))

    @property
    def text(self) -> str:
        return self._properties["text"]

    @text.setter
    def text(self, value: str) -> None:
        self._set("text", _text(value))

    def bind_text(self, state: State[Any], transform: Callable[[Any], str] = str) -> Label:
        self.text = transform(state.value)
        self._bindings.append(state.subscribe(lambda value: setattr(self, "text", transform(value))))
        return self


class TextInput(Control):
    """Rust owns editing, caret, selection and history; value is a Python mirror.

    Assigning value replaces native text and clears undo history without firing
    on_change. Native edits update this mirror before dispatching on_change.
    """

    def __init__(
        self, value: str = "", *, placeholder: str = "", on_change: Callable[..., Any] | None = None
    ):
        handler = Handler(on_change) if on_change is not None else None
        super().__init__("input", value=_text(value), placeholder=_text(placeholder))
        self._state: State[str] | None = None
        if handler is not None:
            self._handlers["change"] = handler

    @property
    def value(self) -> str:
        return self._properties["value"]

    @value.setter
    def value(self, value: str) -> None:
        self._set("value", _text(value))
        if self._state:
            self._state.value = value

    @property
    def placeholder(self) -> str:
        return self._properties["placeholder"]

    @placeholder.setter
    def placeholder(self, value: str) -> None:
        self._set("placeholder", _text(value))

    def bind_value(self, state: State[str]) -> TextInput:
        self.unbind()
        self._state = state
        self.value = state.value
        self._bindings.append(state.subscribe(lambda value: setattr(self, "value", value)))
        return self

    def unbind(self) -> None:
        super().unbind()
        self._state = None

    def _receive_native(self, value: str) -> None:
        # Never echo a user edit through set_value: it would reset caret/undo.
        self._properties["value"] = value
        if self._state:
            self._state.value = value


class Button(Control):
    def __init__(self, text: str, *, on_click: Callable[..., Any] | None = None, disabled: bool = False):
        if not isinstance(disabled, bool):
            raise TypeError("disabled requires bool")
        handler = Handler(on_click) if on_click is not None else None
        super().__init__("button", text=_text(text), disabled=disabled)
        if handler is not None:
            self._handlers["click"] = handler

    @property
    def text(self) -> str:
        return self._properties["text"]

    @text.setter
    def text(self, value: str) -> None:
        self._set("text", _text(value))

    @property
    def disabled(self) -> bool:
        return self._properties["disabled"]

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("disabled requires bool")
        self._set("disabled", value)
