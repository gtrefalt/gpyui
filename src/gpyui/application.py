from __future__ import annotations

import asyncio
import inspect
import itertools
import json
import math
import threading
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

from .commands import Command, DropdownMenu, Menu, menu_commands, menu_specs, validate_items
from .controls import Column, Control, Event, Handler, _containers
from .tree import walk

if TYPE_CHECKING:
    from .controls import TextInput
    from .widgets import KitControl


class ApplicationClosedError(RuntimeError):
    """The native application has closed or has not started."""


class Application:
    """One native window with an owned Python asyncio callback thread.

    Call run() on the main thread. Callbacks run on the owned asyncio loop;
    call_soon() marshals work from other Python threads. Native startup is
    currently one run per process. Structural updates retain controls by ID.
    """

    def __init__(
        self,
        *controls: Control,
        title: str = "gpyui",
        width: float = 480,
        height: float = 300,
        theme: str = "light",
        commands: Iterable[Command] = (),
        menus: Iterable[Menu] = (),
        on_start: Callable[..., Any] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ):
        if not isinstance(title, str):
            raise TypeError("title requires str")
        if theme not in {"light", "dark"}:
            raise ValueError("theme requires 'light' or 'dark'")
        self.theme = theme
        if not math.isfinite(width) or not math.isfinite(height) or width < 240 or height < 160:
            raise ValueError("window size must be finite and at least 240 x 160")
        self.title, self.width, self.height = title, width, height
        self._children: list[Control] = []
        self._controls: dict[int, Control] = {}
        self._phase = "new"
        self._pending: dict[tuple[int, str], Any] = {}
        self._tree_dirty = False
        self._actions_dirty = False
        self._commands: dict[int, Command] = {}
        self._menus: tuple[Menu, ...] = ()
        self._batch_depth = 0
        self._flush_scheduled = False
        self._bridge: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._worker_ident: int | None = None
        self._startup = Handler(on_start) if on_start is not None else None
        self._on_error = on_error
        self._tasks: set[asyncio.Task[None]] = set()
        self._snapshots: dict[int, asyncio.Future[dict[int, dict[str, Any]]]] = {}
        self._tokens = itertools.count(1)
        self._errors: list[Exception] = []
        self.add_command(*commands)
        self.menus = menus
        self.add(*controls)

    @property
    def children(self) -> tuple[Control, ...]:
        return tuple(self._children)

    @children.setter
    def children(self, controls: Iterable[Control]) -> None:
        self.set_children(controls)

    @property
    def commands(self) -> tuple[Command, ...]:
        return tuple(self._commands.values())

    @property
    def menus(self) -> tuple[Menu, ...]:
        return self._menus

    @menus.setter
    def menus(self, menus: Iterable[Menu]) -> None:
        value = validate_items(menus)
        if any(not isinstance(menu, Menu) for menu in value):
            raise TypeError("application menus require Menu roots")
        if self._phase != "new":
            self._check_mutation()
        self._register_commands(menu_commands(value))
        self._menus = cast("tuple[Menu, ...]", value)
        if self._phase != "new":
            self._actions_dirty = True
            self._schedule_flush()

    def add_command(self, *commands: Command) -> Application:
        if self._phase != "new":
            self._check_mutation()
        self._register_commands(commands)
        return self

    def _validate_commands(self, commands: Iterable[Command]) -> dict[int, Command]:
        combined = dict(self._commands)
        for command in commands:
            if not isinstance(command, Command):
                raise TypeError("commands require Command")
            combined[command.id] = command
        keys = {}
        for command in combined.values():
            if command._app is not None and command._app is not self:
                raise ValueError("a command can belong to only one application")
            if command._key:
                if command._key in keys and keys[command._key] != command.id:
                    raise ValueError(f"duplicate shortcut: {command.shortcut}")
                keys[command._key] = command.id
        if len(combined) > 1024:
            raise ValueError("application exceeds 1,024 registered commands")
        return combined

    def _register_commands(self, commands: Iterable[Command]) -> None:
        combined = self._validate_commands(commands)
        changed = combined.keys() != self._commands.keys()
        self._commands = combined
        if self._phase != "new":
            for command in combined.values():
                command._app = self
            if changed:
                self._actions_dirty = True
                self._schedule_flush()

    def _control_commands(self, control: Control) -> Iterator[Command]:
        if command := getattr(control, "_command", None):
            yield command
        if isinstance(control, DropdownMenu):
            yield from menu_commands(control.items)
        yield from menu_commands(control._context_items or ())

    def _config(self) -> dict[str, Any]:
        return {"commands": [command._spec() for command in self.commands], "menus": menu_specs(self.menus)}

    @property
    def errors(self) -> tuple[Exception, ...]:
        return tuple(self._errors)

    def add(self, *controls: Control) -> Application:
        return self.set_children((*self._children, *controls))

    def set_children(self, controls: Iterable[Control]) -> Application:
        from .tree import set_children

        set_children(self, controls)
        return self

    def insert(self, index: int, control: Control) -> Application:
        children = list(self.children)
        children.insert(index, control)
        return self.set_children(children)

    def remove(self, *controls: Control) -> Application:
        if any(control not in self._children for control in controls):
            raise ValueError("control is not an application root")
        return self.set_children(control for control in self._children if control not in controls)

    def clear(self) -> Application:
        return self.set_children(())

    def _register(self, control: Control) -> None:
        for node in walk(control):
            node._app = self
            self._controls[node.id] = node
            self._register_commands(self._control_commands(node))

    def _validate_tree_change(self, parent: Column | Application, children: tuple[Control, ...]) -> None:
        roots = children if parent is self else self.children
        active: dict[int, Control] = {}

        def visit(control: Control, depth: int) -> None:
            if depth > 64:
                raise ValueError("control tree exceeds 64 levels")
            if control.id in active:
                raise ValueError("a control can have only one parent")
            control._ensure_alive()
            active[control.id] = control
            if isinstance(control, Column):
                for child in children if control is parent else control.children:
                    visit(child, depth + 1)

        for root in roots:
            visit(root, 0)
        self._validate_commands(
            command for node in active.values() for command in self._control_commands(node)
        )
        owned = set(self._controls) | set(active)
        for child in children:
            owned.update(node.id for node in walk(child))
        if len(owned) > 10_000:
            raise ValueError("application exceeds 10,000 retained controls; dispose detached controls")
        for kind in ("dialog", "sheet"):
            if sum(getattr(node, "native", None) == kind for node in active.values()) > 1:
                raise ValueError(f"one {kind} per window is currently supported")
        # Detached forests still cross the bridge and must obey its depth bound.
        for control in self._controls.values():
            if control._parent is None and control.id not in active:
                visit(control, 0)

    def _forests(self) -> list[dict[str, Any]]:
        roots = [*self.children, *(control for control in self._controls.values() if control._parent is None)]
        return [control._spec() for control in roots]

    def _schedule_flush(self) -> None:
        if not self._batch_depth and not self._flush_scheduled:
            self._flush_scheduled = True
            assert self._loop is not None
            self._loop.call_soon(self._auto_flush)

    def __enter__(self) -> Application:
        _containers.set((*_containers.get(), self))
        return self

    def __exit__(self, *_: Any) -> None:
        stack = _containers.get()
        if not stack or stack[-1] is not self:
            raise RuntimeError("unbalanced application context")
        _containers.set(stack[:-1])

    def _check_mutation(self) -> None:
        if self._phase not in {"starting", "running"}:
            raise ApplicationClosedError("application is closed")
        if threading.get_ident() != self._worker_ident:
            raise RuntimeError("mutate controls on the callback loop; use app.call_soon() from other threads")

    def _queue(self, control_id: int, name: str, value: Any) -> None:
        self._pending[(control_id, name)] = value
        self._schedule_flush()

    def _auto_flush(self) -> None:
        self._flush_scheduled = False
        if self._phase in {"starting", "running"} and not self._batch_depth:
            try:
                self.update()
            except Exception as error:
                self._report(error)

    def update(self) -> None:
        """Submit coalesced properties and children. Await snapshot() to observe applied state."""
        self._check_mutation()
        if self._pending or self._tree_dirty or self._actions_dirty:
            patches = [
                {"id": control_id, "property": name, "value": value}
                for (control_id, name), value in self._pending.items()
            ]
            if self._tree_dirty or self._actions_dirty:
                self._bridge.reconcile(
                    json.dumps(self._forests()),
                    json.dumps([control.id for control in self.children]),
                    json.dumps(patches),
                    json.dumps(self._config()),
                )
            else:
                self._bridge.submit(json.dumps(patches))
            self._pending.clear()
            self._tree_dirty = False
            self._actions_dirty = False

    @contextmanager
    def batch(self) -> Iterator[None]:
        """Coalesce synchronous mutations into one batch; this is not rollback."""
        self._check_mutation()
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if not self._batch_depth and self._phase in {"starting", "running"}:
                self.update()

    async def snapshot(self) -> dict[int, dict[str, Any]]:
        """Flush and await native state after preceding commands (not GPU presentation)."""
        self._check_mutation()
        self.update()
        token = next(self._tokens)
        future = asyncio.get_running_loop().create_future()
        self._snapshots[token] = future
        try:
            self._bridge.snapshot(token)
            return await future
        finally:
            self._snapshots.pop(token, None)

    def close(self) -> None:
        """Request native shutdown, flushing pending properties first."""
        self._check_mutation()
        self.update()
        self._bridge.close()

    def notify(self, message: str, *, title: str = "", variant: str = "info") -> None:
        """Queue a native Kit notification on the callback loop."""
        from .widgets import choice, text

        self._check_mutation()
        message, title = text(message), text(title)
        variant = choice("info", "success", "warning", "danger")(variant)
        self.update()
        self._bridge.notify(message, title, variant)

    def call_soon(self, callback: Callable[..., Any], *args: Any) -> None:
        """Schedule a short synchronous callback from any Python thread."""
        if self._phase not in {"starting", "running"} or self._loop is None:
            raise ApplicationClosedError("application is not running")

        def invoke() -> None:
            if self._phase in {"starting", "running"}:
                try:
                    callback(*args)
                except Exception as error:
                    self._report(error)

        self._loop.call_soon_threadsafe(invoke)

    def _report(self, error: Exception) -> None:
        self._errors.append(error)
        assert self._loop is not None
        if self._on_error:
            try:
                self._on_error(error)
            except Exception as reporting_error:
                self._errors.append(reporting_error)
                self._loop.call_exception_handler(
                    {"message": "gpyui on_error failed", "exception": reporting_error}
                )
        else:
            self._loop.call_exception_handler({"message": "gpyui callback failed", "exception": error})

    def _dispatch(self, handler: Handler, event: Event) -> None:
        async def invoke() -> None:
            token = _containers.set(())  # Each callback starts with an independent composition context.
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as error:
                self._report(error)
            finally:
                _containers.reset(token)
                if self._phase in {"starting", "running"}:
                    try:
                        self.update()
                    except Exception as error:
                        self._report(error)

        task = asyncio.create_task(invoke())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _events(self, started: threading.Event) -> None:
        self._loop = asyncio.get_running_loop()
        self._worker_ident = threading.get_ident()
        started.set()
        try:
            while True:
                events = json.loads(await asyncio.to_thread(self._bridge.next_events))
                for event in events:
                    name = event["event"]
                    if name == "closed":
                        return
                    if name == "ready":
                        self._phase = "running"
                        if self._startup:
                            self._dispatch(self._startup, Event(self, "start"))
                    elif name == "snapshot":
                        future = self._snapshots.get(event["token"])
                        if future is not None and not future.done():
                            future.set_result({int(k): v for k, v in event["nodes"].items()})
                    elif name == "command":
                        command = self._commands.get(event["id"])
                        if command is None or not command.enabled:
                            continue
                        source = event.get("source")
                        if source is not None:
                            control = self._controls.get(source)
                            if control is None or not control._is_displayed():
                                continue
                        for control_id, value in event.get("values", {}).items():
                            if mirrored := self._controls.get(int(control_id)):
                                cast("TextInput | KitControl", mirrored)._receive_native(value)
                        self._dispatch(command._handler, Event(command, "command"))
                        await asyncio.sleep(0)
                    elif name in {"click", "change", "release", "resize"}:
                        control = self._controls.get(event["id"])
                        if control is None:
                            continue
                        # Rust includes values only for native input/Kit controls.
                        for control_id, value in event.get("values", {}).items():
                            if mirrored := self._controls.get(int(control_id)):
                                cast("TextInput | KitControl", mirrored)._receive_native(value)
                        if name == "change":
                            cast("TextInput | KitControl", control)._receive_native(event["value"])
                        if not control._is_displayed():
                            continue
                        if handler := control._handlers.get(name):
                            self._dispatch(handler, Event(control, name, event.get("value")))
                            # Begin this callback with its activation snapshot before
                            # later queued input events advance the Python mirrors.
                            await asyncio.sleep(0)
        finally:
            self._phase = "closed"
            for future in self._snapshots.values():
                if not future.done():
                    future.set_exception(ApplicationClosedError("native window closed"))
            tasks = tuple(self._tasks)
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    def run(self) -> None:
        """Block the main thread in GPUI, with Python callbacks on an asyncio worker."""
        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("Application.run() must be called on the main thread")
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            raise RuntimeError("run() owns the native main loop; call it outside an existing asyncio loop")
        if self._phase != "new":
            raise RuntimeError("Application.run() can only be called once")
        from ._core import Bridge

        commands = self._validate_commands(
            command
            for root in self.children
            for node in walk(root)
            for command in self._control_commands(node)
        )
        config = {
            "commands": [command._spec() for command in commands.values()],
            "menus": menu_specs(self.menus),
        }
        # Validate the native contract before claiming controls or committing the
        # discovered commands. A failed start leaves the unmounted tree editable.
        self._bridge = Bridge(json.dumps([c._spec() for c in self.children]), json.dumps(config))
        self._commands = commands
        for control in self.children:
            self._register(control)
        self._phase = "starting"
        for command in self.commands:
            command._app = self
        started = threading.Event()
        worker_failures: list[BaseException] = []

        def worker_main() -> None:
            try:
                asyncio.run(self._events(started))
            except BaseException as error:
                worker_failures.append(error)
                self._bridge.close()

        worker = threading.Thread(target=worker_main, name="gpyui-asyncio", daemon=True)
        worker.start()
        try:
            if not started.wait(5):
                raise RuntimeError("Python callback loop failed to start")
            self._bridge.run(self.title, self.width, self.height, self.theme)
        finally:
            self._bridge.finish()
            worker.join(timeout=5)
            self._phase = "closed"
            for control in self._controls.values():
                control.unbind()
            for command in self.commands:
                command.unbind()
            if worker.is_alive():
                raise RuntimeError("Python callback did not stop; synchronous handlers must not block")
        if worker_failures:
            raise RuntimeError("Python callback loop failed") from worker_failures[0]
