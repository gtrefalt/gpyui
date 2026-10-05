"""A light native notes editor with shared commands, menus and shortcuts.

Run: uv run python examples/notes.py --file notes.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path

from gpyui import (
    Application,
    ApplicationClosedError,
    Button,
    Column,
    Command,
    DropdownMenu,
    Label,
    Menu,
    MenuSeparator,
    Row,
    Separator,
    TextArea,
)

DEFAULT_TEXT = "Project notes\n\nCapture an idea, then choose Save or press the save shortcut.\n\n• Keep the first version focused.\n• Preserve the editor when changing the layout.\n• Use the same command from buttons, menus and the keyboard.\n"


def build_app(path: Path):
    """Construct without opening a window or writing a file."""
    modifier = "Command" if sys.platform == "darwin" else "Ctrl"
    text = path.read_text(encoding="utf-8") if path.exists() else DEFAULT_TEXT
    editor = TextArea(text, placeholder="Write a note…").style(full_width=True, flex=1, min_height=220)
    status = Label("Ready · Changes are saved when you choose Save.").style(
        color="muted_foreground", font_size=13
    )

    async def save():
        # Capture this activation's value before another edit can arrive.
        content = editor.value
        with app.batch():
            save_command.enabled = False
            status.text = "Saving…"
        try:
            await asyncio.to_thread(path.write_text, content, encoding="utf-8")
            status.text = f"Saved to {path.name}."
        except OSError as error:
            status.text = f"Could not save {path.name}: {error}. Choose Save to retry."
        finally:
            try:
                save_command.enabled = True
            except ApplicationClosedError:
                pass  # Closing the native window cancels the callback.

    def toggle_sidebar():
        with app.batch():
            sidebar.visible = not sidebar.visible
            sidebar_command.checked = sidebar.visible

    save_command = Command("Save", save, shortcut="mod+s")
    sidebar_command = Command("Show sidebar", toggle_sidebar, shortcut="mod+shift+b", checked=True)
    app = Application(
        title="Notes · gpyui",
        width=860,
        height=580,
        theme="light",
        menus=[Menu("File", [save_command]), Menu("View", [sidebar_command])],
    )
    editor.context_menu([save_command, MenuSeparator(), sidebar_command])
    with app, Column().style(full_width=True, full_height=True, gap=16, flex=1) as workspace:
        with Row().style(full_width=True, justify="between", align="center"):
            with Column().style(gap=4):
                Label("Notes").style(font_size=24, bold=True)
                Label(path.name).style(color="muted_foreground", font_size=13)
            with Row().style(gap=8):
                Button(command=save_command, variant="primary", icon="save")
                DropdownMenu("More", [save_command, MenuSeparator(), Menu("View", [sidebar_command])])
        Separator().style(full_width=True)
        with Row().style(full_width=True, flex=1, gap=24, align="stretch"):
            with Column().style(width=190, gap=12, padding=16, background="muted", radius=8) as sidebar:
                Label("WORKSPACE").style(font_size=12, bold=True, color="muted_foreground")
                Label("Project notes").style(bold=True)
                Label("One document.\nOne shared Save command.").style(font_size=13, color="muted_foreground")
                Label("SHORTCUTS").style(font_size=12, bold=True, color="muted_foreground")
                Label(f"Save: {modifier}+S\nSidebar: {modifier}+Shift+B").style(
                    font_size=12, color="muted_foreground"
                )
            with Column().style(full_width=True, flex=1, gap=8) as document:
                Label("Document").style(bold=True)
                # The same retained editor is used when the sidebar is hidden.
                document.add(editor)
        # Controls constructed before entering a context can be attached explicitly.
        workspace.add(status)
    return app, {
        "editor": editor,
        "status": status,
        "save": save_command,
        "sidebar": sidebar,
        "toggle": sidebar_command,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=Path("notes.txt"))
    args = parser.parse_args()
    app, _ = build_app(args.file)
    app.run()
