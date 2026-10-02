# Wheels and PyPI releases

The [Build wheels workflow](https://github.com/gtrefalt/gpyui/actions/workflows/release.yml)
builds a Linux x86_64 wheel and source archive. The wheel uses Python's stable
`abi3` interface starting at CPython 3.12. It is built in the `manylinux_2_28`
container, targeting glibc 2.28 or newer, and tagged `linux_x86_64`.
It uses the system's X11 libraries and does not claim manylinux portability.

GPUI passes its XCB connection to the system graphics driver. Repairing this
wheel with auditwheel bundles a separate XCB library, which caused a native
crash inside Mesa during installed-wheel testing. Keeping the desktop libraries
on the system avoids mixing their private connection structures.

The workflow installs the resulting wheel into clean environments on Python
3.12, 3.13 and 3.14. Each environment runs the Python/bridge tests and actual
native-window tests using Xvfb and Mesa's software Vulkan driver. Tests assert
that both the Python package and Rust extension are loaded from the installed
wheel, not the source checkout.

macOS, Windows, Linux ARM64 and musl/Alpine wheels are not included in this first
build workflow. A functioning display, Vulkan driver and native font stack are
still needed to run an application; an installed wheel does not require Rust.
For Ubuntu/Debian, install the runtime packages before launching an app:

```bash
sudo apt-get install libxcb1 libxkbcommon0 libxkbcommon-x11-0 \
  libfontconfig1 libfreetype6 libvulkan1 mesa-vulkan-drivers fonts-dejavu-core
```

## Build and download

Relevant pull requests, version tags and manual workflow runs build artifacts.
After a successful build, open the workflow run and download
**gpyui-distributions**. It contains the wheel and `.tar.gz` source distribution.
Artifacts are retained for 14 days. No PyPI account is needed to build or download
them. To install an extracted wheel:

```bash
uv venv
uv pip install path/to/gpyui-0.1.0-cp312-abi3-linux_x86_64.whl
```

The exact filename is shown in the artifact. The workflow audits native
dependencies and validates distribution metadata before uploading it.

## Connect PyPI once

1. Create a [PyPI account](https://pypi.org/account/register/) and enable
   two-factor authentication.
2. Choose the project's distribution license, add its license file and metadata,
   and include required third-party license notices before the first public release.
3. In PyPI's [publishing settings](https://pypi.org/manage/account/publishing/),
   add a pending Trusted Publisher for a new `gpyui` project, or a Trusted
   Publisher on an existing project you own:

   | Setting | Value |
   | --- | --- |
   | Project name | `gpyui` |
   | GitHub owner | `gtrefalt` |
   | Repository | `gpyui` |
   | Workflow filename | `release.yml` |
   | Environment | `pypi` |

   A pending publisher does not reserve a package name. Check name availability
   before the first upload.
4. Optionally configure the repository's `pypi` environment with required
   reviewers. The workflow already requests GitHub's short-lived OIDC identity;
   no PyPI API token or repository secret is needed.

## Publish a version

Update the version in `pyproject.toml`, the corresponding Rust package version
in `Cargo.toml`, and both lockfiles. Each PyPI version must be new; uploaded
distribution filenames cannot be reused. An alpha is appropriate for the current
scope: Python `0.1.0a1` corresponds to Rust `0.1.0-alpha.1`.

Commit the version update, then create and push a matching version tag such as
`v0.1.0a1`. Tag pushes build and test artifacts. To publish, open **Build wheels**,
select **Run workflow**, select that tag as the ref, and enable **Publish to PyPI**.
The tag must exactly match `v` plus the Python package version. Publication runs
only after the build and all three installed-wheel test jobs succeed.

Manual runs default to building only. Pull requests and tag pushes do not upload
anything to PyPI. Configure the publisher before selecting the publish checkbox.
