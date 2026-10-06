"""Fixed-size native editor with live title and programmatic sizing.

Run: uv run python examples/window_controls.py
"""

from gpyui import Application, Button, Column, Label, Row, TextInput, Theme


def build_app():
    app = Application(
        title="Window controls",
        width=560,
        height=360,
        resizable=False,
        min_width=400,
        min_height=280,
        theme=Theme("macos"),
    )
    expanded = False

    async def resize():
        nonlocal expanded
        expanded = not expanded
        app.title = "Window controls — expanded" if expanded else "Window controls"
        app.resize(720 if expanded else 560, 460 if expanded else 360)
        requested.text = f"Requested: {app.width:g} × {app.height:g}"
        current = await app.window_snapshot()
        status.text = f"Native snapshot: {current['width']:g} × {current['height']:g}"

    with app, Column().style(gap=12):
        Label("A fixed-size settings window").style(font_size=22)
        Label("Display name")
        TextInput("Sam Taylor")
        requested = Label("Requested: 560 × 360")
        status = Label("Editing stays intact when the window changes").style(color="muted")
        with Row().style(gap=8):
            Button("Change size", on_click=resize)
            Button("Fullscreen", on_click=app.toggle_fullscreen)
            Button("Minimize", on_click=app.minimize)
    return app


if __name__ == "__main__":
    build_app().run()
