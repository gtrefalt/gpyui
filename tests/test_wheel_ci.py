"""Publishing must preserve tested bytes and exclude unsupported Linux tags."""

import hashlib
import importlib.util
import json
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
                    "themes.py",
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


@pytest.mark.parametrize(
    ("event", "ref"),
    [
        ("push", "refs/heads/main"),
        ("pull_request", "refs/pull/10/merge"),
        ("workflow_dispatch", "refs/tags/v0.1.0"),
        ("push", "refs/tags/v0.1.1"),
    ],
)
def test_build_rejects_non_release_events_and_mismatched_tags(distributions, monkeypatch, event, ref):
    monkeypatch.setenv("GITHUB_EVENT_NAME", event)
    monkeypatch.setenv("GITHUB_REF", ref)
    with pytest.raises(SystemExit, match="Building requires a pushed version tag"):
        wheel_ci.prepare()


def test_matching_tag_prepares_complete_release_matrix(distributions, monkeypatch):
    project = Path("pyproject.toml")
    project.write_text(project.read_text() + '\n[build-system]\nrequires = ["maturin==1.12.6"]\n')
    Path("rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.99.0"\n')
    output = Path("github-output")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_REF", "refs/tags/v0.1.0")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    wheel_ci.prepare()
    values = dict(line.split("=", 1) for line in output.read_text().splitlines())
    assert values["version"] == "0.1.0"
    assert len(json.loads(values["builds"])["include"]) == 6
    assert len(json.loads(values["tests"])["include"]) == 17


@pytest.mark.parametrize("missing_build", [False, True])
def test_upload_recovery_requires_passed_jobs_but_allows_failed_publishing(
    distributions, monkeypatch, missing_build
):
    manifest = checksum_manifest(distributions)
    (distributions / "SHA256SUMS").write_text(manifest)
    assets = [
        dict(name=file.name, digest=f"sha256:{hashlib.sha256(file.read_bytes()).hexdigest()}")
        for file in distributions.iterdir()
    ]
    saved = Path("saved-release")
    distributions.rename(saved)
    monkeypatch.setenv("GITHUB_REPOSITORY", "gtrefalt/gpyui")
    monkeypatch.setenv("RELEASE_TAG", "")  # Defaults to the current package version.
    jobs = [dict(name=f"Wheel / {p['name']}", conclusion="success") for p in wheel_ci.PLATFORMS]
    jobs += [
        dict(name=f"Installed wheel / {p['name']} / Python {python}", conclusion="success")
        for p in wheel_ci.PLATFORMS
        for python in ("3.12", "3.13", "3.14")
        if not (p["name"] == "windows-arm64" and python == "3.12")
    ]
    jobs.append(dict(name="Publish tested distributions to PyPI", conclusion="failure"))
    if missing_build:
        jobs[0]["conclusion"] = "failure"

    def command(args, **kwargs):
        if args[0] == "git":
            return "tested-commit\n"
        if "--paginate" in args:
            assert "filter=all" in args[-1]
            return json.dumps([dict(jobs=jobs[:10]), dict(jobs=jobs[10:])])
        if "releases/tags/" in args[-1]:
            return json.dumps(dict(draft=False, assets=assets))
        assert "status=completed" in args[-1]
        return json.dumps(
            dict(
                workflow_runs=[dict(id=123, head_branch="v0.1.0", html_url="test-run", conclusion="failure")]
            )
        )

    def download(args, **kwargs):
        assert args[:4] == ["gh", "release", "download", "v0.1.0"]
        saved.rename(Path("dist"))

    monkeypatch.setattr(wheel_ci.subprocess, "check_output", command)
    monkeypatch.setattr(wheel_ci.subprocess, "run", download)
    if missing_build:
        with pytest.raises(AssertionError, match="Required builds/tests missing"):
            wheel_ci.existing_release()
        assert not Path("dist").exists()
    else:
        wheel_ci.existing_release()
        assert Path("dist/SHA256SUMS").read_text() == manifest
