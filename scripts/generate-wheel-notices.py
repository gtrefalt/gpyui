"""Regenerate bundled notices from locked Cargo sources and published VCS revisions."""

import concurrent.futures
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

m = json.loads(subprocess.check_output(["cargo", "metadata", "--locked", "--format-version", "1"], text=True))
packages = []
texts = {}
missing = []


def record(text):
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    texts[digest] = text
    return digest


for p in m["packages"]:
    if p["name"] == "gpyui":
        continue
    root = Path(p["manifest_path"]).parent
    files = []
    for parent in [root, *list(root.parents)[:3]]:
        files = [
            f
            for f in parent.iterdir()
            if f.is_file()
            and ("license" in f.name.lower() or "copying" in f.name.lower() or f.name.lower() == "notice")
        ]
        if files:
            break
    p["notice_ids"] = [record(f.read_text(errors="replace")) for f in sorted(files)]
    packages.append(p)
    if not files:
        missing.append(p)

names = [
    "LICENSE",
    "LICENSE-MIT",
    "LICENSE-APACHE",
    "LICENSE.txt",
    "LICENSE.md",
    "COPYING",
    "LICENSE-MPL-2.0",
]


def retrieve(p):
    root = Path(p["manifest_path"]).parent
    vcsfile = root / ".cargo_vcs_info.json"
    if not vcsfile.exists() or not p.get("repository"):
        return p, []
    vcs = json.loads(vcsfile.read_text())
    sha = vcs.get("git", {}).get("sha1")
    parsed = urlparse(p["repository"])
    parts = parsed.path.strip("/").split("/")
    if parsed.hostname != "github.com" or len(parts) < 2 or not sha:
        return p, []
    repo = "/".join(parts[:2]).removesuffix(".git")
    paths = [vcs.get("path_in_vcs", "").strip("/"), ""]
    found = []
    for directory in dict.fromkeys(paths):
        for name in names:
            path = f"{directory}/{name}".lstrip("/")
            url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    found.append(response.read().decode(errors="replace"))
            except Exception:
                pass
        if found:
            break
    return p, found


with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    for p, found in pool.map(retrieve, missing):
        p["notice_ids"] = [record(t) for t in found]
remaining = [p["name"] + " " + p["version"] for p in packages if not p["notice_ids"]]

print("Using declared standard license texts for", len(remaining), "crates without bundled license files.")
# Supply standard license texts where crates omit their own license files.
# Preserve author/source attribution and any copyright lines in their sources.
standard = {}
for p in packages:
    if p["notice_ids"]:
        continue
    expression = p.get("license") or ""
    license_id = next(
        (item for item in ("Apache-2.0", "MIT", "MPL-2.0", "CC0-1.0") if item in expression), None
    )
    if license_id is None:
        raise RuntimeError((p["name"], expression))
    if license_id not in standard:
        url = f"https://raw.githubusercontent.com/spdx/license-list-data/31ba1a50e5397e00a304dbadc76531740e89ee48/json/details/{license_id}.json"
        with urllib.request.urlopen(url, timeout=30) as response:
            standard[license_id] = json.load(response)["licenseText"]
    p["notice_ids"] = [record(standard[license_id])]
    root = Path(p["manifest_path"]).parent
    notices = []
    for file in root.rglob("*"):
        if file.is_file() and (file.suffix == ".rs" or file.name.lower().startswith("readme")):
            for line in file.read_text(errors="replace").splitlines():
                if "copyright" in line.lower() and len(line) < 350:
                    notices.append(line.strip())
    p["source_copyright_notices"] = list(dict.fromkeys(notices))
lines = [
    "THIRD-PARTY LICENSE NOTICES",
    "",
    "Generated from Cargo.lock SHA256 " + hashlib.sha256(Path("Cargo.lock").read_bytes()).hexdigest() + ".",
    "This inventory includes build-time, optional and platform-specific packages in the lockfile.",
    "Their inclusion here does not imply every package is compiled into every wheel.",
    "License terms below apply to their respective components, not to gpyui authors' own code.",
    "",
]
for p in sorted(packages, key=lambda p: (p["name"], p["version"])):
    source = p.get("repository") or p.get("source") or ""
    lines.extend(
        [
            p["name"] + " " + p["version"],
            "Declared license: " + str(p.get("license") or p.get("license_file")),
            ("Authors: " + ", ".join(p.get("authors", []))).rstrip(),
            "Source: " + source,
            "Source archive: https://crates.io/api/v1/crates/" + p["name"] + "/" + p["version"] + "/download"
            if str(p.get("source", "")).startswith("registry+")
            else "Git source: " + str(p.get("source")),
            "License text IDs: " + ", ".join(p["notice_ids"]),
            *p.get("source_copyright_notices", []),
            "",
        ]
    )
for key, text in sorted(texts.items()):
    lines.extend(["=" * 72, "LICENSE TEXT " + key, "=" * 72, text, ""])
Path("src/gpyui/THIRD_PARTY_NOTICES.txt").write_text("\n".join(lines))
print(
    "Wrote notices:",
    len(packages),
    "packages;",
    len(texts),
    "unique texts;",
    Path("src/gpyui/THIRD_PARTY_NOTICES.txt").stat().st_size,
    "bytes",
)
