"""Native component gallery. All controls and callbacks are composed in Python."""

from __future__ import annotations

import argparse

import gpyui as ui


def create_gallery(theme="light", *, on_start=None, on_error=None):
    app = ui.Application(
        title="gpyui · Component gallery",
        width=1120,
        height=860,
        theme=theme,
        on_start=on_start,
        on_error=on_error,
    )
    controls = []

    def keep(control):
        controls.append(control)
        return control

    with app, ui.Column().style(full_width=True, full_height=True, gap=16):
        with ui.Row().style(justify="between", full_width=True):
            ui.Label("Native components, Python composition").style(font_size=22, bold=True)
            ui.Tag("GPUI Kit", variant="primary")
        ui.Label("A working selection of the component library. Scroll to explore.").style(
            color="muted_foreground"
        )
        with ui.Scroll().style(full_width=True, flex=1):
            with ui.Row().style(align="start", full_width=True, gap=24):
                with ui.Column().style(flex=1):
                    with ui.GroupBox("Inputs and selection"):
                        ui.Label("Text field")
                        keep(ui.TextInput("Hello from Python", placeholder="Your name"))
                        keep(
                            ui.TextArea("A native multiline field.\nEditing and undo stay in Rust.").style(
                                height=82
                            )
                        )
                        keep(ui.NumberInput("42"))
                        keep(ui.OtpInput("123", length=6))
                        keep(ui.Checkbox("Enable notifications", value=True))
                        keep(ui.Switch("Dark appearance"))
                        keep(ui.Radio("Use system settings", value=True))
                        keep(ui.RadioGroup(["Small", "Medium", "Large"], value=1))
                        keep(ui.Toggle("Pin to workspace"))
                        keep(ui.Select(["Python", "Rust", "GPUI"], value="Python"))
                        keep(ui.Combobox(["London", "New York", "Tokyo"], value="London"))
                        keep(ui.Slider(35))
                        keep(ui.Rating(4))
                    with ui.GroupBox("Date, time and color"):
                        keep(ui.Editor("print('Hello from Python')\n").style(height=100))
                        keep(ui.DatePicker("2026-10-01"))
                        keep(ui.TimeField("09:30"))
                        keep(ui.ColorPicker("#3b82f6"))
                        keep(ui.Calendar("2026-10-01"))
                with ui.Column().style(flex=1):
                    with ui.GroupBox("Navigation and actions"):
                        keep(ui.Breadcrumb(["Workspace", "Components"], value=1))
                        keep(ui.Tabs(["Overview", "Activity", "Settings"]))
                        keep(ui.Stepper(["Details", "Review", "Complete"], value=1))
                        keep(ui.Pagination(pages=8))
                        with ui.Toolbar():
                            keep(ui.Button("Save", variant="primary"))
                            keep(ui.Button("Cancel", variant="outline"))
                            keep(ui.Clipboard("Copied from gpyui"))
                        keep(ui.Link("Explore GPUI Kit ↗", href="https://gpui-kit.com"))
                        keep(ui.List(["Recent files", "Shared with me", "Archive"]))
                        keep(ui.Sidebar(["Overview", "Projects", "Settings"]).style(height=145))
                    with ui.GroupBox("Content and feedback"):
                        with ui.Row():
                            keep(ui.Avatar("Ada Lovelace"))
                            keep(ui.Tag("Ready", variant="success"))
                            keep(ui.Badge(count=3, text="Inbox"))
                            keep(ui.Kbd("ctrl-k"))
                            keep(ui.Icon("check"))
                        keep(ui.Alert("Your changes are saved.", title="All set", variant="success"))
                        keep(ui.Progress(68))
                        with ui.Row():
                            keep(ui.ProgressCircle(68))
                            keep(ui.Spinner())
                            keep(ui.Shimmer("Preparing preview…"))
                        keep(ui.Skeleton())
                        keep(ui.DescriptionList([["Renderer", "GPUI"], ["Components", "GPUI Kit"]]))
                        keep(ui.Empty(title="No new messages", description="You're up to date."))
                with ui.Column().style(flex=1):
                    with ui.GroupBox("Data and charts"):
                        keep(
                            ui.Table(
                                columns=["Name", "Status"], rows=[["Python", "Ready"], ["Rust", "Native"]]
                            ).style(height=130)
                        )
                        data = [["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]
                        keep(ui.LineChart(data).style(height=120))
                        keep(ui.AreaChart(data).style(height=120))
                        keep(ui.BarChart(data).style(height=120))
                        keep(ui.PieChart(data).style(height=120))
                        keep(
                            ui.CandlestickChart(
                                [["Mon", 10, 18, 8, 16], ["Tue", 16, 21, 12, 14], ["Wed", 14, 25, 13, 24]]
                            ).style(height=120)
                        )
                    with ui.GroupBox("Disclosure and messages"):
                        keep(ui.Markdown("**Rich text** and *native selection*."))
                        keep(ui.Html("<p>Rendered by <strong>GPUI Kit</strong>.</p>"))
                        keep(
                            ui.Tree(
                                [
                                    {
                                        "id": "src",
                                        "text": "Source",
                                        "children": [{"id": "src/main.py", "text": "main.py"}],
                                    }
                                ]
                            ).style(height=100)
                        )
                        with keep(ui.Resizable().style(height=90)):
                            ui.Label("Resizable left pane")
                            ui.Label("Resizable right pane")
                        keep(
                            ui.Accordion(
                                [
                                    ["About gpyui", "Compose native apps in Python."],
                                    ["Architecture", "Rust owns native state."],
                                ]
                            )
                        )
                        with keep(ui.Collapsible("More information", value=True)):
                            ui.Label("A retained native disclosure region.")
                        with keep(ui.Bubble()):
                            ui.Label("Hello from a Kit bubble.")
                        keep(ui.Message("Everything here is composed in Python.", author="gpyui"))
                        keep(ui.Marker("Today"))
                        keep(ui.Attachment("report.csv", description="A sample file attachment"))
                        with keep(ui.Tooltip("A native tooltip")):
                            ui.Button("Hover for help")
                        with keep(ui.Popover("Open details")):
                            ui.Label("A native popup with Python-composed contents.")
                        with keep(ui.HoverCard("Hover for a preview")):
                            ui.Label("Kit owns the hover lifecycle.")
                        with keep(ui.Carousel().style(height=100)):
                            ui.Label("First native slide")
                            ui.Label("Second native slide")
        with ui.StatusBar():
            ui.Label("Native GPUI Kit controls · Python callbacks · Light and dark themes")
    with app:
        with keep(ui.Dialog("A native dialog")) as dialog:
            ui.Label("The contents are composed in Python.")
            ui.Button("Close", on_click=dialog.close)
        with keep(ui.Sheet("A native sheet")) as sheet:
            ui.Label("A native side panel.")
            ui.Button("Close", on_click=sheet.close)
    return app, controls


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("light", "dark"), default="light")
    create_gallery(parser.parse_args().theme)[0].run()
