"""Native Kit form composition with Python-owned validation and submission."""

from __future__ import annotations

import copy
import inspect
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from .commands import Command
from .controls import Control, Handler, TextInput
from .tree import walk
from .widgets import BOOL, TEXT, KitControl, choice, number, text


def columns(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 12:
        raise ValueError("requires an integer between 1 and 12")
    return value


def field_name(value: Any) -> str:
    value = text(value)
    if value and (not value.strip() or len(value) > 128):
        raise ValueError("field name requires 1–128 nonblank characters")
    return value


def label_width(value: Any) -> float:
    value = number(value)
    if value < 0:
        raise ValueError("label width requires a nonnegative number")
    return value


class ValidationError(Exception):
    """Expected submission failure with named field errors and optional summary."""

    def __init__(self, errors: Mapping[str, str], message: str = "Please fix the marked fields."):
        if not isinstance(errors, Mapping):
            raise TypeError("errors requires a mapping")
        self.errors = dict(errors)
        if any(
            not isinstance(key, str) or not key or not isinstance(value, str) or not value
            for key, value in self.errors.items()
        ):
            raise ValueError("field errors require nonempty names and messages")
        super().__init__(text(message))


class Field(KitControl):
    """A real Kit Field. Validators return None/empty string or an error message."""

    native = "field"
    container = True
    fields = {
        "label": TEXT,
        "name": ("", field_name),
        "help": TEXT,
        "required": BOOL,
        "error": TEXT,
        "col_span": (1, columns),
    }
    readonly = ("name",)

    def __init__(
        self,
        label: str = "",
        *,
        name: str = "",
        control: Control | None = None,
        validators: Iterable[Callable[[Any], Any]] = (),
        children: Iterable[Control] = (),
        **properties: Any,
    ):
        self._validators = tuple(validators)
        for validator in self._validators:
            if not callable(validator):
                raise TypeError("validators requires callables accepting one value")
            inspect.signature(validator).bind(None)
        children = tuple(children)
        if control is not None:
            if children:
                raise ValueError("use control or children, not both")
            children = (control,)
        super().__init__(label, name=name, children=children, **properties)

    @property
    def validators(self) -> tuple[Callable[[Any], Any], ...]:
        return self._validators

    @property
    def control(self) -> TextInput | KitControl:
        """Resolve the one bindable value control, including inside child layouts."""
        controls = [
            node
            for child in self.children
            for node in walk(child)
            if isinstance(node, TextInput)
            or isinstance(node, KitControl)
            and "value" in node.fields
            and "change" in node.events
        ]
        if len(controls) != 1:
            raise ValueError(f"field {self.name!r} requires exactly one bindable value control")
        return controls[0]


class Form(KitControl):
    """A real Kit Form whose shared command validates and awaits a save callback.

    The save callback accepts zero arguments or a copied dict of active raw values.
    Hidden fields retain their controls but are excluded from validation/submission.
    """

    native = "form"
    container = True
    fields = {
        "label_layout": ("vertical", choice("vertical", "horizontal")),
        "columns": (1, columns),
        "label_width": (140, label_width),
        "size": ("medium", choice("small", "medium", "large")),
        "error": TEXT,
    }

    def __init__(
        self,
        *,
        on_submit: Callable[..., Any] | None = None,
        submit_label: str = "Save",
        shortcut: str = "",
        children: Iterable[Field] = (),
        **properties: Any,
    ):
        self._submit_handler = Handler(on_submit) if on_submit is not None else None
        self._busy = False
        self._command = Command(submit_label, self.submit, shortcut=shortcut)
        super().__init__(children=children, **properties)

    def _validate_children(self, children: tuple[Control, ...]) -> None:
        names: set[str] = set()
        for field in children:
            if not isinstance(field, Field):
                raise TypeError("Form accepts Field children; compose actions outside the Form")
            if not field.name or field.name in names:
                raise ValueError("Form fields require nonempty unique names")
            names.add(field.name)

    @property
    def submit_command(self) -> Command:
        return self._command

    @property
    def busy(self) -> bool:
        return self._busy

    def _check_access(self) -> None:
        self._ensure_alive()
        if self._app is not None and self._app._phase != "new":
            self._app._check_mutation()

    def _active_fields(self) -> tuple[Field, ...]:
        node: Any = self
        while isinstance(node, Control):
            if not node.visible or node.disposed:
                return ()
            node = node._parent
        if self._app is not None and self._app._phase != "new" and node is not self._app:
            return ()
        return tuple(field for field in self.children if isinstance(field, Field) and field.visible)

    def values(self) -> dict[str, Any]:
        """Read copied active raw values. Numeric editors remain editing strings."""
        self._check_access()
        return {field.name: copy.deepcopy(field.control.value) for field in self._active_fields()}

    @property
    def errors(self) -> dict[str, str]:
        return {field.name: field.error for field in self._active_fields() if field.error}

    def clear_errors(self) -> None:
        self._check_access()
        self.error = ""
        for field in self.children:
            if isinstance(field, Field):
                field.error = ""

    def _capture(self) -> tuple[list[tuple[Field, TextInput | KitControl, Any, bool]], dict[str, Any]]:
        captured = [
            (field, field.control, copy.deepcopy(field.control.value), field.required)
            for field in self._active_fields()
        ]
        return captured, {field.name: copy.deepcopy(value) for field, _, value, _ in captured}

    def _current(self, captured: list[tuple[Field, TextInput | KitControl, Any, bool]]) -> bool:
        active = self._active_fields()
        try:
            return len(active) == len(captured) and all(
                current is field
                and field.control is control
                and field.required == required
                and control.value == value
                for current, (field, control, value, required) in zip(active, captured, strict=True)
            )
        except (ValueError, RuntimeError):
            return False

    async def _validate_capture(
        self, captured: list[tuple[Field, TextInput | KitControl, Any, bool]]
    ) -> bool:
        errors: dict[str, str] = {}
        for field, _, value, required in captured:
            empty = (
                value is None or value is False or isinstance(value, str) and not value.strip() or value == []
            )
            if required and empty:
                errors[field.name] = "This field is required."
                continue
            for validator in field.validators:
                try:
                    error = validator(copy.deepcopy(value))
                    if inspect.isawaitable(error):
                        error = await error
                except ValueError as failure:
                    error = str(failure) or "Invalid value."
                if error is not None and not isinstance(error, str):
                    raise TypeError("validators must return None or an error message string")
                if error:
                    errors[field.name] = error
                    break
        self._check_access()
        if not self._current(captured):
            self.error = "Values changed during validation. Please review and try again."
            return False
        for field, _, _, _ in captured:
            field.error = errors.get(field.name, "")
        self.error = "Please fix the marked fields." if errors else ""
        return not errors

    async def validate(self) -> bool:
        """Validate active values without rewriting or reconstructing editors."""
        self._check_access()
        if self._busy:
            return False
        return await self._operate(save=False)

    async def submit(self) -> bool:
        """Validate and save once. Expected failures remain visible and retryable."""
        self._check_access()
        if self._busy:
            return False
        return await self._operate(save=True)

    async def _operate(self, *, save: bool) -> bool:
        from .application import ApplicationClosedError

        self._busy = True
        was_enabled = self.submit_command.enabled
        self.submit_command.enabled = False
        captured = []
        try:
            captured, values = self._capture()
            if not captured:
                self.error = "No active fields to submit."
                return False
            if not await self._validate_capture(captured):
                return False
            if save and self._submit_handler is not None:
                handler = self._submit_handler
                result = handler.callback(values) if handler.arguments else handler.callback()
                if inspect.isawaitable(result):
                    await result
            return True
        except ValidationError as failure:
            self._check_access()
            known = {field.name for field, _, _, _ in captured}
            if failure.errors.keys() - known:
                raise ValueError("submission errors must name active fields") from failure
            if self._current(captured):
                for field, _, _, _ in captured:
                    field.error = failure.errors.get(field.name, "")
                self.error = str(failure)
            else:
                self.error = "Values changed while saving. Please review and try again."
            return False
        except OSError as failure:
            self._check_access()
            self.error = str(failure) or "Could not save. Please try again."
            return False
        finally:
            self._busy = False
            try:
                if not self.disposed:
                    self.submit_command.enabled = was_enabled
            except ApplicationClosedError:
                pass

    def dispose(self) -> None:
        if not self.disposed:
            self.submit_command.enabled = False
        super().dispose()
