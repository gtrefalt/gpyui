"""Reusable application commands and declarative menu models."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from .controls import Control, Handler, _ids
from .state import State

if TYPE_CHECKING:
    from .application import Application


def shortcut_key(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("shortcut requires str")
    if not value:
        return ""
    parts = value.lower().split("+")
    modifiers = parts[:-1]
    key = parts[-1]
    allowed = {"mod", "ctrl", "cmd", "alt", "shift"}
    if any(part not in allowed for part in modifiers) or len(set(modifiers)) != len(modifiers):
        raise ValueError("shortcut requires modifiers joined by '+', followed by one key")
    if not key or not key.isascii() or not key.replace("_", "").isalnum():
        raise ValueError("shortcut requires one letter, digit or named key")
    # Resolve the portable modifier before detecting aliases such as mod+ctrl.
    modifiers = [
        ("cmd" if sys.platform == "darwin" else "ctrl") if part == "mod" else part for part in parts[:-1]
    ]
    if len(set(modifiers)) != len(modifiers):
        raise ValueError("shortcut contains duplicate platform modifiers")
    if not modifiers and not (key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24):
        raise ValueError("shortcut requires a modifier or a function key")
    return "-".join([*(part for part in ("ctrl", "cmd", "alt", "shift") if part in modifiers), key])


class Command:
    """A window-owned callback shared by buttons, menus and a shortcut."""

    def __init__(
        self,
        label: str,
        on_execute: Callable[..., Any],
        *,
        shortcut: str = "",
        enabled: bool = True,
        checked: bool = False,
    ):
        if not isinstance(label, str) or not label:
            raise ValueError("command label requires a nonempty string")
        if not isinstance(enabled, bool) or not isinstance(checked, bool):
            raise TypeError("enabled and checked require bool")
        self._id = next(_ids)
        self._label = label
        self._shortcut = shortcut
        self._key = shortcut_key(shortcut)
        self._enabled, self._checked = enabled, checked
        self._handler = Handler(on_execute)
        self._app: Application | None = None
        self._bindings: list[Callable[[], None]] = []

    @property
    def id(self) -> int:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @property
    def shortcut(self) -> str:
        return self._shortcut

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._set("enabled", value)

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        self._set("checked", value)

    def _set(self, name: str, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"{name} requires bool")
        if self._app is not None:
            self._app._check_mutation()
        if getattr(self, f"_{name}") != value:
            setattr(self, f"_{name}", value)
            if self._app is not None:
                self._app._queue(self.id, name, value)

    def execute(self) -> None:
        """Queue execution with a current native input snapshot on the owning window."""
        if self._app is None:
            from .application import ApplicationClosedError

            raise ApplicationClosedError("command is not mounted")
        self._app._check_mutation()
        if self.enabled:
            self._app.update()
            self._app._bridge.execute(self.id)

    def bind_enabled(self, state: State[bool]) -> Self:
        self.enabled = state.value
        self._bindings.append(state.subscribe(lambda value: setattr(self, "enabled", value)))
        return self

    def bind_checked(self, state: State[bool]) -> Self:
        self.checked = state.value
        self._bindings.append(state.subscribe(lambda value: setattr(self, "checked", value)))
        return self

    def unbind(self) -> None:
        for unsubscribe in self._bindings:
            unsubscribe()
        self._bindings.clear()

    def _spec(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "shortcut": self._key,
            "enabled": self.enabled,
            "checked": self.checked,
        }


@dataclass(frozen=True)
class MenuSeparator:
    """A separator shared by all menu backends."""


@dataclass(frozen=True, init=False)
class Menu:
    """An immutable menu/submenu; reassign its owner's items to replace it."""

    label: str
    items: tuple[Command | Menu | MenuSeparator, ...]

    def __init__(self, label: str, items: Iterable[Command | Menu | MenuSeparator]):
        if not isinstance(label, str) or not label:
            raise ValueError("menu label requires a nonempty string")
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "items", validate_items(items))


def validate_items(
    items: Iterable[Command | Menu | MenuSeparator],
) -> tuple[Command | Menu | MenuSeparator, ...]:
    result = tuple(items)
    count = 0

    def visit(entries, depth):
        nonlocal count
        if depth > 8:
            raise ValueError("menus exceed eight submenu levels")
        for item in entries:
            count += 1
            if count > 1000:
                raise ValueError("menu exceeds 1,000 entries")
            if not isinstance(item, (Command, Menu, MenuSeparator)):
                raise TypeError("menu items require Command, Menu or MenuSeparator")
            if isinstance(item, Menu):
                visit(item.items, depth + 1)

    visit(result, 0)
    return result


def menu_commands(items: Iterable[Command | Menu | MenuSeparator]) -> Iterator[Command]:
    for item in items:
        if isinstance(item, Command):
            yield item
        elif isinstance(item, Menu):
            yield from menu_commands(item.items)


def menu_specs(items: Iterable[Command | Menu | MenuSeparator]) -> list[dict[str, Any]]:
    return [
        {"type": "command", "id": item.id}
        if isinstance(item, Command)
        else {"type": "menu", "label": item.label, "items": menu_specs(item.items)}
        if isinstance(item, Menu)
        else {"type": "separator"}
        for item in items
    ]


class DropdownMenu(Control):
    """A GPUI Kit button that opens a keyboard-navigable popup menu."""

    def __init__(self, text: str, items: Iterable[Command | Menu | MenuSeparator]):
        if not isinstance(text, str):
            raise TypeError("text requires str")
        self._items = validate_items(items)
        super().__init__("dropdown_menu", text=text, items=menu_specs(self._items), disabled=False)

    @property
    def items(self) -> tuple[Command | Menu | MenuSeparator, ...]:
        return self._items

    @items.setter
    def items(self, items: Iterable[Command | Menu | MenuSeparator]) -> None:
        value = validate_items(items)
        self._ensure_alive()
        if self._app is not None:
            self._app._check_mutation()
            self._app._register_commands(menu_commands(value))
        self._set("items", menu_specs(value))
        self._items = value

    @property
    def text(self) -> str:
        return self._properties["text"]

    @text.setter
    def text(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("text requires str")
        self._set("text", value)

    @property
    def disabled(self) -> bool:
        return self._properties["disabled"]

    @disabled.setter
    def disabled(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("disabled requires bool")
        self._set("disabled", value)
