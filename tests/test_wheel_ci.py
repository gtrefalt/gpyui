"""Publishing must preserve tested bytes and exclude unsupported Linux tags."""

import hashlib
import importlib.util
from pathlib import Path
from zipfile import ZipFile

import pytest

spec = importlib.util.spec_from_file_location(
    "wheel_ci", Path(__file__).resolve().parents[1] / "scripts/wheel-ci.py"
)
assert spec and spec.loader
wheel_ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wheel_ci)


@pytest.fixture
def distributions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n')
    dist = tmp_path / "dist"
    dist.mkdir()
    for name in wheel_ci.distribution_names():
        file = dist / name
        if name.endswith(".whl"):
            with ZipFile(file, "w") as archive:
                for entry in (
                    "py.typed",
                    "THIRD_PARTY_NOTICES.txt",
                    "_core.pyi",
                    "application.py",
                    "controls.py",
                    "_core.abi3.so",
                ):
                    archive.writestr(f"gpyui/{entry}", "test fixture")
        else:
            file.write_bytes(b"source fixture")
    return dist


def checksum_manifest(dist):
    return "".join(
        f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}\n" for file in sorted(dist.iterdir())
    )


def test_pypi_selection_preserves_four_wheels_and_source(distributions):
    wheel_ci.pypi()
    output = Path("pypi-dist")
    assert len(list(output.iterdir())) == 5
    assert not list(output.glob("*linux*"))
    for file in output.iterdir():
        assert file.read_bytes() == (distributions / file.name).read_bytes()
    assert len(list(distributions.iterdir())) == 7


def test_missing_platform_aborts_before_creating_upload_directory(distributions):
    next(distributions.glob("*linux_x86_64.whl")).unlink()
    with pytest.raises(AssertionError):
        wheel_ci.pypi()
    assert not Path("pypi-dist").exists()


def test_checksum_verification_detects_changed_bytes(distributions):
    manifest = checksum_manifest(distributions)
    wheel_ci.verify_checksums(distributions, manifest)
    next(distributions.glob("*.whl")).write_bytes(b"corrupt wheel")
    with pytest.raises(AssertionError):
        wheel_ci.verify_checksums(distributions, manifest)


@pytest.mark.parametrize("alteration", ["missing", "duplicate", "path"])
def test_checksum_manifest_requires_exact_asset_set(distributions, alteration):
    lines = checksum_manifest(distributions).splitlines()
    if alteration == "missing":
        lines.pop()
    elif alteration == "duplicate":
        lines.append(lines[0])
    else:
        lines[0] = f"{'0' * 64}  ../untrusted.whl"
    with pytest.raises(AssertionError):
        wheel_ci.verify_checksums(distributions, "\n".join(lines))
