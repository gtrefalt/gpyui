"""Run one catalog specimen in a real GPUI window."""

import argparse
import asyncio
import json
import threading
from pathlib import Path

from component_catalog import SAMPLES, specimen

import gpyui as ui


def create_preview(name, theme="dark", *, state_dir=None):
    control, roots = specimen(name)

    def write(name, data):
        if state_dir is not None:
            state_dir.mkdir(parents=True, exist_ok=True)
            path = state_dir / f"{name}.json"
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data))
            temporary.replace(path)

    async def started(event):
        if SAMPLES[name].action == "overlay":
            control.open()
        await asyncio.sleep(0.15)
        write("ready", await event.sender.snapshot())

    def error(exc):
        write("error", {"type": type(exc).__name__, "message": str(exc)})
        app.close()

    app = ui.Application(
        ui.Column(
            [
                ui.Label(name).style(font_size=24, bold=True),
                ui.Label("Native GPUI Kit · Python composition").style(
                    color="muted_foreground", font_size=13
                ),
                ui.Separator(),
                *roots.values(),
            ]
        ).style(full_width=True, gap=16),
        title=f"gpyui component {name}",
        width=640,
        height=SAMPLES[name].height,
        theme=theme,
        on_start=started,
        on_error=error,
    )
    return app, write


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("component", choices=SAMPLES)
    parser.add_argument("--theme", choices=("light", "dark"), default="dark")
    parser.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    app, write = create_preview(args.component, args.theme, state_dir=args.state_dir)
    app.run()
    write(
        "closed",
        {
            "errors": [str(error) for error in app.errors],
            "threads": [thread.name for thread in threading.enumerate()],
        },
    )
