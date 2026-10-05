"""Validate installable skill references and construct every bundled Python example.

Runs without the native extension. Native rendering/interaction needs a desktop.
"""

import re
import runpy
import sys
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gpyui import Application

ROOT = Path(__file__).resolve().parents[1]


def check() -> None:
    examples = 0
    links = 0
    skills = sorted(path for path in (ROOT / "skills").iterdir() if path.is_dir())
    assert {path.name for path in skills} == {"gpyui", "gpyui-design-guides"}
    for skill in skills:
        entry = skill / "SKILL.md"
        content = entry.read_text()
        metadata = re.match(r"\A---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", content)
        assert metadata and metadata[1] == skill.name, f"Invalid skill metadata: {entry}"
        assert len(metadata[2]) <= 1024, f"Skill description is too long: {entry}"
        for page in sorted(skill.rglob("*.md")):
            content = page.read_text()
            for target in re.findall(r"\]\(([^)]+)\)", content):
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                path = (page.parent / unquote(parsed.path)).resolve()
                assert path.is_relative_to(skill), f"Reference leaves installed skill: {page}: {target}"
                assert path.is_file(), f"Missing skill reference: {page}: {target}"
                links += 1
            for code in re.findall(r"```python\n(.*?)\n```", content, flags=re.DOTALL):
                with patch.object(Application, "run"):
                    namespace = {"__name__": "skill_example"}
                    exec(compile(code, str(page), "exec"), namespace)
                    if isinstance(app := namespace.get("app"), Application):
                        for control in app.children:
                            control._spec()
                examples += 1
        for script in sorted((skill / "scripts").glob("*.py")):
            namespace = runpy.run_path(str(script), run_name="skill_recipe")
            app = namespace["app"]
            assert isinstance(app, Application), script
            for control in app.children:
                control._spec()
            examples += 1
    print(f"Verified 2 installable skills, {links} bundled links and {examples} Python examples/recipes.")


if __name__ == "__main__":
    check()
