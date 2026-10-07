"""Real-window fixture for retained tables, inputs and command search."""

import asyncio
import json
import sys
from pathlib import Path

import gpyui as ui

path, mode = Path(sys.argv[1]), sys.argv[2]
calls = []


def write(name, value):
    target = path / f"{name}.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(value))
    temporary.replace(target)


def execute():
    calls.append({"input": field.value, "query": palette.query})
    write(f"executed-{len(calls)}", calls[-1])


async def start():
    if mode == "table":
        table.sort(1)
    write(
        "ready",
        {"ids": {name: control.id for name, control in controls.items()}, "snapshot": await app.snapshot()},
    )
    while True:
        file = path / "command.json"
        if file.exists():
            data = json.loads(file.read_text())
            file.unlink()
            with app.batch():
                action = data["action"]
                if action == "replace":
                    table.rows = [ui.TableRow("b", ("Two", 2)), ui.TableRow("c", ("Thirty", 30))]
                elif action == "filter":
                    table.filter = "Two"
                elif action == "enable":
                    save.enabled = True
                elif action == "disable":
                    save.enabled = False
                elif action == "options":
                    choice.items = ["b", "c"]
                elif action == "select":
                    choice.value = ["b", "c"]
                elif action == "query":
                    palette.query = ""
                elif action != "snapshot":
                    raise ValueError(action)
            snapshot = await app.snapshot()
            write(
                data["name"],
                {
                    "snapshot": snapshot,
                    "calls": calls,
                    "key": table.selected_key if mode == "table" else None,
                },
            )
        await asyncio.sleep(0.02)


app = ui.Application(title=f"gpyui data inputs commands {mode}", width=660, height=430, on_start=start)
controls = {}
with app, ui.Column().style(gap=16):
    if mode == "table":
        table = ui.Table(
            columns=[
                ui.TableColumn("Name", width=240),
                ui.TableColumn("Quantity", width=220, sort_type="number"),
            ],
            rows=[
                ui.TableRow("a", ("Ten", 10)),
                ui.TableRow("b", ("Two", 2)),
                ui.TableRow("c", ("Thirty", 30)),
            ],
            sortable=True,
            on_sort=lambda event: write("sorted", event.value),
        ).style(height=220, width=560)
        controls["table"] = table
    elif mode == "inputs":
        field = ui.TextInput(
            "secret",
            password=True,
            prefix="Account",
            clearable=True,
            on_submit=lambda event: write("submitted", event.value),
            on_focus=lambda: write("focused", True),
            on_blur=lambda: write("blurred", True),
        ).style(width=500)
        fixed = ui.TextInput("fixed", read_only=True).style(width=500)
        number = ui.NumberInput("1.5", minimum=0, maximum=2, step=0.5).style(width=500)
        controls.update(field=field, fixed=fixed, number=number)
    elif mode == "palette":
        field = ui.TextInput("Ada").style(width=500)
        save = ui.Command("Save document", execute, shortcut="mod+s", enabled=False)
        other = ui.Command("Open document", lambda: write("opened", field.value), shortcut="mod+o")
        palette = ui.CommandPalette(
            [save, other],
            on_query=lambda event: write("query", event.value),
            on_cancel=lambda: write("cancelled", True),
        ).style(width=500)
        controls.update(field=field, palette=palette)
    elif mode == "multi":
        choice = ui.MultiSelect(["a", "b", "c"], value=["a", "b"]).style(width=500)
        controls["choice"] = choice
    else:
        raise ValueError(mode)
app.run()
write("closed", {"errors": [str(error) for error in app.errors]})
