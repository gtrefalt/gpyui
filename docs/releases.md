# Wheels and releases

The [Build wheels workflow](https://github.com/gtrefalt/gpyui/actions/workflows/release.yml)
builds six native wheels and one source archive with pinned Rust and maturin versions.
All wheels use Python's stable `abi3` interface starting at CPython 3.12.

| Platform | Architecture | Wheel suffix | Test Python versions |
| --- | --- | --- | --- |
| Linux | x86_64 | `linux_x86_64` | 3.12, 3.13, 3.14 |
| Linux | ARM64 | `linux_aarch64` | 3.12, 3.13, 3.14 |
| macOS 12+ | Intel | `macosx_12_0_x86_64` | 3.12, 3.13, 3.14 |
| macOS 12+ | Apple Silicon | `macosx_12_0_arm64` | 3.12, 3.13, 3.14 |
| Windows | x64 | `win_amd64` | 3.12, 3.13, 3.14 |
| Windows | ARM64 | `win_arm64` | 3.13, 3.14 |

Windows ARM64 uses native Python 3.13+ on GitHub's runners. The ABI wheel tag
still starts at 3.12; a native Windows ARM64 3.12 interpreter is not tested.
32-bit and musl/Alpine builds are outside this matrix.

Every test job installs the exact built wheel into a clean environment and checks
that both Python code and the Rust extension load from that environment. It runs
the Python/bridge tests. Linux additionally runs the full X11 interaction suite
using Xvfb and software Vulkan. Windows and macOS run a real native-window smoke
test covering input state, batched Python updates, asyncio and shutdown; these
smoke tests do not cover OS mouse/keyboard interaction.

Linux wheels are built in `manylinux_2_28` containers for glibc 2.28+, but tagged
`linux`, using system X11 libraries. They do not claim manylinux portability.
GPUI passes its XCB connection to the system graphics driver: bundling a separate
XCB library during auditwheel repair caused a native crash inside Mesa. Keep the
desktop libraries on the system to avoid mixing private connection structures.
An installed wheel needs no Rust compiler. A functioning display and graphics
backend are required: Metal on macOS, DirectX on Windows, Vulkan on Linux.
For Ubuntu/Debian, install the runtime packages:

```bash
sudo apt-get install libxcb1 libxkbcommon0 libxkbcommon-x11-0 \
  libfontconfig1 libfreetype6 libvulkan1 mesa-vulkan-drivers fonts-dejavu-core
```

## Build and download

Relevant pull requests, version tags and manual workflow runs build artifacts.
Each target uploads `gpyui-dist-<platform>` to its workflow run, retained for
14 days. Each contains a wheel; Linux x64 also includes the source archive.
No PyPI account is needed to build or download them. Install the extracted wheel
matching your operating system and architecture:

```bash
uv venv
uv pip install path/to/gpyui-0.1.0-cp312-abi3-linux_x86_64.whl
```

The exact filenames and sizes are shown in the artifacts. Wheel contents and
metadata are checked before upload; Linux native dependencies are also audited.
Wheels and source archives include `gpyui/THIRD_PARTY_NOTICES.txt`, an inventory
of locked Rust dependencies and their license texts. To regenerate it after
changing dependencies, run `python scripts/generate-wheel-notices.py` with the
pinned Rust toolchain available. It includes optional, build-time and platform
dependencies as well as packages compiled into the binary.

## GitHub releases

Push a tag matching `v` plus the version in `pyproject.toml`, such as `v0.1.0`.
After all six builds and all installed-wheel test jobs pass, the workflow creates
a GitHub prerelease, attaches the six wheels, source archive and `SHA256SUMS`,
and publishes it. Release notes list the download size of each distribution.
These assets remain available on the
[releases page](https://github.com/gtrefalt/gpyui/releases), beyond artifact retention.

The workflow creates a draft first and publishes it only after attaching assets.
If upload fails, it leaves a draft for recovery. It will not replace an existing
release automatically. Pull requests never create releases. Manual runs can select
a matching version tag and enable **Create a GitHub prerelease**.
GitHub releases do not publish packages to PyPI.

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
only after the build and all installed-wheel test jobs succeed.

Manual runs default to building only. Pull requests and tag pushes do not upload
anything to PyPI. Configure the publisher before selecting the publish checkbox.
