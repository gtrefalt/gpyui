"""Build matrices and checks for the exact distributions offered in releases."""

import hashlib
import json
import os
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
    if ref.startswith("refs/tags/") and ref != tag:
        raise SystemExit(f"Tag must match the package version: v{version}")
    if any(os.environ.get(flag) == "true" for flag in ("PUBLISH", "RELEASE")) and ref != tag:
        raise SystemExit(f"Publishing requires selecting the v{version} tag")
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
    subprocess.run(["uv", "venv", ".venv", "--python", sys.executable], check=True)
    wheels = list(Path("dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    subprocess.run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(venv_python()),
            str(wheels[0]),
            "pytest>=8,<10",
            "python-xlib>=0.33,<1",
        ],
        check=True,
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
        f"Initial gpyui {project_version()} prerelease: native Python controls powered by GPUI Kit.",
        "",
        "Download the wheel matching your OS and architecture; install with `uv pip install path/to/wheel.whl`.",
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


if __name__ == "__main__":
    commands = dict(prepare=prepare, check=check, install=install, test=test, native=native, release=release)
    commands[sys.argv[1]]()
