"""Generate docs and skill references from Python contracts and runnable specimens.

The docs-only environment can run this without a compiled Rust extension.
Use --check in CI to detect stale references or missing native screenshots.
"""

import argparse
import hashlib
import inspect
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from component_catalog import GROUPS, SAMPLES, runnable_example, specimen

import gpyui as ui

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://github.com/gtrefalt/gpyui/blob/main/"
FIELDS = {
    "Column": {"children": ((), "Iterable[Control]", "Composition")},
    "Label": {"text": ("", "str", "Assignment")},
    "TextInput": {"value": ("", "str", "Assignment"), "placeholder": ("", "str", "Assignment")},
    "Button": {
        "text": (None, "str; defaults to command.label", "Assignment"),
        "command": (None, "Command; mutually exclusive with on_click", "Constructor only"),
        "disabled": (False, "bool", "Assignment"),
        "variant": ("secondary", "primary · secondary · outline · ghost · danger", "Constructor only"),
        "icon": ("", "Lucide name", "Constructor only"),
    },
    "DropdownMenu": {
        "text": ("Required", "str", "Assignment"),
        "items": ("Required", "Iterable[Command | Menu | MenuSeparator]", "Assignment"),
        "disabled": (False, "bool", "Assignment"),
    },
}


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"(?<!^)(?=[A-Z][a-z])", "-", name).lower()).strip("-")


def type_name(validator):
    names = {
        "text": "str",
        "columns": "integer 1–12",
        "field_name": "str; nonempty unique name within a Form",
        "label_width": "nonnegative pixel number",
        "boolean": "bool",
        "number": "finite number",
        "integer": "nonnegative int",
        "strings": "list[str]",
        "rows": "list[list[str]]",
        "points": "list[chart point]",
        "percent": "percentage (0–100)",
        "iso_date": "ISO date string",
        "iso_time": "local time string",
        "hex_color": "RGB/RGBA hex string",
        "tree_items": "list[tree item]",
    }
    if validator.__name__ == "validate":
        values = validator.__closure__[0].cell_contents
        return " · ".join(values)
    return names[validator.__name__]


def source_link(cls):
    relative = Path(inspect.getfile(cls)).relative_to(ROOT).as_posix()
    return SOURCE + relative + f"#L{inspect.getsourcelines(cls)[1]}"


def asset_url(path, prefix=""):
    version = hashlib.sha256((ROOT / "docs" / path).read_bytes()).hexdigest()[:12]
    return f"{prefix}{path}?v={version}"


def card(name, prefix):
    sample = SAMPLES[name]
    target = f"{prefix}{slug(name)}.md"
    image = asset_url(f"screenshots/components/{slug(name)}.png", f"{prefix}../")
    return (
        f'<div class="component-card" markdown>\n\n'
        f"[![Native {name} component]({image})]({target})\n\n"
        f"**[{name}]({target})**\n\n{sample.description}\n\n</div>\n"
    )


def component_page(name):
    cls = getattr(ui, name)
    sample = SAMPLES[name]
    control, _ = specimen(name)
    assert type(control) is cls, name
    events = getattr(cls, "events", ())
    if name == "Button":
        events = ("click",)
    elif name == "TextInput":
        events = ("change",)
    if name in FIELDS:
        fields = FIELDS[name]
    else:
        fields = {
            key: (default, type_name(validate), "Constructor only" if key in cls.readonly else "Assignment")
            for key, (default, validate) in cls.fields.items()
        }
    lines = [
        f"# {name}",
        "",
        sample.description,
        "",
        f"![Native {name} preview]({asset_url(f'screenshots/components/{slug(name)}.png', '../')})",
        "",
        "A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.",
        "",
        "## Runnable example",
        "",
        "```python",
        subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--stdin-filename", "example.py", "-"],
            input=runnable_example(name),
            text=True,
            capture_output=True,
            check=True,
        ).stdout.rstrip(),
        "```",
        "",
        "Run this in a fresh Python process on a desktop with the native build installed.",
        "",
        "## Properties",
        "",
    ]
    if fields:
        lines += ["| Property | Default | Type / accepted values | Update |", "| --- | --- | --- | --- |"]
        for key, (default, typename, update) in fields.items():
            encoded = json.dumps(default, ensure_ascii=False).replace("|", "&#124;")
            display = "Required" if default == "Required" else f"`{encoded}`"
            lines.append(f"| `{key}` | {display} | {typename} | {update} |")
    else:
        lines += ["This control has no component-specific constructor properties."]
    container = name == "Column" or getattr(cls, "container", False)
    if container:
        lines += [
            "",
            "Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, "
            "`clear`, `set_children` or assignment to `children`. Each child has one parent. "
            "Reuse existing instances to preserve native state; see "
            "[runtime composition](../guide/layout.md#runtime-children-and-visibility).",
            "",
            "Construct explicit child lists outside a composition context, as in the example. "
            "Inside a `with` block, construct the parent first and then its children.",
        ]
    lines += [
        "",
        "All controls support `visible` and `dispose()`. Hiding or detaching retains native state; "
        "disposal permanently releases it. See [Control](../reference/core.md).",
        "",
        "## Events and state",
        "",
    ]
    if name == "Form":
        lines += [
            "`on_submit` accepts a sync/async callback with zero arguments or one copied values dict. "
            "`submit_label` and `shortcut` configure the immutable `submit_command`, shared with Button and menus. "
            "`await validate()` and `await submit()` return bool; `busy`, `errors` and `values()` expose Python state. "
            "See [forms and validation](../guide/forms.md) for hidden fields, stale async validation and retry.",
        ]
    elif name == "Field":
        lines += [
            "`control=` accepts a prebuilt value control; alternatively compose children with a `with` block. "
            "Validation requires exactly one bindable value control, including within nested layouts. "
            "`validators=` is a constructor-only iterable of sync/async callables taking one raw value. "
            "Return None/empty string for success or an error message. `control` and `validators` are read-only. "
            "See [forms and validation](../guide/forms.md) for the full validation/submission contract.",
        ]
    elif name == "DropdownMenu":
        lines += [
            "Menu activation calls the selected `Command.on_execute` callback with current native input values. "
            "See [commands and menus](../guide/commands.md)."
        ]
    elif events:
        for event in events:
            text = {
                "change": "Runs after native value and Python mirror/bound State change.",
                "click": "Native pointer or keyboard activation, with current input-value snapshots.",
                "release": "Reports the slider value when the native drag is released.",
                "resize": "Reports native panel sizes after a resize.",
            }[event]
            lines.append(f"- `on_{event}(event)`: {text}")
        lines += [
            "",
            "Handlers can take zero arguments or one `Event`, and can be synchronous or async. "
            "They run on the owned Python asyncio loop. See [events and asyncio](../guide/events.md).",
        ]
        if "change" in events:
            lines += [
                "",
                "`bind_value(State(...))` binds both ways without echoing native edits back through setters. "
                "`unbind()` disposes the subscription. See [state binding](../guide/state.md).",
            ]
    else:
        lines += [
            "This wrapper exposes no Python activation/change handler. Update its mutable properties "
            "by assignment from a running callback. Native behavior remains in Rust."
        ]
        if name == "Label":
            lines += ["", "`bind_text(State(...), transform)` provides one-way text binding."]
    if sample.note:
        lines += ["", "## Contract and limits", "", sample.note]
    lines += [
        "",
        "All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. "
        "Collections are copied on assignment/read: reassign them to submit updates.",
        "",
        f"[Python implementation]({source_link(cls)}) · "
        f"[Native builders]({SOURCE}{'src/view.rs' if name in FIELDS else 'src/kit.rs'}) · "
        "[Full coverage and remaining Kit APIs](../component-coverage.md)",
        "",
    ]
    return "\n".join(lines)


def generated_files():
    names = [name for group in GROUPS.values() for name in group]
    actual = {
        "Column",
        "Label",
        "TextInput",
        "Button",
        "DropdownMenu",
        "Form",
        "Field",
        *(cls.__name__ for cls in ui.widgets.COMPONENTS),
    }
    assert len(names) == len(set(names)) and set(names) == set(SAMPLES) == actual
    pages = {f"docs/components/{slug(name)}.md": component_page(name) for name in names}
    lines = [
        "# Components",
        "",
        f"Browse all **{len(names)} Python controls**. Each page includes a native preview, "
        "an executable Python example, accepted properties and events. These are real GPUI/Kit controls, "
        "not browser replicas.",
        "",
        "Use the site search to find a control by name. "
        "[Coverage and remaining APIs](../component-coverage.md) distinguishes the initial wrappers from full Kit parity.",
        "",
    ]
    nav = ['{ "Components" = [', '  { "Overview" = "components/index.md" },']
    for group, members in GROUPS.items():
        family = slug(group)
        lines += [
            f"## {group}",
            "",
            '<div class="component-grid" markdown>',
            *[card(name, "") for name in members],
            "</div>",
            "",
        ]
        family_lines = [
            f"# {group}",
            "",
            f"Native {group.lower()} controls composed in Python.",
            "",
            '<div class="component-grid" markdown>',
            *[card(name, "../") for name in members],
            "</div>",
            "",
        ]
        pages[f"docs/components/{family}/index.md"] = "\n".join(family_lines)
        nav += [
            f'  {{ "{group}" = [',
            f'    {{ "Overview" = "components/{family}/index.md" }},',
            *[f'    {{ "{name}" = "components/{slug(name)}.md" }},' for name in members],
            "  ] },",
        ]
    nav += ["] },"]
    pages["docs/components/index.md"] = "\n".join(lines)
    config = (ROOT / "zensical.toml").read_text()
    config = re.sub(
        r'"stylesheets/catalog\.css(?:\?v=[a-f0-9]+)?"',
        f'"{asset_url("stylesheets/catalog.css")}"',
        config,
    )
    start, end = "# BEGIN COMPONENT NAV", "# END COMPONENT NAV"
    config = (
        config[: config.index(start) + len(start)]
        + "\n"
        + "\n".join(nav)
        + "\n"
        + config[config.index(end) :]
    )
    pages["zensical.toml"] = config
    pages.update(skill_references())
    return pages


def skill_references():
    """Bundle the same contracts/examples with the installable agent skill."""
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    prefix = "skills/gpyui/references/"
    index = [
        "# Python component index",
        "",
        f"Generated from gpyui {version}'s Python contracts and tested catalog specimens.",
        "Run `uv run --only-group docs python scripts/generate-docs.py` in the library checkout to regenerate.",
        "",
        "Read only the families relevant to the task. Each includes complete runnable examples,",
        "properties, events, constructor-only fields and limits. Rust Kit methods do not imply Python methods.",
        "See [composition](composition.md), [state/events](state-and-events.md) and [styling](styling.md) for shared contracts.",
        "",
        "| Family | Python controls |",
        "| --- | --- |",
    ]
    files = {}
    for group, names in GROUPS.items():
        relative = f"components/{slug(group)}.md"
        index.append(f"| [{group}]({relative}) | {', '.join(names)} |")
        lines = [f"# {group}", "", f"Generated Python API reference for gpyui {version}.", ""]
        for name in names:
            page = component_page(name)
            page = re.sub(r"^!\[Native .*?\n\n", "", page, flags=re.MULTILINE)
            page = page.replace(
                "A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.\n\n",
                "",
            )
            page = re.sub(r"^(#+) ", r"\1# ", page, flags=re.MULTILINE)
            page = re.sub(
                r"\]\(\.\./([^)]*?)\.md(#[^)]*)?\)",
                lambda match: (
                    "]("
                    + {
                        "guide/styling": "../styling.md",
                        "guide/layout": "../composition.md",
                        "guide/events": "../state-and-events.md",
                        "guide/state": "../state-and-events.md",
                        "guide/commands": "../commands-and-menus.md",
                        "guide/forms": "../forms.md",
                    }.get(match[1], f"https://gtrefalt.github.io/gpyui/{match[1].removesuffix('/index')}/")
                    + (
                        "#dynamic-composition"
                        if match[1] == "guide/layout" and match[2]
                        else (match[2] or "")
                    )
                    + ")"
                ),
                page,
            )
            lines.append(page)
        files[prefix + relative] = "\n".join(lines)
    files[prefix + "components.md"] = "\n".join(index) + "\n"
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = generated_files()
    stale = []
    for relative, content in files.items():
        path = ROOT / relative
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    missing = [
        name for name in SAMPLES if not (ROOT / "docs/screenshots/components" / f"{slug(name)}.png").exists()
    ]
    if args.check and (stale or missing):
        raise SystemExit(f"Stale generated docs: {stale}; missing native previews: {missing}")
    print(
        f"{'Verified' if args.check else 'Generated'} {len(SAMPLES)} component references and runnable examples for docs and skills."
    )
