"""Native presets with live switching and retained editing controls.

Run: uv run python examples/appearance.py --theme macos --mode light
"""

import argparse

from gpyui import (
    Application,
    Button,
    Checkbox,
    Column,
    Label,
    Row,
    Select,
    Separator,
    Slider,
    Switch,
    Tag,
    TextArea,
    TextInput,
    Theme,
)

PRESETS = {
    "macOS": "macos",
    "Windows": "windows",
    "Shadcn Zinc": "shadcn-zinc",
    "Shadcn Blue": "shadcn-blue",
    "Kit default": "default",
}


def build_app(preset="macos", mode="light", *, on_start=None):
    """Construct the preview; changing appearance never reconstructs its inputs."""
    app = Application(
        title="Appearance · gpyui", width=820, height=660, theme=Theme(preset, mode=mode), on_start=on_start
    )

    def apply_theme():
        app.theme = Theme(PRESETS[theme_select.value], mode="dark" if dark.value else "light")
        status.text = f"{theme_select.value} · {app.theme.mode.title()} appearance"

    def notify():
        app.notify("Your native controls use the selected theme.", title="Appearance", variant="success")

    with app, Column().style(full_width=True, full_height=True, gap=20):
        with Row().style(full_width=True, justify="between", align="center"):
            with Column().style(gap=4):
                Label("Appearance").style(font_size=26, bold=True)
                Label("Choose a native theme. Your edits stay intact.").style(color="muted_foreground")
            Tag("Live preview", variant="secondary")
        Separator().style(full_width=True)
        with Row().style(full_width=True, flex=1, gap=28, align="stretch"):
            with Column().style(width=210, gap=14):
                Label("THEME").style(bold=True, font_size=12, color="muted_foreground")
                theme_select = Select(
                    items=list(PRESETS),
                    value=next(name for name, key in PRESETS.items() if key == preset),
                    on_change=apply_theme,
                ).style(full_width=True)
                dark = Switch("Dark appearance", value=mode == "dark", on_change=apply_theme)
                Label(
                    "Control sizes, surfaces and\ntypography follow the preset.\nEditing stays native."
                ).style(color="muted_foreground", font_size=13)
                Separator().style(full_width=True)
                Label("TRY IT").style(bold=True, font_size=12, color="muted_foreground")
                Label(
                    "Edit the profile, then switch\nstyles. Selection and undo\nhistory are preserved."
                ).style(color="muted_foreground", font_size=13)
            with Column().style(flex=1, full_width=True, gap=12, background="popover", padding=16, radius=8):
                Label("Profile preview").style(font_size=19, bold=True)
                Label("Display name")
                name = TextInput("Sam Taylor", placeholder="Your name").style(full_width=True)
                Label("About you")
                about = TextArea("Building useful tools, one small idea at a time.").style(
                    full_width=True, height=100
                )
                Checkbox("Share my profile with the team", value=True)
                Switch("Enable desktop notifications", value=True)
                Label("Preview intensity").style(color="muted_foreground", font_size=12)
                Slider(value=65).style(full_width=True)
                with Row().style(gap=10):
                    Button("Show notification", variant="primary", on_click=notify)
                    Button("Cancel", on_click=lambda: app.notify("No changes were saved."))
                    Button("Unavailable", variant="outline", disabled=True)
        Separator().style(full_width=True)
        status = Label(
            f"{next(name for name, key in PRESETS.items() if key == preset)} · {mode.title()} appearance"
        ).style(color="muted_foreground", font_size=12)
    return app, {"name": name, "about": about, "preset": theme_select, "dark": dark, "status": status}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=list(PRESETS.values()), default="macos")
    parser.add_argument("--mode", choices=("light", "dark"), default="light")
    args = parser.parse_args()
    build_app(args.theme, args.mode)[0].run()
