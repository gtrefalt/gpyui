import json

import pytest

from gpyui import (
    Application,
    Checkbox,
    ColorPicker,
    Column,
    Dialog,
    Label,
    OtpInput,
    Row,
    Select,
    Slider,
    State,
    Table,
    Tabs,
    Tree,
)
from gpyui._core import Bridge
from gpyui.widgets import COMPONENTS


@pytest.mark.parametrize("component", COMPONENTS, ids=lambda c: c.__name__)
def test_component_contract_is_accepted_by_native_bridge(component):
    control = component()
    bridge = Bridge(json.dumps([control._spec()]))
    bridge.finish()


def test_boolean_binding_does_not_echo_native_interaction():
    state = State(False)
    check = Checkbox("Enabled").bind_value(state)
    messages = []
    check._app = type(
        "Mounted", (), {"_check_mutation": lambda _: None, "_queue": lambda _, *args: messages.append(args)}
    )()
    check._receive_native(True)
    assert check.value is state.value is True
    assert messages == []
    state.value = False
    assert messages == [(check.id, "value", False)]
    check.unbind()
    state.value = True
    assert check.value is False


def test_color_picker_preserves_alpha_in_the_bridge_contract():
    picker = ColorPicker("#33669980")
    bridge = Bridge(json.dumps([picker._spec()]))
    try:
        assert picker.value == "#33669980"
        picker.value = "#11223344"
        bridge.submit(json.dumps([{"id": picker.id, "property": "value", "value": picker.value}]))
        with pytest.raises(ValueError):
            picker.value = "#1122334"
    finally:
        bridge.finish()


def test_collections_are_copied_and_reassignment_validates_shape():
    data = [["Ada", "Ready"]]
    table = Table(columns=["Name", "Status"], rows=data)
    data[0][0] = "Changed outside the control"
    table.rows[0][0] = "Changed outside the control"
    assert table.rows == [["Ada", "Ready"]]
    with pytest.raises(ValueError, match="column count"):
        table.rows = [["Missing a cell"]]
    assert table.rows == [["Ada", "Ready"]]
    table.rows = [["Grace", "Ready"]]
    assert table.rows[0][0] == "Grace"


def test_mixed_layout_composition_and_leaf_ownership():
    with Application() as app:
        with Row() as row:
            with Column() as column:
                label = Label("One owner")
            check = Checkbox("Enabled")
    assert row.children == (column, check)
    assert column.children == (label,)
    with pytest.raises(ValueError, match="one parent"):
        app.add(check)
    with pytest.raises(TypeError, match="does not accept children"):
        check.add(Label("Invalid"))


def test_failed_component_property_registration_does_not_attach():
    with Application() as app:
        with pytest.raises(TypeError):
            Checkbox("Enabled", on_change=lambda a, b: None)
        with pytest.raises(TypeError, match="unknown properties"):
            Checkbox("Enabled", imaginary=True)
        with pytest.raises(ValueError, match="slider range"):
            Slider(200)
    assert app.children == ()


def test_invalid_numeric_and_style_updates_fail_without_mutating():
    slider = Slider(25)
    with pytest.raises(ValueError):
        slider.value = float("nan")
    with pytest.raises(AttributeError, match="fixed"):
        slider.maximum = 500
    assert slider.value == 25
    with pytest.raises(ValueError, match="nonnegative"):
        slider.style(width=-1)
    with pytest.raises(ValueError, match="unsupported style"):
        slider.style(imaginary=42)
    assert slider._style == {}
    tabs = Tabs(["One", "Two"])
    with pytest.raises(ValueError, match="valid item index"):
        tabs.value = 3


def test_new_control_batches_remain_atomic():
    control = Checkbox("Enabled")
    bridge = Bridge(json.dumps([control._spec()]))
    with pytest.raises(ValueError, match="invalid property"):
        bridge.submit(
            json.dumps(
                [
                    {"id": control.id, "property": "value", "value": True},
                    {"id": control.id, "property": "disabled", "value": "not a boolean"},
                ]
            )
        )
    bridge.submit(json.dumps([{"id": control.id, "property": "value", "value": True}]))
    bridge.finish()


@pytest.mark.parametrize(
    "control,property,value",
    [
        (Slider(20, minimum=10, maximum=50), "value", 51),
        (Select(["One", "Two"]), "value", "Unknown"),
        (OtpInput(length=4), "value", "12345"),
        (OtpInput(length=4), "value", "１２３４"),
        (Table(columns=["Name", "Status"]), "rows", [["Missing cell"]]),
        (Tree([{"id": "one", "text": "One"}]), "value", "unknown"),
    ],
)
def test_native_bridge_validates_fixed_component_constraints(control, property, value):
    bridge = Bridge(json.dumps([control._spec()]))
    try:
        with pytest.raises(ValueError, match="invalid property"):
            bridge.submit(json.dumps([{"id": control.id, "property": property, "value": value}]))
    finally:
        bridge.finish()


def test_tree_ids_and_child_attachment_are_validated_before_mount():
    with pytest.raises(ValueError, match="unique"):
        Tree([{"id": "duplicate", "text": "Parent", "children": [{"id": "duplicate", "text": "Child"}]}])
    with Application() as app:
        with pytest.raises(TypeError, match="does not accept"):
            Checkbox(children=[Label("Unparented")])
    assert len(app.children) == 1 and isinstance(app.children[0], Label)
    with pytest.raises(ValueError, match="one dialog"):
        Bridge(json.dumps([Dialog()._spec(), Dialog()._spec()]))
