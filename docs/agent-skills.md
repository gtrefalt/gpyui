# Agent skills

Give your coding agent the context to build native desktop apps with gpyui.
The skills include the **Python** API for all 72 controls, composition and State
conventions, asyncio/lifecycle guidance, runnable applications and desktop design
rules. They are inspired by
[GPUI Kit's skills](https://github.com/longbridge/gpui-kit/tree/3a142844d3661159964dce9e5512ca9a40286160/skills),
with guidance adapted to gpyui's actual binding capabilities.

## Install

From your application project, use the
[skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add gtrefalt/gpyui --skill gpyui --skill gpyui-design-guides
```

Choose your coding agent and installation scope. This installs agent instructions;
it does not install the Python library. Use `uv add gpyui` on macOS/Windows,
or `uv add /path/to/wheel.whl` for a Linux wheel from GitHub Releases. See
[installation](guide/install.md) for details and `pip install` alternatives.

For manual Codex installation, copy both complete directories into your
application's `.agents/skills/`:

```bash
git clone --depth 1 https://github.com/gtrefalt/gpyui.git /tmp/gpyui-skills
mkdir -p .agents/skills
cp -R /tmp/gpyui-skills/skills/gpyui .agents/skills/
cp -R /tmp/gpyui-skills/skills/gpyui-design-guides .agents/skills/
```

Other agents may use different installation directories. Include `references/`
and `scripts/`, not just SKILL.md. No upstream checkout is needed to read the
bundled guidance.

## What's included

| Skill | Contents |
| --- | --- |
| [gpyui](https://github.com/gtrefalt/gpyui/blob/main/skills/gpyui/SKILL.md) | Setup, runtime ownership, component-family contracts and complete examples, layout, State/value types, callbacks, batching, async I/O and cancellation, styles and binding limits |
| [gpyui-design-guides](https://github.com/gtrefalt/gpyui/blob/main/skills/gpyui-design-guides/SKILL.md) | Task hierarchy, forms and panes, restrained light appearance, semantic colors, loading/error/destructive states, data views and native interaction review |

The technical skill includes a profile form that saves JSON asynchronously,
a bounded simulated streaming dashboard, and a prebuilt confirmation dialog.
Copy a bundled script into your uv application and launch it with
`uv run python profile.py`, `uv run python dashboard.py`, or `uv run python dialog.py`.
The profile recipe writes `profile.json` in the working directory.

## Ask your agent

> Use the gpyui and gpyui-design-guides skills to build a light native settings
> app. Bind the fields to State, save asynchronously, show validation and errors,
> and verify actual editing and button activation on a desktop.

The references target gpyui 0.4.0; agents should verify their installed version.
They cover native themes, runtime switching, and the current one-window limit. Rust Kit documentation is useful background but does not imply a Python
API exists. The component references are generated from the same source contracts
and specimens as this site's catalog, and CI checks runnable snippets and recipe
logic without compiling the native extension.

See the [skill installation and maintenance guide](https://github.com/gtrefalt/gpyui/blob/main/skills/README.md)
for the full package structure.
