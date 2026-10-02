import asyncio
import threading

import pytest

from gpyui import Application, Button, Column, Label, State, TextInput


def test_explicit_and_context_composition():
    explicit = Column([Label("First"), TextInput("Ada"), Button("Greet")])
    with Application() as app:
        with Column() as contextual:
            Label("First")
            TextInput("Ada")
            Button("Greet")
    assert app.children == (contextual,)
    assert [type(c) for c in explicit.children] == [type(c) for c in contextual.children]
    explicit_input, contextual_input = explicit.children[1], contextual.children[1]
    assert isinstance(explicit_input, TextInput) and isinstance(contextual_input, TextInput)
    assert explicit_input.value == contextual_input.value == "Ada"
    assert len({c.id for c in (*explicit.children, *contextual.children)}) == 6


def test_context_restored_after_exception():
    with Application() as app:
        with pytest.raises(ValueError):
            with Column() as column:
                raise ValueError("leave scope")
        label = Label("Sibling")
    assert app.children == (column, label)
    assert column.children == ()


def test_async_composition_keeps_task_stacks_separate():
    async def compose(title):
        with Application() as app:
            with Column() as column:
                await asyncio.sleep(0)
                label = Label(title)
        assert column.children == (label,)
        return app

    async def run():
        return await asyncio.gather(compose("A"), compose("B"))

    first, second = asyncio.run(run())
    assert first.children[0].children[0].text == "A"
    assert second.children[0].children[0].text == "B"


def test_control_cannot_be_owned_twice_or_form_cycle():
    label = Label("Once")
    Column([label])
    with pytest.raises(ValueError, match="one parent"):
        Application(label)
    column = Column()
    nested = Column()
    column.add(nested)
    with pytest.raises(ValueError, match="cycle"):
        nested.add(column)


def test_two_way_binding_and_disposal():
    state = State("Ada")
    field = TextInput().bind_value(state)
    label = Label().bind_text(state, lambda value: f"Hello, {value}")
    assert field.value == "Ada"
    assert label.text == "Hello, Ada"
    field.value = "Grace"
    assert state.value == "Grace"
    assert label.text == "Hello, Grace"
    state.value = "Lin"
    assert field.value == "Lin"
    field.unbind()
    label.unbind()
    state.value = "Disconnected"
    assert field.value == "Lin"
    assert label.text == "Hello, Lin"
    field.value = "Independent"
    assert state.value == "Disconnected"


def test_state_equality_and_unsubscribe():
    state = State(1)
    observed = []
    unsubscribe = state.subscribe(observed.append)
    state.value = 1
    state.value = 2
    unsubscribe()
    unsubscribe()
    state.value = 3
    assert observed == [2]


@pytest.mark.parametrize(
    "construct",
    [
        lambda: Label(1),  # ty: ignore[invalid-argument-type] -- exercise runtime validation
        lambda: TextInput(placeholder=1),  # ty: ignore[invalid-argument-type]
        lambda: Button("Go", disabled=1),  # ty: ignore[invalid-argument-type]
        lambda: Button("Go", on_click=1),  # ty: ignore[invalid-argument-type]
    ],
)
def test_invalid_control_properties_fail_early(construct):
    with pytest.raises(TypeError):
        construct()


def test_invalid_handler_arity_fails_at_registration():
    with pytest.raises(TypeError):
        Button("Go", on_click=lambda a, b: None)


def test_failed_handler_registration_does_not_attach_a_control():
    with Application() as app:
        with pytest.raises(TypeError):
            Button("Go", on_click=lambda a, b: None)
        with pytest.raises(TypeError):
            TextInput(on_change=42)  # ty: ignore[invalid-argument-type] -- invalid callback test
    assert app.children == ()


def test_run_requires_main_thread_before_native_import():
    errors = []

    def run():
        try:
            Application().run()
        except RuntimeError as error:
            errors.append(str(error))

    thread = threading.Thread(target=run)
    thread.start()
    thread.join()
    assert errors == ["Application.run() must be called on the main thread"]


def test_run_rejects_existing_asyncio_loop():
    async def run():
        with pytest.raises(RuntimeError, match="outside an existing asyncio loop"):
            Application().run()

    asyncio.run(run())


@pytest.mark.parametrize("width,height", [(0, 300), (480, 0), (float("nan"), 300), (480, float("inf"))])
def test_window_size_validation(width, height):
    with pytest.raises(ValueError):
        Application(width=width, height=height)
