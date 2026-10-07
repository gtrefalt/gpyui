"""Dependent data updates and shared palette actions validate atomically."""

import asyncio
import json

import pytest
from test_dynamic import mounted

from gpyui import (
    Application,
    Combobox,
    Command,
    CommandPalette,
    MultiSelect,
    NumberInput,
    Select,
    State,
    Table,
    TableColumn,
    TableRow,
    TextArea,
    TextInput,
)
from gpyui._core import Bridge


def test_table_keys_survive_reorder_and_source_rows_are_not_sorted():
    table = Table(
        columns=[TableColumn("Quantity", sort_type="number")],
        rows=[TableRow("a", (10,)), TableRow("b", (2,))],
        value=1,
        sortable=True,
    )
    assert table.selected_key == "b"
    table.rows = [TableRow("b", (3,)), TableRow("a", (12,))]
    assert table.value == 0 and table.selected_key == "b"
    table.sort(0, descending=True)
    table.filter = "12"
    assert table.rows == [["3"], ["12"]] and table.selected_key == "b"
    before = table._spec()
    with pytest.raises(ValueError, match="unique"):
        table.rows = [TableRow("a", (1,)), TableRow("a", (2,))]
    assert table._spec() == before
    table.rows = [TableRow("a", (4,))]
    assert table.selected_key == "a"
    table.rows = []
    assert table.selected_key is None and table.value == 0
    with pytest.raises(ValueError):
        table.sort(1)
    with pytest.raises(ValueError):
        TableColumn("Invalid", width=23)
    with pytest.raises(ValueError):
        TableRow("invalid", (float("nan"),))


@pytest.mark.parametrize("control", [Select, Combobox, MultiSelect])
def test_option_replacement_preserves_valid_selection_and_updates_binding(control):
    selected = ["a", "b"] if control is MultiSelect else "b"
    state = State(selected)
    choice = control(["a", "b"]).bind_value(state)
    choice.items = ["b", "c"]
    assert choice.value == state.value == (["b"] if control is MultiSelect else "b")
    choice.items = ["c"]
    assert choice.value == state.value == ([] if control is MultiSelect else "")
    before = choice._spec()
    with pytest.raises(ValueError):
        choice.items = ["c", "c"]
    assert choice._spec() == before


def test_numeric_bounds_allow_partial_edits_and_validate_configuration():
    number = NumberInput("-", minimum=-5, maximum=5, step=0.25)
    number.value = "4."
    before = number._spec()
    with pytest.raises(ValueError):
        number.minimum = 6
    with pytest.raises(ValueError):
        number.step = 0
    assert number._spec() == before
    number.maximum = None
    assert number.maximum is None
    field = TextInput("secret", password=True, read_only=True, clearable=True, prefix="$", suffix="USD")
    field.disabled = True
    assert field._spec()["password"] is True and field.disabled
    with pytest.raises(TypeError):
        field.read_only = "yes"
    assert TextArea(read_only=True).read_only


def test_native_bridge_validates_final_dependent_batch_and_remembers_new_options():
    choice = Select(["a"], value="a")
    bridge = Bridge(json.dumps([choice._spec()]))

    def submit(**props):
        bridge.submit(
            json.dumps([{"id": choice.id, "property": key, "value": value} for key, value in props.items()])
        )

    try:
        submit(items=["b"], value="b")
        submit(value="")
        submit(value="b")  # Valid against the latest options, not the constructor.
        with pytest.raises(ValueError):
            submit(items=["c"], value="unknown")
        submit(value="b")  # Failed batch did not change the schema.
        with pytest.raises(ValueError):
            submit(items=["b", "b"])
    finally:
        bridge.finish()


def test_keyed_table_rows_and_selection_cross_native_bridge_in_one_batch():
    async def scenario():
        table = Table(columns=["Name"], rows=[TableRow("a", ("Ada",)), TableRow("b", ("Grace",))], value=1)
        app = Application(table)
        recording = mounted(app)
        bridge = Bridge(json.dumps([table._spec()]))
        try:
            table.rows = [TableRow("b", ("Grace",))]
            app.update()
            patches = recording.calls[-1][1]
            assert {p["property"] for p in patches} == {"rows", "row_keys", "value"}
            bridge.submit(json.dumps(patches))
            assert table.selected_key == "b"
        finally:
            bridge.finish()

    asyncio.run(scenario())


def test_palette_registers_shared_commands_and_rejects_invalid_replacement():
    async def scenario():
        command = Command("Save", lambda: None, shortcut="mod+s")
        palette = CommandPalette([command], query="sav")
        app = Application(palette)
        recording = mounted(app)
        assert command in app.commands
        next_command = Command("Open", lambda: None, shortcut="mod+o")
        palette.commands = [next_command, command]
        app.update()
        assert next_command in app.commands and palette.query == "sav"
        assert recording.calls[-1][0] == "reconcile"
        bridge = Bridge(json.dumps([palette._spec()]), json.dumps(app._config()))
        try:
            with pytest.raises(ValueError):
                bridge.submit(json.dumps([{"id": palette.id, "property": "items", "value": [999999]}]))
        finally:
            bridge.finish()
        before = palette.commands
        with pytest.raises(ValueError):
            palette.commands = [command, command]
        assert palette.commands == before
        foreign = Command("Other", lambda: None)
        foreign._app = Application()
        with pytest.raises(ValueError, match="one application"):
            palette.commands = [foreign]
        assert palette.commands == before

    asyncio.run(scenario())
