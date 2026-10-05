# Wheels and releases

The [Release workflow](https://github.com/gtrefalt/gpyui/actions/workflows/release.yml)
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

Only a pushed version tag builds release artifacts. Pull requests and ordinary
branch pushes run lightweight Python checks and documentation builds; they do
not build native wheels. Manual release workflow runs reuse tested GitHub release
assets without rebuilding.
Each target uploads `gpyui-dist-<platform>` to its workflow run, retained for
14 days. Each contains a wheel; Linux x64 also includes the source archive.
No PyPI account is needed to build or download them. Install the extracted wheel
matching your operating system and architecture:

```bash
uv init my-app
cd my-app
uv add /path/to/gpyui-0.1.1-cp312-abi3-linux_x86_64.whl
```

For an existing uv project, only the `uv add` command is needed.
Alternatively, use `pip install /path/to/wheel.whl` in a virtual environment.

The exact filenames and sizes are shown in the artifacts. Wheel contents and
metadata are checked before upload; Linux native dependencies are also audited.
Wheels and source archives include `gpyui/THIRD_PARTY_NOTICES.txt`, an inventory
of locked Rust dependencies and their license texts. To regenerate it after
changing dependencies, run `python scripts/generate-wheel-notices.py` with the
pinned Rust toolchain available. It includes optional, build-time and platform
dependencies as well as packages compiled into the binary.

## GitHub releases

Push a tag matching `v` plus the version in `pyproject.toml`, such as `v0.1.1`.
After all six builds and all installed-wheel test jobs pass, the workflow creates
a GitHub prerelease, attaches the six wheels, source archive and `SHA256SUMS`,
and publishes it. Release notes list the download size of each distribution.
These assets remain available on the
[releases page](https://github.com/gtrefalt/gpyui/releases), beyond artifact retention.

The workflow creates a draft first and publishes it only after attaching assets.
If upload fails, it leaves a draft for recovery. It will not replace an existing
release automatically. Pull requests and manual runs never create GitHub
releases. After the GitHub release succeeds, the same workflow automatically
publishes the PyPI-compatible distributions with Trusted Publishing.

## PyPI platform support

PyPI accepts the four macOS/Windows wheels and the source archive. The workflow
checks the complete six-wheel build before selecting those five distributions.
The Linux wheels remain on GitHub Releases: PyPI's
[platform validation](https://github.com/pypi/warehouse/blob/main/warehouse/utils/wheel.py)
rejects `linux_x86_64` and `linux_aarch64`. We cannot claim manylinux compatibility
by changing the filename; the XCB/graphics-driver issue described above must be
resolved first. On Linux, download a prebuilt wheel from GitHub. Installing the
PyPI source archive instead requires Rust and the native build prerequisites.

## Connect PyPI once

1. Create a [PyPI account](https://pypi.org/account/register/) and enable
   two-factor authentication. Connecting GitHub for account login does **not**
   configure a Trusted Publisher.
2. gpyui uses the [MIT License](https://github.com/gtrefalt/gpyui/blob/main/LICENSE).
   The license file and distribution metadata are configured for subsequent
   builds. The already published `0.1.0` distributions cannot be replaced;
   they predate this metadata update. Third-party notices are included in both
   that release and subsequent builds.
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
distribution filenames cannot be reused. Record release changes in `CHANGELOG.md`.

Merge the version update, then create and push a matching version tag such as
`v0.1.1`. This is the only event that starts native builds. After all six builds
and 17 installed-wheel test jobs pass, the workflow publishes the GitHub release
and then uploads the PyPI-compatible files automatically. Configure the Trusted
Publisher before pushing the tag.

To recover a PyPI upload without rebuilding, run **Release** on **main**, enable
**Publish to PyPI**, and enter the published tag in **existing_release** (or leave
it blank to use the current project's version). The tag must match the current
project's version. The job checks the tag's passed build/test jobs, even if an
earlier PyPI upload failed. It
downloads its seven distributions, verifies SHA256SUMS and GitHub asset digests,
then uploads the PyPI-compatible subset. Already published distributions are not
replaced; their filenames and bytes must match. A manual run with publication
disabled does not build or upload anything.

## Updating the PyPI README

PyPI displays the README stored in the uploaded distribution metadata. A commit
to GitHub changes the repository README, but does not change PyPI. To refresh
the PyPI description, screenshots, license metadata or project links, publish a
new version (a patch release such as `0.1.1` is appropriate for packaging changes).
Existing release files cannot be overwritten. Use absolute image and documentation
URLs so the README also renders outside the GitHub checkout.
