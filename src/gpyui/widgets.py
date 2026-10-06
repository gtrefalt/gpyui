"""Python handles for the native GPUI Kit component catalog.

Properties are validated before attachment and sent as batched updates. Mutable
collections are copied on assignment and read: reassign them to update the UI.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Callable, Iterable
from datetime import date, time
from typing import Any, ClassVar, Self

from .controls import Column, Control, Handler, _containers
from .state import State


def text(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("requires str")
    return value


def boolean(value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError("requires bool")
    return value


def number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError("requires a number")
    if not math.isfinite(value) or abs(value) > 1e9:
        raise ValueError("requires a finite number within ±1e9")
    return float(value)


def integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("requires int")
    if not 0 <= value <= 1_000_000:
        raise ValueError("requires an integer between 0 and 1,000,000")
    return value


def choice(*values: str) -> Callable[[Any], str]:
    def validate(value: Any) -> str:
        if value not in values:
            raise ValueError(f"requires one of {values}")
        return text(value)

    return validate


def strings(value: Any) -> list[str]:
    if isinstance(value, str) or not isinstance(value, list | tuple):
        raise TypeError("requires a list or tuple of strings")
    if len(value) > 10_000:
        raise ValueError("at most 10,000 items are supported")
    return [text(item) for item in value]


def rows(value: Any) -> list[list[str]]:
    if not isinstance(value, list | tuple) or len(value) > 10_000:
        raise ValueError("requires up to 10,000 rows")
    return [strings(row) for row in value]


def points(value: Any) -> list[list[Any]]:
    if not isinstance(value, list | tuple) or len(value) > 10_000:
        raise ValueError("requires up to 10,000 data points")
    result = []
    for row in value:
        if not isinstance(row, list | tuple) or len(row) < 2:
            raise ValueError("a chart point is [label, value, ...]")
        result.append([text(row[0]), *[number(v) for v in row[1:]]])
    return result


def percent(value: Any) -> float:
    result = number(value)
    if not 0 <= result <= 100:
        raise ValueError("requires a percentage between 0 and 100")
    return result


_TOKENS = (
    "background",
    "foreground",
    "muted",
    "muted_foreground",
    "primary",
    "primary_foreground",
    "secondary",
    "secondary_foreground",
    "border",
    "accent",
    "accent_foreground",
    "danger",
    "success",
    "warning",
    "info",
    "transparent",
    "popover",
    "sidebar",
)


def validate_style(properties: dict[str, Any]) -> dict[str, Any]:
    validators = {
        **dict.fromkeys(
            ("width", "height", "min_width", "min_height", "padding", "gap", "radius", "font_size"), number
        ),
        "flex": number,
        "full_width": boolean,
        "full_height": boolean,
        "border": boolean,
        "background": choice(*_TOKENS),
        "color": choice(*_TOKENS),
        "align": choice("start", "center", "end", "stretch"),
        "justify": choice("start", "center", "end", "between"),
        "bold": boolean,
    }
    result = {}
    for key, value in properties.items():
        if key not in validators:
            raise ValueError(f"unsupported style property: {key}")
        validated = validators[key](value)
        if isinstance(validated, float) and validated < 0:
            raise ValueError(f"{key} must be nonnegative")
        result[key] = validated
    return result


# (default value, validator). Concrete classes define their native contract.
Field = tuple[Any, Callable[[Any], Any]]
TEXT: Field = ("", text)
BOOL: Field = (False, boolean)
VALUE: Field = (0, number)
INDEX: Field = (0, integer)
ITEMS: Field = ([], strings)
VARIANT: Field = ("secondary", choice("primary", "secondary", "success", "warning", "danger", "info"))


class KitControl(Column):
    """A typed native Kit component, with Python-owned callback registrations.

    The first declared field accepts a positional argument. Other properties are
    keyword arguments. Container components also accept children or a with block.
    """

    native: ClassVar[str]
    fields: ClassVar[dict[str, Field]] = {}
    container: ClassVar[bool] = False
    events: ClassVar[tuple[str, ...]] = ()
    readonly: ClassVar[tuple[str, ...]] = ()

    def __init__(self, *args: Any, children: Iterable[Control] = (), **properties: Any):
        if len(args) == 1 and self.container and not self.fields:
            children = args[0]
            args = ()
        if len(args) > 1:
            raise TypeError("at most one positional property is accepted")
        if args:
            if not self.fields:
                raise TypeError("this component has no positional property")
            name = next(iter(self.fields))
            if name in properties:
                raise TypeError(f"{name} specified twice")
            properties[name] = args[0]
        handlers = {}
        for event in self.events:
            callback = properties.pop(f"on_{event}", None)
            if callback is not None:
                handlers[event] = Handler(callback)
        unknown = properties.keys() - self.fields.keys()
        if unknown:
            raise TypeError(f"unknown properties for {type(self).__name__}: {sorted(unknown)}")
        props = {
            key: validate(copy.deepcopy(properties.get(key, default)))
            for key, (default, validate) in self.fields.items()
        }
        self._validate(props)
        children = tuple(children)
        if children and not self.container:
            raise TypeError(f"{type(self).__name__} does not accept children")
        seen = set()
        for child in children:
            if not isinstance(child, Control):
                raise TypeError("containers accept Control children")
            if child in _containers.get():
                raise ValueError("control tree cannot contain a cycle")
            child._ensure_alive()
            if child._parent is not None or child.id in seen:
                raise ValueError("a control can have only one parent")
            if child._app is not None:
                parent = _containers.get()[-1] if _containers.get() else None
                app = parent._app if isinstance(parent, Control) else parent
                if child._app is not app:
                    raise ValueError("a control can belong to only one application")
            seen.add(child.id)
        self._children = []
        self._state: State[Any] | None = None
        Control.__init__(self, "kit", kind=self.native, props=props)
        self._handlers.update(handlers)
        self.add(*children)

    def _validate(self, props: dict[str, Any]) -> None:
        pass

    def add(self, *controls: Control) -> Self:
        if controls and not self.container:
            raise TypeError(f"{type(self).__name__} does not accept children")
        super().add(*controls)
        return self

    def __getattr__(self, name: str) -> Any:
        if name in self.fields and "_properties" in self.__dict__:
            return copy.deepcopy(self._properties["props"][name])
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name not in self.fields or "_properties" not in self.__dict__:
            super().__setattr__(name, value)
            return
        if name in self.readonly:
            raise AttributeError(f"{name} is fixed after construction")
        self._ensure_alive()
        value = self.fields[name][1](copy.deepcopy(value))
        props = self._properties["props"]
        self._validate({**props, name: value})
        if self._app:
            self._app._check_mutation()
        if props[name] != value:
            props[name] = value
            if self._app:
                self._app._queue(self.id, name, value)
        if name == "value" and self._state is not None:
            self._state.value = value

    def bind_value(self, state: State[Any]) -> Self:
        if "value" not in self.fields or "change" not in self.events:
            raise TypeError("this control has no bindable value")
        self.unbind()
        self.value = state.value
        self._state = state
        self._bindings.append(state.subscribe(lambda value: setattr(self, "value", value)))
        return self

    def unbind(self) -> None:
        super().unbind()
        self._state = None

    def _receive_native(self, value: Any) -> None:
        # Native interactions already changed native state; do not echo setters.
        self._properties["props"]["value"] = value
        if self._state is not None:
            self._state.value = value


class Row(KitControl):
    native = "row"
    container = True


class Container(KitControl):
    native = "container"
    container = True


class Scroll(KitControl):
    native = "scroll"
    container = True


class GroupBox(KitControl):
    native = "group_box"
    container = True
    fields = {"title": TEXT}


class Toolbar(KitControl):
    native = "toolbar"
    container = True


class StatusBar(KitControl):
    native = "status_bar"
    container = True


class Checkbox(KitControl):
    native = "checkbox"
    fields = {"text": TEXT, "value": BOOL, "disabled": BOOL}
    events = ("change",)


class Switch(Checkbox):
    native = "switch"


class Radio(Checkbox):
    native = "radio"


class Toggle(Checkbox):
    native = "toggle"


class RadioGroup(KitControl):
    native = "radio_group"
    fields = {"items": ITEMS, "value": INDEX, "disabled": BOOL}
    events = ("change",)

    def _validate(self, props: dict[str, Any]) -> None:
        if props["items"] and props["value"] >= len(props["items"]):
            raise ValueError("value must be a valid item index")


class Tabs(RadioGroup):
    native = "tabs"


class Sidebar(RadioGroup):
    native = "sidebar"


class Breadcrumb(RadioGroup):
    native = "breadcrumb"


class Rating(KitControl):
    native = "rating"
    fields = {"value": INDEX, "disabled": BOOL}
    events = ("change",)

    def _validate(self, props: dict[str, Any]) -> None:
        if props["value"] > 5:
            raise ValueError("rating must be between 0 and 5")


class Slider(KitControl):
    native = "slider"
    fields = {
        "value": VALUE,
        "minimum": (0, number),
        "maximum": (100, number),
        "step": (1, number),
        "disabled": BOOL,
    }
    events = ("change", "release")
    readonly = ("minimum", "maximum", "step")

    def _validate(self, props: dict[str, Any]) -> None:
        if not props["minimum"] < props["maximum"] or props["step"] <= 0:
            raise ValueError("slider requires minimum < maximum and step > 0")
        if not props["minimum"] <= props["value"] <= props["maximum"]:
            raise ValueError("value is outside the slider range")


class Select(KitControl):
    native = "select"
    fields = {"items": ITEMS, "value": TEXT, "placeholder": ("Choose…", text), "disabled": BOOL}
    events = ("change",)
    readonly = ("items",)

    def _validate(self, props: dict[str, Any]) -> None:
        if props["value"] and props["value"] not in props["items"]:
            raise ValueError("value must be an item or the empty string")


class Progress(KitControl):
    native = "progress"
    fields = {"value": (0, percent), "loading": BOOL}


class ProgressCircle(Progress):
    native = "progress_circle"


class Spinner(KitControl):
    native = "spinner"


class Tag(KitControl):
    native = "tag"
    fields = {"text": TEXT, "variant": VARIANT}


class Badge(KitControl):
    native = "badge"
    fields = {"count": INDEX, "text": TEXT}


class Avatar(KitControl):
    native = "avatar"
    fields = {"name": TEXT}


class Icon(KitControl):
    native = "icon"
    fields = {"name": ("check", text)}

    def _validate(self, props: dict[str, Any]) -> None:
        name = props["name"]
        if not name or not all(c.islower() or c.isdigit() or c == "-" for c in name):
            raise ValueError("icon names use lowercase Lucide names, e.g. 'arrow-right'")


class Separator(KitControl):
    native = "separator"
    fields = {"text": TEXT, "vertical": BOOL}


class Link(KitControl):
    native = "link"
    fields = {"text": TEXT, "href": TEXT, "disabled": BOOL}
    events = ("click",)


class Pagination(KitControl):
    native = "pagination"
    fields = {"value": INDEX, "pages": (1, integer)}
    events = ("change",)

    def _validate(self, props: dict[str, Any]) -> None:
        if props["pages"] < 1 or props["value"] >= props["pages"]:
            raise ValueError("page indices start at zero and must be below pages")


class DescriptionList(KitControl):
    native = "description_list"
    fields = {"items": ([], rows)}

    def _validate(self, props: dict[str, Any]) -> None:
        if any(len(row) != 2 for row in props["items"]):
            raise ValueError("description items are [label, value] pairs")


class Empty(KitControl):
    native = "empty"
    fields = {"title": ("No items", text), "description": TEXT}


class Alert(KitControl):
    native = "alert"
    fields = {
        "text": TEXT,
        "title": TEXT,
        "variant": ("info", choice("info", "success", "warning", "danger")),
    }


class Skeleton(KitControl):
    native = "skeleton"


class Shimmer(KitControl):
    native = "shimmer"
    fields = {"text": ("Loading…", text)}


class Kbd(KitControl):
    native = "kbd"
    fields = {"key": ("ctrl-k", text)}


class Collapsible(KitControl):
    native = "collapsible"
    container = True
    fields = {"text": TEXT, "value": BOOL}
    events = ("change",)


class Accordion(KitControl):
    native = "accordion"
    fields = {"items": ([], rows), "value": INDEX, "disabled": BOOL}
    events = ("change",)

    def _validate(self, props: dict[str, Any]) -> None:
        if any(len(row) != 2 for row in props["items"]):
            raise ValueError("accordion items are [title, content] pairs")


class Table(KitControl):
    native = "table"
    fields = {"columns": ITEMS, "rows": ([], rows), "value": INDEX, "column_width": (125, number)}
    events = ("change",)
    readonly = ("columns", "column_width")

    def _validate(self, props: dict[str, Any]) -> None:
        if props["column_width"] < 24:
            raise ValueError("column_width must be at least 24 pixels")
        if any(len(row) != len(props["columns"]) for row in props["rows"]):
            raise ValueError("each table row must match the column count")


class LineChart(KitControl):
    native = "line_chart"
    fields = {"data": ([], points)}

    def _validate(self, props: dict[str, Any]) -> None:
        if any(len(point) != 2 for point in props["data"]):
            raise ValueError("data points must be [label, value]")


class AreaChart(LineChart):
    native = "area_chart"


class BarChart(LineChart):
    native = "bar_chart"


class PieChart(LineChart):
    native = "pie_chart"

    def _validate(self, props: dict[str, Any]) -> None:
        super()._validate(props)
        if any(point[1] < 0 for point in props["data"]):
            raise ValueError("pie values must be nonnegative")


class CandlestickChart(LineChart):
    native = "candlestick_chart"

    def _validate(self, props: dict[str, Any]) -> None:
        for point in props["data"]:
            if len(point) != 5:
                raise ValueError("candles are [label, open, high, low, close]")
            _, opening, high, low, close = point
            if not low <= min(opening, close) <= max(opening, close) <= high:
                raise ValueError("candles require low <= open/close <= high")


class Bubble(KitControl):
    native = "bubble"
    container = True


class Message(KitControl):
    native = "message"
    fields = {"text": TEXT, "author": TEXT}


class Marker(KitControl):
    native = "marker"
    fields = {"text": TEXT, "loading": BOOL}


class Attachment(KitControl):
    native = "attachment"
    fields = {"title": TEXT, "description": TEXT}


class Clipboard(KitControl):
    native = "clipboard"
    fields = {"text": TEXT}


class Tooltip(KitControl):
    native = "tooltip"
    container = True
    fields = {"text": TEXT}


class Popover(KitControl):
    native = "popover"
    container = True
    fields = {"text": ("Details", text)}


class HoverCard(Popover):
    native = "hover_card"


class Stepper(RadioGroup):
    native = "stepper"


class List(RadioGroup):
    native = "list"


class Combobox(Select):
    native = "combobox"


class TextArea(KitControl):
    native = "textarea"
    fields = {"value": TEXT, "placeholder": TEXT, "disabled": BOOL}
    events = ("change",)


class NumberInput(TextArea):
    """Native numeric text editing. value is text, including partial edits."""

    native = "number_input"


class OtpInput(TextArea):
    native = "otp_input"
    fields = {"value": TEXT, "length": (6, integer), "disabled": BOOL}
    readonly = ("length",)

    def _validate(self, props: dict[str, Any]) -> None:
        if not 1 <= props["length"] <= 32:
            raise ValueError("OTP length must be between 1 and 32")
        if len(props["value"]) > props["length"] or any(c not in "0123456789" for c in props["value"]):
            raise ValueError("OTP value must contain at most length ASCII digits")


def iso_date(value: Any) -> str:
    return str(date.fromisoformat(text(value))) if value else text(value)


def iso_time(value: Any) -> str:
    parsed = time.fromisoformat(text(value))
    if parsed.tzinfo is not None:
        raise ValueError("time must be local, without a timezone")
    return parsed.strftime("%H:%M:%S")


def hex_color(value: Any) -> str:
    value = text(value).lower()
    if len(value) not in {7, 9} or value[0] != "#" or any(c not in "0123456789abcdef" for c in value[1:]):
        raise ValueError("color requires #rrggbb or #rrggbbaa")
    return value


class Calendar(KitControl):
    native = "calendar"
    fields = {"value": ("", iso_date)}
    events = ("change",)


class DatePicker(Calendar):
    native = "date_picker"


class TimeField(KitControl):
    native = "time_field"
    fields = {"value": ("09:30:00", iso_time)}
    events = ("change",)


class ColorPicker(KitControl):
    native = "color_picker"
    fields = {"value": ("#3b82f6", hex_color)}
    events = ("change",)


class Carousel(KitControl):
    native = "carousel"
    container = True
    fields = {"value": INDEX}
    events = ("change",)


class Dialog(KitControl):
    native = "dialog"
    container = True
    fields = {"title": TEXT, "value": BOOL}
    events = ("change",)
    readonly = ("title",)

    def open(self) -> None:
        self.value = True

    def close(self) -> None:
        self.value = False


class Sheet(Dialog):
    native = "sheet"


class Markdown(KitControl):
    native = "markdown"
    fields = {"text": TEXT}


class Html(Markdown):
    native = "html"


class Editor(TextArea):
    native = "editor"


class Resizable(KitControl):
    native = "resizable"
    container = True
    fields = {"vertical": BOOL}
    events = ("resize",)
    readonly = ("vertical",)


def tree_items(value: Any) -> list[dict[str, Any]]:
    ids: set[str] = set()

    def visit(nodes: Any, depth: int) -> list[dict[str, Any]]:
        if depth > 32 or not isinstance(nodes, list | tuple):
            raise ValueError("tree items require lists with at most 32 levels")
        result = []
        for item in nodes:
            if not isinstance(item, dict) or item.keys() - {"id", "text", "children"}:
                raise ValueError("tree items have id, text and optional children")
            identity = text(item.get("id"))
            if not identity or identity in ids or len(ids) >= 10_000:
                raise ValueError("tree item IDs must be nonempty and unique; at most 10,000 items")
            ids.add(identity)
            result.append(
                {
                    "id": identity,
                    "text": text(item.get("text")),
                    "children": visit(item.get("children", []), depth + 1),
                }
            )
        return result

    return visit(value, 0)


class Tree(KitControl):
    native = "tree"
    fields = {"items": ([], tree_items), "value": TEXT}
    events = ("change",)
    readonly = ("items",)

    def _validate(self, props: dict[str, Any]) -> None:
        def identities(items):
            for item in items:
                yield item["id"]
                yield from identities(item["children"])

        if props["value"] and props["value"] not in set(identities(props["items"])):
            raise ValueError("tree value must be an item ID or empty string")


COMPONENTS = tuple(
    value
    for value in tuple(globals().values())
    if isinstance(value, type) and issubclass(value, KitControl) and value is not KitControl
)
