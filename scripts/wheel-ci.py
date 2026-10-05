"""Build matrices and checks for the exact distributions offered in releases."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZipFile

PLATFORMS = [
    dict(
        name="linux-x64",
        runner="ubuntu-24.04",
        target="x86_64-unknown-linux-gnu",
        arch="x86_64",
        platform="linux_x86_64",
        python="3.12",
        sdist="--sdist",
    ),
    dict(
        name="linux-arm64",
        runner="ubuntu-24.04-arm",
        target="aarch64-unknown-linux-gnu",
        arch="aarch64",
        platform="linux_aarch64",
        python="3.12",
        sdist="",
    ),
    dict(
        name="macos-intel",
        runner="macos-15-intel",
        target="x86_64-apple-darwin",
        arch="x86_64",
        platform="macosx_12_0_x86_64",
        python="3.12",
        sdist="",
    ),
    dict(
        name="macos-arm64",
        runner="macos-15",
        target="aarch64-apple-darwin",
        arch="aarch64",
        platform="macosx_12_0_arm64",
        python="3.12",
        sdist="",
    ),
    dict(
        name="windows-x64",
        runner="windows-2022",
        target="x86_64-pc-windows-msvc",
        arch="x86_64",
        platform="win_amd64",
        python="3.12",
        sdist="",
    ),
    dict(
        name="windows-arm64",
        runner="windows-11-arm",
        target="aarch64-pc-windows-msvc",
        arch="aarch64",
        platform="win_arm64",
        python="3.13",
        sdist="",
    ),
]


def project_version():
    return tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]


def prepare():
    version = project_version()
    ref = os.environ["GITHUB_REF"]
    tag = f"refs/tags/v{version}"
    if os.environ.get("GITHUB_EVENT_NAME") != "push" or ref != tag:
        raise SystemExit(f"Building requires a pushed version tag matching v{version}")
    project = tomllib.loads(Path("pyproject.toml").read_text())
    backend = next(r for r in project["build-system"]["requires"] if r.startswith("maturin=="))
    tests = [
        dict(name=p["name"], runner=p["runner"], python=python)
        for p in PLATFORMS
        for python in ("3.12", "3.13", "3.14")
        # Native Windows ARM64 Python builds start at 3.13 on these runners.
        if not (p["name"] == "windows-arm64" and python == "3.12")
    ]
    values = dict(
        version=version,
        rust=tomllib.loads(Path("rust-toolchain.toml").read_text())["toolchain"]["channel"],
        maturin=backend.split("==", 1)[1],
        builds=json.dumps(dict(include=PLATFORMS)),
        tests=json.dumps(dict(include=tests)),
    )
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        for key, value in values.items():
            print(f"{key}={value}", file=output)


def check_wheel(wheel, platform):
    assert wheel.name == f"gpyui-{project_version()}-cp312-abi3-{platform}.whl", wheel
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        for required in (
            "gpyui/py.typed",
            "gpyui/THIRD_PARTY_NOTICES.txt",
            "gpyui/_core.pyi",
            "gpyui/application.py",
            "gpyui/controls.py",
        ):
            assert required in names, required
        assert any(name.startswith("gpyui/_core.") and name.endswith((".so", ".pyd")) for name in names)
        assert not any(name.startswith("gpyui.libs/") for name in names)
    print(f"Verified {wheel.name}: {wheel.stat().st_size:,} bytes")


def check():
    wheels = list(Path("dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    check_wheel(wheels[0], os.environ["WHEEL_PLATFORM"])


def venv_python():
    # Resolving this symlink selects the base interpreter and loses venv isolation.
    return Path(".venv/Scripts/python.exe" if sys.platform == "win32" else ".venv/bin/python").absolute()


def install():
    wheels = list(Path("dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    # A separate, dependency-only project prevents building the source checkout.
    project = Path("artifacts/wheel-test")
    project.mkdir(parents=True, exist_ok=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "gpyui-wheel-test"\nversion = "0.0.0"\n'
        f'requires-python = "=={sys.version_info.major}.{sys.version_info.minor}.*"\n'
        "dependencies = []\n\n[tool.uv]\npackage = false\n"
    )
    environment = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(Path(".venv").absolute())}
    environment.pop("VIRTUAL_ENV", None)
    subprocess.run(
        [
            "uv",
            "add",
            "--project",
            str(project),
            "--no-workspace",
            "--python",
            sys.executable,
            str(wheels[0].absolute()),
            "pytest>=8,<10",
            "python-xlib>=0.33,<1",
        ],
        check=True,
        env=environment,
    )
    subprocess.run(
        [
            str(venv_python()),
            "-c",
            """
import sys
from pathlib import Path
import gpyui
import gpyui._core
assert Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(), sys.prefix
for module in (gpyui, gpyui._core):
    path = Path(module.__file__).resolve()
    assert path.is_relative_to(Path(sys.prefix).resolve()), path
    print(f'Testing installed wheel: {path}')
""",
            str(Path(".venv").resolve()),
        ],
        check=True,
    )


def test():
    subprocess.run([str(venv_python()), "-m", "pytest", "-q"], check=True, timeout=180)


def native():
    Path("artifacts").mkdir(exist_ok=True)
    with Path("artifacts/native-smoke.log").open("w") as log:
        result = subprocess.run(
            [str(venv_python()), "-X", "faulthandler", "tests/native_smoke.py"],
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    print(Path("artifacts/native-smoke.log").read_text())
    result.check_returncode()


def release():
    dist = Path("dist")
    wheels = list(dist.glob("*.whl"))
    assert len(wheels) == len(PLATFORMS), wheels
    for platform in PLATFORMS:
        wheel = dist / f"gpyui-{project_version()}-cp312-abi3-{platform['platform']}.whl"
        check_wheel(wheel, platform["platform"])
    assert len(list(dist.glob("*.tar.gz"))) == 1
    files = sorted([*wheels, *dist.glob("*.tar.gz")])
    (dist / "SHA256SUMS").write_text(
        "".join(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}\n" for file in files)
    )
    notes = [
        f"gpyui {project_version()}: native Python controls powered by GPUI Kit.",
        "",
        f"[Changelog](https://github.com/gtrefalt/gpyui/blob/v{project_version()}/CHANGELOG.md)",
        "",
        "In your uv project, install the wheel matching your OS and architecture with `uv add /path/to/wheel.whl`.",
        "Alternatively, use `pip install /path/to/wheel.whl` in a virtual environment.",
        "CPython 3.12+ uses the stable abi3 interface; Windows ARM64 is tested on 3.13+.",
        "macOS requires 12.0+. Linux uses system X11, font and Vulkan libraries (glibc 2.28+); these are Linux-tagged wheels, not manylinux bundles.",
        "",
        "All wheels passed installed-package tests. Linux has native interaction tests; Windows/macOS have native state/lifecycle smoke tests.",
        "",
        "| Distribution | Download size |",
        "| --- | ---: |",
        *[f"| `{file.name}` | {file.stat().st_size / 1_000_000:.2f} MB |" for file in files],
        "",
        "`SHA256SUMS` covers every wheel and the source archive.",
        "",
        "[Documentation](https://gtrefalt.github.io/gpyui/) · [GPUI](https://www.gpui.rs/) · [GPUI Kit](https://gpui-kit.com/)",
    ]
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/release-notes.md").write_text("\n".join(notes) + "\n")


def distribution_names():
    version = project_version()
    return {
        *(f"gpyui-{version}-cp312-abi3-{p['platform']}.whl" for p in PLATFORMS),
        f"gpyui-{version}.tar.gz",
    }


def verify_checksums(dist, manifest):
    expected = distribution_names()
    checksums = {}
    for line in manifest.splitlines():
        digest, name = line.split("  ", 1)
        assert name in expected and name not in checksums, name
        assert len(digest) == 64 and all(char in "0123456789abcdef" for char in digest), digest
        checksums[name] = digest
    assert set(checksums) == expected, checksums
    for name, digest in checksums.items():
        assert hashlib.sha256((dist / name).read_bytes()).hexdigest() == digest, name


def existing_release():
    tag = os.environ.get("RELEASE_TAG") or f"v{project_version()}"
    assert tag == f"v{project_version()}", "Release tag must match the current project version"
    repo = os.environ["GITHUB_REPOSITORY"]

    def api(path):
        return json.loads(subprocess.check_output(["gh", "api", f"repos/{repo}/{path}"], text=True))

    release_info = api(f"releases/tags/{tag}")
    assert not release_info["draft"], "The GitHub release must already be published"
    expected = distribution_names() | {"SHA256SUMS"}
    assets = release_info["assets"]
    assert len(assets) == len(expected) and {asset["name"] for asset in assets} == expected, assets
    commit = subprocess.check_output(["git", "rev-list", "-n", "1", tag], text=True).strip()
    runs = api(f"actions/workflows/release.yml/runs?event=push&head_sha={commit}&status=completed")[
        "workflow_runs"
    ]
    run = next((run for run in runs if run["head_branch"] == tag), None)
    assert run is not None, "No completed tag workflow for this release"
    # A failed PyPI upload must not hide the passed build/test jobs. Include
    # earlier attempts when only the publishing job has been rerun.
    pages = json.loads(
        subprocess.check_output(
            [
                "gh",
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100&filter=all",
            ],
            text=True,
        )
    )
    jobs = [job for page in pages for job in page["jobs"]]
    required = {
        *(f"Wheel / {p['name']}" for p in PLATFORMS),
        *(
            f"Installed wheel / {p['name']} / Python {python}"
            for p in PLATFORMS
            for python in ("3.12", "3.13", "3.14")
            if not (p["name"] == "windows-arm64" and python == "3.12")
        ),
    }
    passed = {job["name"] for job in jobs if job["conclusion"] == "success"}
    assert required <= passed, f"Required builds/tests missing: {required - passed}"
    print(f"Verified all six builds and 17 installed-wheel jobs: {run['html_url']}")
    dist = Path("dist")
    assert not dist.exists(), "Use a clean workspace for release downloads"
    subprocess.run(["gh", "release", "download", tag, "--repo", repo, "--dir", str(dist)], check=True)
    assert {file.name for file in dist.iterdir()} == expected
    verify_checksums(dist, (dist / "SHA256SUMS").read_text())
    for asset in assets:
        actual = f"sha256:{hashlib.sha256((dist / asset['name']).read_bytes()).hexdigest()}"
        assert asset["digest"] == actual, asset["name"]
    print("Verified every release asset against SHA256SUMS and GitHub's asset digests")


def pypi():
    dist = Path("dist")
    expected = distribution_names()
    files = {file.name for file in dist.iterdir()}
    assert files in (expected, expected | {"SHA256SUMS"}), files
    output = Path("pypi-dist")
    assert not output.exists(), "Use a clean destination for publishing"
    # PyPI rejects linux_x86_64/linux_aarch64. Retain these wheels on GitHub;
    # auditwheel bundling is unsafe until GPUI/Mesa share the same XCB library.
    selected = []
    for platform in PLATFORMS:
        wheel = dist / f"gpyui-{project_version()}-cp312-abi3-{platform['platform']}.whl"
        check_wheel(wheel, platform["platform"])
        if platform["platform"].startswith("linux_"):
            print(f"GitHub-only Linux wheel (PyPI rejects this platform tag): {wheel.name}")
        else:
            selected.append(wheel)
    selected.append(dist / f"gpyui-{project_version()}.tar.gz")
    assert len(selected) == 5
    output.mkdir()
    for file in selected:
        shutil.copy2(file, output / file.name)
    print("Prepared four macOS/Windows wheels and one source archive for PyPI")


if __name__ == "__main__":
    commands = {
        "prepare": prepare,
        "check": check,
        "install": install,
        "test": test,
        "native": native,
        "release": release,
        "existing-release": existing_release,
        "pypi": pypi,
    }
    commands[sys.argv[1]]()
