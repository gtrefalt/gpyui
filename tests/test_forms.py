"""Validate business/lifecycle contracts without a native window."""

import asyncio

import pytest
from test_dynamic import mounted

from gpyui import (
    Application,
    ApplicationClosedError,
    Button,
    Checkbox,
    Field,
    Form,
    Label,
    Row,
    Slider,
    State,
    TextInput,
    ValidationError,
)


def make_form(value="Ada", **kwargs):
    editor = TextInput(value)
    field = Field("Name", name="name", control=editor, required=True)
    return Form(children=[field], **kwargs), field, editor


def test_context_composition_shared_command_and_atomic_field_ownership():
    with Form(shortcut="mod+s") as form:
        with Field("Name", name="name", required=True) as field:
            editor = TextInput("Ada")
    assert field.control is editor and form.values() == {"name": "Ada"}
    button = Button(command=form.submit_command)
    app = Application(form, button)
    assert form._spec()["kind"] == "form" and field._spec()["kind"] == "field"
    other = Field("Other", name="name", control=TextInput())
    with pytest.raises(ValueError, match="unique"):
        form.add(other)
    assert other._parent is None and form.children == (field,)
    with pytest.raises(TypeError, match="Field"):
        form.add(Label("Invalid"))
    with pytest.raises(ValueError, match="nonempty"):
        form.add(Field("Unnamed"))
    with pytest.raises(AttributeError):
        field.name = "changed"
    assert button._command is form.submit_command and button in app.children


def test_required_indicators_validation_and_metadata_keep_values():
    async def scenario():
        form, field, editor = make_form("  ")
        state = State("  ")
        editor.bind_value(state)
        assert not await form.validate()
        assert form.errors == {"name": "This field is required."}
        assert form.error and editor.value == "  " and state.value == "  "
        editor.value = "Grace"
        assert await form.validate() and not form.errors and not form.error
        assert form.submit_command.enabled and not form.busy
        field.help = "Visible help"
        field.error = "Server error"
        form.clear_errors()
        assert field.help == "Visible help" and form.errors == {}

    asyncio.run(scenario())


@pytest.mark.parametrize("value,valid", [(False, False), (True, True), ("", False), (0, True), ("0", True)])
def test_required_boolean_and_numeric_zero(value, valid):
    async def scenario():
        control = (
            Checkbox(value=value)
            if isinstance(value, bool)
            else TextInput(str(value))
            if isinstance(value, str)
            else Slider(value=value)
        )
        form = Form(children=[Field("Value", name="value", control=control, required=True)])
        assert await form.validate() is valid

    asyncio.run(scenario())


def test_sync_async_validators_first_error_and_raw_numeric_text():
    async def scenario():
        calls = []

        async def length(value):
            await asyncio.sleep(0)
            calls.append(value)
            return "Use three characters." if len(value) < 3 else None

        def stop(value):
            raise ValueError("Unavailable")

        editor = TextInput("12")
        field = Field("Code", name="code", control=editor, validators=[length, stop])
        form = Form(children=[field])
        assert not await form.validate() and field.error == "Use three characters."
        assert calls == ["12"]
        editor.value = "123"
        assert not await form.validate() and field.error == "Unavailable"
        assert form.values() == {"code": "123"}

    asyncio.run(scenario())


@pytest.mark.parametrize("result", [False, True, 1, [], {}])
def test_bad_validator_results_are_programming_errors_and_restore_command(result):
    async def scenario():
        form = Form(
            children=[Field("Name", name="name", control=TextInput("Ada"), validators=[lambda value: result])]
        )
        with pytest.raises(TypeError, match="validators must return"):
            await form.submit()
        assert not form.busy and form.submit_command.enabled

    asyncio.run(scenario())


def test_bad_control_and_bad_validator_signatures_do_not_leave_busy():
    async def scenario():
        form = Form(children=[Field("Name", name="name", children=[Label("No value")])])
        with pytest.raises(ValueError, match="one bindable"):
            await form.submit()
        assert not form.busy and form.submit_command.enabled
        with pytest.raises(TypeError):
            Field(validators=[lambda left, right: None])  # ty: ignore[invalid-argument-type]

    asyncio.run(scenario())


def test_nested_editor_and_conditional_fields_retain_values_but_skip_submission():
    async def scenario():
        seen = []
        name = TextInput("Ada")
        mail = TextInput("")
        mail_field = Field("Mail", name="mail", control=mail, required=True)
        form = Form(
            on_submit=lambda values: seen.append(values),
            children=[Field("Name", name="name", children=[Row([name, Label("Hint")])]), mail_field],
        )
        mail_field.visible = False
        assert await form.submit() and seen == [{"name": "Ada"}]
        mail.value = "typed@localhost"
        mail_field.visible = True
        assert await form.submit() and seen[-1]["mail"] == "typed@localhost"
        parent = Row([form])
        parent.visible = False
        assert form.values() == {} and not await form.submit()
        assert mail.value == "typed@localhost"

    asyncio.run(scenario())


@pytest.mark.parametrize("mutation", ["value", "visibility", "replacement", "required"])
def test_async_validation_never_applies_stale_errors_or_saves(mutation):
    async def scenario():
        started, resume = asyncio.Event(), asyncio.Event()
        saved = []

        async def check(value):
            started.set()
            await resume.wait()
            return "Old error"

        editor = TextInput("Ada")
        field = Field("Name", name="name", control=editor, validators=[check])
        form = Form(on_submit=lambda values: saved.append(values), children=[field])
        pending = asyncio.create_task(form.submit())
        await started.wait()
        if mutation == "value":
            editor.value = "Grace"
        elif mutation == "visibility":
            field.visible = False
        elif mutation == "required":
            field.required = True
        else:
            field.clear()
            field.add(TextInput("Grace"))
        resume.set()
        assert not await pending and not field.error and not saved
        assert "changed" in form.error and form.submit_command.enabled

    asyncio.run(scenario())


def test_async_submission_single_flight_copied_values_and_io_retry():
    async def scenario():
        entered, resume = asyncio.Event(), asyncio.Event()
        seen = []

        async def save(values):
            seen.append(values.copy())
            entered.set()
            await resume.wait()
            values["name"] = "Payload mutation"
            if len(seen) == 1:
                raise OSError("Offline. Retry saving.")

        form, _, editor = make_form(on_submit=save)
        pending = asyncio.create_task(form.submit())
        await entered.wait()
        assert form.busy and not form.submit_command.enabled
        assert not await form.submit() and not await form.validate()
        editor.value = "Grace"
        resume.set()
        assert not await pending and form.error == "Offline. Retry saving."
        assert editor.value == "Grace" and form.submit_command.enabled
        assert await form.submit() and seen == [{"name": "Ada"}, {"name": "Grace"}]
        assert editor.value == "Grace" and not form.error

    asyncio.run(scenario())


def test_submission_field_errors_and_unexpected_exceptions():
    async def scenario():
        def save(values):
            raise ValidationError({"name": "Already taken."})

        form, field, editor = make_form(on_submit=save)
        assert not await form.submit() and field.error == "Already taken." and editor.value == "Ada"

        def broken():
            raise TypeError("Programming error")

        form, _, _ = make_form(on_submit=broken)
        with pytest.raises(TypeError, match="Programming"):
            await form.submit()
        assert form.submit_command.enabled and not form.busy

    asyncio.run(scenario())


def test_cancellation_restores_busy_and_command_without_turning_into_error():
    async def scenario():
        entered = asyncio.Event()

        async def save(values):
            entered.set()
            await asyncio.Event().wait()

        form, _, _ = make_form(on_submit=save)
        pending = asyncio.create_task(form.submit())
        await entered.wait()
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert not form.busy and form.submit_command.enabled and not form.error

    asyncio.run(scenario())


def test_mounted_validation_patches_metadata_only_and_lifecycle_restrictions():
    async def scenario():
        form, field, editor = make_form("")
        app = Application(form, Button(command=form.submit_command))
        bridge = mounted(app)
        bridge.calls.clear()
        assert not await form.submit()
        app.update()
        patches = [
            patch for call in bridge.calls for patch in (call[3] if call[0] == "reconcile" else call[1])
        ]
        assert any(patch["id"] == field.id and patch["property"] == "error" for patch in patches)
        assert not any(patch["id"] == editor.id for patch in patches)
        assert all(patch["property"] in {"error", "enabled"} for patch in patches)
        with pytest.raises(RuntimeError, match="callback loop"):
            await asyncio.to_thread(form.values)
        app._phase = "closed"
        with pytest.raises(ApplicationClosedError):
            await form.submit()

    asyncio.run(scenario())
