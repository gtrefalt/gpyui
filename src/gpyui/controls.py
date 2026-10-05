from __future__ import annotations

import inspect
import itertools
from collections.abc import Callable, Iterable
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from .state import State

if TYPE_CHECKING:
    from .application import Application
    from .commands import Command, Menu, MenuSeparator

_ids = itertools.count(1)
_containers: ContextVar[tuple[Any, ...]] = ContextVar("gpyui_containers", default=())


@dataclass(frozen=True)
class Event:
    """An activation or native value change, delivered on the Python asyncio loop."""

    sender: Control | Application | Command
    name: str
    value: Any = None


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
        self._style: dict[str, Any] = {}
        self._context_items: tuple[Command | Menu | MenuSeparator, ...] | None = None
        self._context_native = False
        self._visible = True
        self._disposed = False
        if stack := _containers.get():
            stack[-1].add(self)

    @property
    def id(self) -> int:
        return self._id

    def _set(self, name: str, value: Any) -> None:
        self._ensure_alive()
        if self._app:
            self._app._check_mutation()
        if self._properties[name] == value:
            return
        self._properties[name] = value
        if self._app:
            self._app._queue(self.id, name, value)

    def _spec(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self._type,
            **self._properties,
            "style": self._style,
            "visible": self.visible,
            "context_menu": self._context_spec(),
        }

    def _context_spec(self) -> dict[str, Any] | None:
        from .commands import menu_specs

        return (
            None
            if self._context_items is None
            else {"items": menu_specs(self._context_items), "native": self._context_native}
        )

    def context_menu(
        self, items: Iterable[Command | Menu | MenuSeparator] | None, *, native: bool = False
    ) -> Self:
        """Attach a Kit right-click menu; None removes it. Native popups are opt-in."""
        from .commands import menu_commands, validate_items

        self._ensure_alive()
        if not isinstance(native, bool):
            raise TypeError("native requires bool")
        value = None if items is None else validate_items(items)
        if self._app is not None:
            self._app._check_mutation()
            self._app._register_commands(menu_commands(value or ()))
        self._context_items, self._context_native = value, native
        if self._app is not None:
            self._app._queue(self.id, "context_menu", self._context_spec())
        return self

    def _ensure_alive(self) -> None:
        if self._disposed:
            raise RuntimeError("control has been disposed")

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._ensure_alive()
        if not isinstance(value, bool):
            raise TypeError("visible requires bool")
        if self._app:
            self._app._check_mutation()
        if self._visible != value:
            self._visible = value
            if self._app:
                self._app._queue(self.id, "visible", value)

    def _is_displayed(self) -> bool:
        node: Control | Application | None = self
        while isinstance(node, Control):
            if not node.visible or node.disposed:
                return False
            node = node._parent
        return self._app is not None and node is self._app

    def dispose(self) -> None:
        """Detach and permanently release this subtree and its bindings."""
        if self.disposed:
            return
        from .tree import dispose

        dispose(self)

    def style(self, **properties: Any) -> Self:
        """Set pixel layout and semantic theme styles; return this control."""
        from .widgets import validate_style

        self._ensure_alive()
        value = validate_style({**self._style, **properties})
        if self._app:
            self._app._check_mutation()
        self._style = value
        if self._app:
            self._app._queue(self.id, "style", value)
        return self

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

    @children.setter
    def children(self, controls: Iterable[Control]) -> None:
        self.set_children(controls)

    def set_children(self, controls: Iterable[Control]) -> Self:
        """Replace/reorder children, retaining existing native control identities."""
        from .tree import set_children

        set_children(self, controls)
        return self

    def add(self, *controls: Control) -> Self:
        self.set_children((*self._children, *controls))
        return self

    def insert(self, index: int, control: Control) -> Self:
        children = list(self.children)
        children.insert(index, control)
        self.set_children(children)
        return self

    def remove(self, *controls: Control) -> Self:
        if any(control not in self._children for control in controls):
            raise ValueError("control is not a child of this container")
        self.set_children(control for control in self._children if control not in controls)
        return self

    def clear(self) -> Self:
        self.set_children(())
        return self

    def __enter__(self) -> Self:
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

    def bind_text(self, state: State[Any], transform: Callable[[Any], str] = str) -> Self:
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

    def bind_value(self, state: State[str]) -> Self:
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
    def __init__(
        self,
        text: str | None = None,
        *,
        command: Command | None = None,
        on_click: Callable[..., Any] | None = None,
        disabled: bool = False,
        variant: str = "secondary",
        icon: str = "",
    ):
        from .commands import Command
        from .widgets import choice

        if command is not None and not isinstance(command, Command):
            raise TypeError("command requires Command")
        if command is not None and on_click is not None:
            raise TypeError("use command or on_click, not both")
        if text is None:
            if command is None:
                raise TypeError("Button requires text or command")
            text = command.label
        self._command = command
        if not isinstance(disabled, bool):
            raise TypeError("disabled requires bool")
        handler = Handler(on_click) if on_click is not None else None
        variant = choice("primary", "secondary", "outline", "ghost", "danger")(variant)
        super().__init__(
            "button",
            text=_text(text),
            disabled=disabled,
            variant=variant,
            icon=_text(icon),
            command=None if command is None else command.id,
        )
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
        return self._properties["disabled"] or (self._command is not None and not self._command.enabled)

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("disabled requires bool")
        self._set("disabled", value)
