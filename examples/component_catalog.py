"""Runnable specimens shared by native captures and the documentation catalog."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    description: str
    code: str
    note: str = ""
    height: int = 340
    action: str = ""


GROUPS = {
    "Layout": ("Column", "Row", "Container", "Scroll", "GroupBox", "Toolbar", "StatusBar", "Resizable"),
    "Text and buttons": ("Label", "Button", "DropdownMenu", "Link", "Clipboard", "Icon", "Kbd", "Separator"),
    "Forms": ("Form", "Field"),
    "Inputs": ("TextInput", "TextArea", "NumberInput", "OtpInput", "Editor"),
    "Selection": (
        "Checkbox",
        "Switch",
        "Radio",
        "Toggle",
        "RadioGroup",
        "Select",
        "Combobox",
        "Slider",
        "Rating",
    ),
    "Navigation": ("Tabs", "Sidebar", "Breadcrumb", "Stepper", "Pagination"),
    "Data": ("List", "Table", "Tree", "DescriptionList"),
    "Charts": ("LineChart", "AreaChart", "BarChart", "PieChart", "CandlestickChart"),
    "Date, time and color": ("Calendar", "DatePicker", "TimeField", "ColorPicker"),
    "Feedback": ("Progress", "ProgressCircle", "Spinner", "Skeleton", "Shimmer", "Alert", "Empty"),
    "Content": ("Tag", "Badge", "Avatar", "Markdown", "Html", "Bubble", "Message", "Marker", "Attachment"),
    "Disclosure": ("Collapsible", "Accordion", "Carousel"),
    "Overlays": ("Tooltip", "Popover", "HoverCard", "Dialog", "Sheet"),
}

DATA = '[["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]'

SAMPLES = {
    "Form": Sample(
        "Native form layout with named fields, required indicators and Python validation.",
        'control = ui.Form(on_submit=lambda values: print(values), children=[ui.Field("Display name", name="name", control=ui.TextInput("Ada"), required=True, help="Shown to your teammates."), ui.Field("Notifications", name="notifications", control=ui.Switch("Desktop notifications", value=True))])\nsave = ui.Button(command=control.submit_command, variant="outline")',
        "Form accepts only uniquely named Field children. on_submit takes zero arguments or an active-values dict. "
        "Use submit_command for buttons, menus and shortcuts; see the forms guide for validation, async saving and retry.",
    ),
    "Field": Sample(
        "Kit field labels, help, required indicators and retained inline error messages.",
        'control = ui.Field("Email address", name="email", control=ui.TextInput("ada@"), required=True, help="Used only for account updates.", error="Enter a complete email address.")',
        "Python validators take one raw value and return None/empty string or an error message, synchronously or asynchronously. "
        "A validated field contains exactly one bindable value control, possibly inside child layouts. "
        "Field.error is rendered through Kit description_fn, not by replacing an editor.",
    ),
    "Column": Sample(
        "Stack controls vertically.",
        'control = ui.Column([ui.Label("Project"), ui.TextInput("gpyui"), ui.Button("Create")]).style(gap=12)',
    ),
    "Row": Sample(
        "Arrange controls horizontally.",
        'control = ui.Row([ui.Button("Save", variant="primary"), ui.Button("Cancel"), ui.Tag("Ready", variant="success")]).style(gap=12)',
    ),
    "Container": Sample(
        "A composable GPUI layout surface.",
        'control = ui.Container([ui.Label("A themed surface"), ui.Label("Compose children in Python.")]).style(padding=20, gap=12, background="muted", radius=12)',
    ),
    "Scroll": Sample(
        "Native vertical scrolling for composed children.",
        'control = ui.Scroll([ui.Label(f"Item {i}") for i in range(1, 13)]).style(height=160, full_width=True)',
        "Use a bounded height or flexible parent so content has a viewport.",
    ),
    "GroupBox": Sample(
        "Group related controls with a native title.",
        'control = ui.GroupBox("Account", children=[ui.Label("Display name"), ui.TextInput("Ada"), ui.Switch("Receive updates", value=True)])',
    ),
    "Toolbar": Sample(
        "Compose a native toolbar.",
        'control = ui.Toolbar(children=[ui.Button("New", icon="plus"), ui.Button("Save", variant="primary"), ui.Clipboard("Project notes")])',
    ),
    "StatusBar": Sample(
        "Native status content composed in Python.",
        'control = ui.StatusBar(children=[ui.Icon("circle-check"), ui.Label("All changes saved")])',
    ),
    "Resizable": Sample(
        "Native draggable boundaries between panes.",
        'control = ui.Resizable(children=[ui.Label("Files"), ui.Label("Editor")]).style(height=150, full_width=True)',
        "Axis is fixed after construction. on_resize receives native panel sizes.",
    ),
    "Label": Sample(
        "A native text label.", 'control = ui.Label("Hello from Python").style(font_size=24, bold=True)'
    ),
    "Button": Sample(
        "Native activation invokes Python callbacks.",
        'status = ui.Label("Choose Save")\ncontrol = ui.Button("Save", variant="primary", icon="save", on_click=lambda: setattr(status, "text", "Saved from Python"))',
    ),
    "DropdownMenu": Sample(
        "A Kit button with nested commands, checks and shortcut hints.",
        'save = ui.Command("Save", lambda: print("Save requested"), shortcut="mod+s")\nsidebar = ui.Command("Show sidebar", lambda: print("Sidebar requested"), checked=True)\ncontrol = ui.DropdownMenu("Actions", [save, ui.MenuSeparator(), ui.Menu("View", [sidebar])])',
        "Items are Command, Menu or MenuSeparator models. Reassign items to update an open menu. "
        "Shared enabled/checked state and callbacks are owned by Command; see the commands guide.",
        action="click",
    ),
    "Link": Sample(
        "A native link with optional Python activation.",
        'control = ui.Link("Explore GPUI Kit ↗", href="https://gpui-kit.com")',
    ),
    "Clipboard": Sample(
        "Copy a string using the native clipboard.",
        'control = ui.Clipboard("Copied from gpyui")',
        "The native copy affordance owns clipboard behavior.",
    ),
    "Icon": Sample(
        "Bundled Lucide icons rendered natively.",
        'control = ui.Icon("sparkles").style(width=32, height=32, color="primary")',
        "Use lowercase kebab-case Lucide names. Names must refer to bundled assets.",
    ),
    "Kbd": Sample(
        "Display a parsed native keyboard shortcut.",
        'control = ui.Kbd("ctrl-shift-p")',
        "This displays a shortcut; it does not register a Python command handler.",
    ),
    "Separator": Sample(
        "A native divider, optionally with a label.",
        'control = ui.Separator("Details").style(full_width=True)',
    ),
    "TextInput": Sample(
        "Native single-line text editing.",
        'control = ui.TextInput("Ada Lovelace", placeholder="Your name", on_change=lambda event: print(event.value))',
        "Programmatic value replacement clears native undo history; native edits are never echoed back through the setter.",
    ),
    "TextArea": Sample(
        "Native multiline editing.",
        'control = ui.TextArea("A native multiline field.\\nFocus, caret and undo stay in Rust.").style(height=120)',
    ),
    "NumberInput": Sample(
        "A native numeric editing buffer with step buttons.",
        'control = ui.NumberInput("42", placeholder="Quantity")',
        "value is a string, including partially edited input. Step buttons change by one.",
    ),
    "OtpInput": Sample(
        "Native one-time-code editing.",
        'control = ui.OtpInput("123", length=6)',
        "Only ASCII digits are accepted, up to length. Length is fixed and must be between 1 and 32.",
    ),
    "Editor": Sample(
        "A retained native editor buffer.",
        'control = ui.Editor("def greet(name):\\n    return name.upper()\\n").style(height=150)',
        "Basic editing is exposed; Python language-server and provider hooks remain future work.",
    ),
    "Checkbox": Sample(
        "An independent boolean choice.", 'control = ui.Checkbox("Enable notifications", value=True)'
    ),
    "Switch": Sample("A native boolean switch.", 'control = ui.Switch("Auto-save", value=True)'),
    "Radio": Sample(
        "A standalone native radio control.",
        'control = ui.Radio("Use system settings", value=True)',
        "Standalone radios do not enforce exclusivity. Use RadioGroup for a grouped choice.",
    ),
    "Toggle": Sample("A boolean button-like toggle.", 'control = ui.Toggle("Pin to workspace", value=True)'),
    "RadioGroup": Sample(
        "An exclusive indexed native choice.",
        'control = ui.RadioGroup(["Small", "Medium", "Large"], value=1)',
        "value is a zero-based item index.",
    ),
    "Select": Sample(
        "A retained native single-selection dropdown.",
        'control = ui.Select(["Python", "Rust", "GPUI"], value="Python")',
        'value is a selected string or "". Items are fixed after construction.',
    ),
    "Combobox": Sample(
        "Search within native string choices.",
        'control = ui.Combobox(["London", "New York", "Tokyo"], value="London")',
        'value is a selected string or "". Items are fixed after construction.',
    ),
    "Slider": Sample(
        "A retained native scalar slider.",
        "control = ui.Slider(35, minimum=0, maximum=100, step=1)",
        "minimum < maximum, step > 0, and value must remain in range. Range and step are fixed. on_release reports the released value.",
    ),
    "Rating": Sample(
        "Native zero-to-five rating.",
        "control = ui.Rating(4)",
        "value is an integer from 0 through 5, not a navigation index.",
    ),
    "Tabs": Sample(
        "Native selection among labeled tabs.",
        'control = ui.Tabs(["Overview", "Activity", "Settings"], value=1)',
        "value is a zero-based item index. Compose the corresponding content in Python.",
    ),
    "Sidebar": Sample(
        "Native sidebar navigation.",
        'control = ui.Sidebar(["Overview", "Projects", "Settings"], value=1).style(height=160)',
    ),
    "Breadcrumb": Sample(
        "Native breadcrumb selection.", 'control = ui.Breadcrumb(["Workspace", "Projects", "gpyui"], value=2)'
    ),
    "Stepper": Sample(
        "Native steps with indexed selection.",
        'control = ui.Stepper(["Details", "Review", "Complete"], value=1)',
    ),
    "Pagination": Sample(
        "A native pagination control.",
        "control = ui.Pagination(pages=8, value=1)",
        "Python page indices start at zero; the wrapper translates to Kit's one-based display.",
    ),
    "List": Sample(
        "Compose selectable native ListItems.",
        'control = ui.List(["Recent files", "Shared with me", "Archive"], value=1)',
        "This wrapper composes ListItems. It does not expose virtual ListState/delegate or async search.",
    ),
    "Table": Sample(
        "Native retained table state with string rows.",
        'control = ui.Table(columns=["Name", "Language", "Status"], rows=[["gpyui", "Python", "Ready"], ["GPUI Kit", "Rust", "Native"]], column_width=185).style(height=160, full_width=True)',
        "Rows must match the column count. Columns and column_width are fixed. Reassign rows to refresh. value is the selected zero-based row index; native selection initially may be empty while the Python default is zero.",
    ),
    "Tree": Sample(
        "Native tree selection with stable item IDs.",
        'control = ui.Tree([{ "id": "src", "text": "Source", "children": [{"id": "src/main.py", "text": "main.py"}]}, {"id": "docs", "text": "Documentation"}], value="docs").style(height=160)',
        "Item IDs must be unique. value is an item ID or an empty string. Items are fixed; at most 10,000 items and 32 levels.",
    ),
    "DescriptionList": Sample(
        "Native label/value presentation.",
        'control = ui.DescriptionList([["Language", "Python"], ["Renderer", "GPUI"], ["Components", "GPUI Kit"]])',
        "Each item is a two-string label/value pair.",
    ),
    "LineChart": Sample(
        "Native line plot with data-following domain.",
        f"control = ui.LineChart({DATA}).style(height=190, full_width=True)",
        "Data points are [label, value]. Reassign data to update the native plot.",
    ),
    "AreaChart": Sample(
        "A native filled area plot.", f"control = ui.AreaChart({DATA}).style(height=190, full_width=True)"
    ),
    "BarChart": Sample(
        "A native bar plot.", f"control = ui.BarChart({DATA}).style(height=190, full_width=True)"
    ),
    "PieChart": Sample(
        "A native pie plot with nonnegative values.",
        f"control = ui.PieChart({DATA}).style(height=190, full_width=True)",
        "Each point is [label, nonnegative value].",
    ),
    "CandlestickChart": Sample(
        "Native OHLC candles.",
        'control = ui.CandlestickChart([["Mon", 10, 18, 8, 16], ["Tue", 16, 21, 12, 14], ["Wed", 14, 25, 13, 24]]).style(height=190, full_width=True)',
        "Candles are [label, open, high, low, close], with low <= open/close <= high.",
    ),
    "Calendar": Sample(
        "Retained native calendar selection.",
        'control = ui.Calendar("2026-10-02")',
        'Single ISO date, YYYY-MM-DD, or "" for no date. Date ranges are not exposed.',
        height=480,
    ),
    "DatePicker": Sample(
        "Native single-date picker.",
        'control = ui.DatePicker("2026-10-02")',
        'Single ISO date, YYYY-MM-DD, or "" for no date.',
    ),
    "TimeField": Sample(
        "Native local time editing.",
        'control = ui.TimeField("09:30:00")',
        "Local time strings normalize to HH:MM:SS. Timezone-aware values are rejected.",
    ),
    "ColorPicker": Sample(
        "Native RGB/RGBA color selection.",
        'control = ui.ColorPicker("#3b82f6")',
        "Use #rrggbb or #rrggbbaa. Alpha is retained.",
    ),
    "Progress": Sample(
        "Native percentage progress.",
        "control = ui.Progress(68).style(full_width=True)",
        "value is a percentage from 0 through 100. loading enables indeterminate feedback.",
    ),
    "ProgressCircle": Sample("Native circular percentage progress.", "control = ui.ProgressCircle(68)"),
    "Spinner": Sample(
        "Native animated busy feedback.",
        "control = ui.Spinner()",
        "The preview captures one frame of a native animation.",
    ),
    "Skeleton": Sample(
        "Native placeholder feedback.",
        "control = ui.Skeleton()",
        "The preview captures one frame of a native animation.",
    ),
    "Shimmer": Sample(
        "Native animated loading text.",
        'control = ui.Shimmer("Preparing preview…")',
        "The preview captures one frame of a native animation.",
    ),
    "Alert": Sample(
        "Native semantic status messages.",
        'control = ui.Alert("Your changes are saved.", title="All set", variant="success")',
    ),
    "Empty": Sample(
        "Native empty-state presentation.",
        'control = ui.Empty(title="No new messages", description="You are up to date.")',
    ),
    "Tag": Sample("Native text tags with semantic variants.", 'control = ui.Tag("Ready", variant="success")'),
    "Badge": Sample("Native count badges.", 'control = ui.Badge(count=3, text="Inbox")'),
    "Avatar": Sample(
        "Native initials generated from a name.",
        'control = ui.Avatar("Ada Lovelace")',
        "Initials are exposed in this wrapper; image avatars remain future work.",
    ),
    "Markdown": Sample(
        "Native rich text from Markdown.",
        'control = ui.Markdown("### Native rich text\\n**Bold**, *emphasis*, and `inline code`.\\n\\nRendered by GPUI Kit.")',
        "Text rendering and selection stay native.",
    ),
    "Html": Sample(
        "Native rich text from supported HTML.",
        'control = ui.Html("<h3>Native rich text</h3><p><strong>Bold</strong> and <em>emphasis</em>.</p>")',
        "This is Kit's native TextView HTML support, not an embedded browser or arbitrary webpage.",
    ),
    "Bubble": Sample(
        "Native bubble content composed in Python.",
        'control = ui.Bubble(children=[ui.Label("Hello from a Kit bubble.")])',
    ),
    "Message": Sample(
        "Native authored message presentation.",
        'control = ui.Message("Compose your app in Python.", author="gpyui")',
    ),
    "Marker": Sample("Native message/date marker.", 'control = ui.Marker("Today")'),
    "Attachment": Sample(
        "Native attachment presentation.",
        'control = ui.Attachment("report.csv", description="Sample file attachment")',
        "Presentation is exposed; file download/open behavior is an application concern.",
    ),
    "Collapsible": Sample(
        "Native disclosure for Python-composed content.",
        'control = ui.Collapsible("More information", value=True, children=[ui.Label("Rust retains native component state.")])',
    ),
    "Accordion": Sample(
        "Native disclosure among labeled items.",
        'control = ui.Accordion([["About gpyui", "Compose native apps in Python."], ["Architecture", "Rust owns rendering and editing."]], value=0)',
        "The initial wrapper exposes one open index and string item contents.",
    ),
    "Carousel": Sample(
        "Native slide selection.",
        'control = ui.Carousel(children=[ui.Label("First native slide"), ui.Label("Second native slide")]).style(height=150, full_width=True)',
    ),
    "Tooltip": Sample(
        "Native tooltip attached to composed content.",
        'control = ui.Tooltip("Native help text", children=[ui.Button("Hover for help")])',
        "Kit owns the hover lifecycle.",
        action="hover",
    ),
    "Popover": Sample(
        "Native popup with Python-composed contents.",
        'control = ui.Popover("Open details", children=[ui.Label("A native popup, composed in Python.")])',
        "Open/close lifecycle is native; controlled Python popup state is not exposed.",
        action="click",
    ),
    "HoverCard": Sample(
        "Native hover preview content.",
        'control = ui.HoverCard("Hover for a preview", children=[ui.Label("A native preview card.")])',
        "Kit owns the hover lifecycle.",
        action="hover",
    ),
    "Dialog": Sample(
        "A native dialog containing Python controls.",
        'control = ui.Dialog("Confirm changes", children=[ui.Label("Save this project?"), ui.Button("Save", variant="primary")])\nopen_button = ui.Button("Open dialog", on_click=control.open)',
        "Use open()/close(), or assign value. One dialog per window; title is fixed.",
        height=440,
        action="overlay",
    ),
    "Sheet": Sample(
        "A native side panel containing Python controls.",
        'control = ui.Sheet("Project details", children=[ui.Label("Project: gpyui"), ui.TextInput("Ada Lovelace"), ui.Switch("Notifications", value=True)])\nopen_button = ui.Button("Open sheet", on_click=control.open)',
        "Use open()/close(), or assign value. One sheet per window; title is fixed.",
        height=440,
        action="overlay",
    ),
}


def specimen(name):
    """Construct the trusted sample outside composition contexts."""
    import gpyui as ui

    namespace = {"ui": ui}
    exec(compile(SAMPLES[name].code, f"<component sample: {name}>", "exec"), namespace)
    roots = {
        key: value
        for key, value in namespace.items()
        if isinstance(value, ui.Control) and value._parent is None
    }
    return namespace["control"], roots


def runnable_example(name):
    _, roots = specimen(name)
    sample = SAMPLES[name]
    return (
        "import gpyui as ui\n\n" + sample.code + "\n\n"
        f"app = ui.Application(ui.Column([{', '.join(roots)}]),\n"
        f'                     title="{name}", width=640, height={sample.height})\n'
        "app.run()\n"
    )
