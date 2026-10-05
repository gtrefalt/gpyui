# Validation

Validation target: Debian 13, x86_64 Linux, Python 3.12.14, Rust 1.99.0,
GPUI Kit 0.7.0 at the pinned git revision, GPUI snapshot 0.3.7.

## Shared commands and menus (0.3.0)

The feature's local checks pass 157 Python/bridge tests, Ruff, ty, Rust formatting
and strict Clippy. The documentation generates 72 component references and
validates 104 built pages; both installable skills construct 81 examples/recipes.

Two Linux/X11 real-window cases exercise the Kit and native-menu fallback paths:
Save from a button, dropdown, assigned context menu, application menu, shortcut
and queued `Command.execute()`, shared disablement, checked sidebar visibility,
nested submenu navigation, replacement/removal of open drawn menus, runtime
shortcut registration, callback thread and shutdown. Input caret insertion and
native Undo are checked around command activation. The full suite runs 16 native
regression cases, including existing editing, dynamic-layout and lifecycle checks.
OS-native context menus contain an opening snapshot;
open drawn menus refresh from live commands/items.

`tests/native_smoke.py` additionally checks command discovery, menu construction,
async queued activation, latest input snapshots and enabled/checked state in
installed release wheels on every supported release platform. macOS/Windows
pointer and keyboard menu interaction remains a separate platform validation
need; a smoke test does not certify every OS interaction.

The new notes editor was run as a native light-theme window. Its save shortcut
wrote a real temporary UTF-8 document, and its sidebar shortcut changed layout.
The public PNGs capture that native window and an open Kit DropdownMenu.
Unit tests verify successful notes persistence, actionable I/O failures and
cancellation after native shutdown. No simulated browser controls are used.

## Dynamic composition (0.2.0)

Real X11/Vulkan interaction tests cover TextInput, TextArea and Editor. While
keyboard editing continues, Python inserts siblings, reorders children and moves
the editing control to another parent. Tests assert unchanged text and retained
caret, selection, focus and undo history. Native navigation deliberately ends a
typing transaction before checking separate undo steps, matching Kit's actual
undo manager rather than relying on a timer.

Hide/show, ancestor visibility, detach/reattach, page replacement, runtime button
activation, binding continuity and explicit disposal are also checked. Hidden
inputs stop receiving keyboard edits; disposed IDs disappear from snapshots.
Window close cancels the polling coroutine and leaves no callback/executor thread.

The cross-platform installed-wheel smoke test now exercises dynamic children,
root moves, visibility, retained state and disposal on every release platform.
Editing interaction remains verified on Linux/X11; platform smoke tests do not
prove OS keyboard interaction on macOS or Windows.

Python tests additionally check atomic ownership validation, cross-app/thread
rejection, bindings and overlay limits. Real bridge tests check immutable
identity, malformed trees, retired IDs and queue-overload schema rollback.
The historical validation results below describe earlier milestones.

## Zensical documentation

Zensical 0.0.67 and Ruff 0.16.10 are pinned in the docs dependency group and
`uv.lock`. A separate docs-only environment successfully generated/verified all
71 references and built in strict/clean mode without importing the native
extension. The site contains 98 Markdown pages and 99 generated HTML pages
including the 404 page. The built-site check verifies local links, assets and
anchors, including card links and the GitHub Pages subpath.

Each of the 71 controls was mounted in a fresh real native process under
Xvfb/Lavapipe, captured to its individual PNG, and closed without callback errors
or a remaining Python asyncio worker. Native hover/popover/dialog/sheet previews
were opened before capture. These captures prove basic mounting/rendering, not
exhaustive interaction coverage for all builder options.

All **80 complete Python examples** in the documentation, including the 71
component examples, constructed their real control trees and were accepted by
the Rust Bridge schema. The bridge was used for validation; those example-code
checks did not start another native window or pretend to test rendering.

Headless Chromium checks confirmed that the 71 catalog images load, the component
page and search results render, and the mobile catalog has no horizontal overflow.
Desktop/mobile captures are kept locally under `artifacts/docs/`. The existing
Python/bridge suite still reports **110 passed, 11 skipped**; Ruff lint/format pass.

The workflow builds an HTML preview artifact on PRs/main without Rust/native
packages. Optional Pages deployment requires the repository Pages source and
`PUBLISH_DOCS` variable described in [documentation development](contributing-docs.md).

## Streaming example and GIF

The Python workspace now runs a seeded local quote/trade stream on the existing
owned asyncio callback loop. Updates are batched every 650 ms. Its native
watchlist, current quote, change tag, 12-point rolling chart, four-row market tape
and feed counter update together. Paper fills use the current simulated price;
the requested symbol/side are captured before the asynchronous fill delay.

`uv run --locked pytest -q`: **110 passed, 11 skipped**. The market tests verify
replay, independent state, positive quotes, consistent percentages, matching
latest chart/quote values and bounded histories/tape across 1,000 ticks.
`scripts/test-native.sh -x`: **11 passed, 110 deselected in 16.05s**. The added
streaming scenario verifies actual native chart/quote consistency, tape updates,
paper fills and shutdown with no asyncio worker/executor threads left running.
The original ten native scenarios still pass. After limiting the visible tape
to four complete rows, the targeted streaming scenario passed again in 2.99s.

[`scripts/record-workspace.py`](https://github.com/gtrefalt/gpyui/blob/main/scripts/record-workspace.py) records the actual
1180×790 X11 window through FFmpeg, with real mouse/keyboard Buy/Sell activation
and a switch to AAPL. Native snapshots verify both fills and the changed chart;
shutdown reports no errors and only MainThread. The resulting
[GIF](screenshots/workspace-stream.gif) contains 120 frames at 10 fps and loops
over 12 seconds. Frames were decoded and visually inspected. Lossless source
video, snapshots and logs remain under gitignored `artifacts/recording/`.

Regenerate with `uv run python scripts/record-workspace.py` on Linux, with Xvfb,
xdotool, FFmpeg, the development dependencies and native build prerequisites.
There are no external market feeds or broker connections. `--static` disables
streaming in the workspace example; its stream is cancelled when the app closes.


## Expanded catalog validation

The optimized extension was rebuilt successfully with `uv sync --locked` after
adding the component catalog. This incremental release build took **29.02s**;
upstream Kit/GPUI revisions remain unchanged. `cargo check --locked`,
`cargo clippy --locked -- -D warnings`, `cargo fmt --check`, Ruff lint and Ruff
format checks all passed.

`uv run --locked pytest -q`: **108 passed, 10 skipped**. The skipped tests require
an actual display. `scripts/test-native.sh -x`: **10 passed, 108 deselected in
13.48s**, using the installed optimized extension, Xvfb and Mesa Lavapipe.

The new Python/bridge tests validate all 67 additional control schemas through
the real Rust bridge, typed binding, collection copies, layout ownership,
constructor failure, immutable native constraints, invalid-update atomicity,
RGB/RGBA values, duplicate tree IDs and per-window overlay limits. They establish
the basic wrapper contracts; they do not test every upstream builder option.

Four additional native scenarios extend the original six below:

1. **Light workspace:** real mouse activation invokes the async Python handler;
   native snapshots contain `Filled: Buy 10 NVDA` and the appended order row.
2. **Dark workspace:** the same behavior with native dark appearance.
3. **Component gallery:** constructs and renders native inputs, selection,
   table, date/color controls, carousel, overlays and five chart families, with
   no reported application error. This checks mounting/rendering; it does not
   establish exhaustive interaction coverage for every control.
4. **Native overlays:** mouse activation opens the Kit dialog and sheet;
   Escape dismisses each, with native close mirrored to Python values.

All scenarios also verify successful native shutdown and an empty error list.
The original text editing/undo, ordered activation, async cancellation and error
scenarios still pass. Actual captured windows were visually inspected and copied
without image editing into [docs/screenshots](screenshots) for README display:
[dark workspace](screenshots/workspace-dark.png),
[light workspace](screenshots/workspace-light.png), and
[gallery](screenshots/gallery-light.png). Rerunning the native script regenerates
local captures and snapshots under the gitignored `artifacts/` directory.

The measured scope is Linux/X11 software Vulkan, a fixed tree and one window.
Complete Kit APIs, macOS/Windows/Wayland, portable wheels and large-data
performance remain unverified. See [component coverage](component-coverage.md)
for the implemented contracts and remaining Kit families.

## Original first-milestone evidence

The results below record the original four-control implementation; the expanded
catalog results above supersede its test counts and scope.

## Upstream compatibility

All four requested repositories were cloned and inspected. Immutable references
and the NiceGUI/Flet implementation comparison are in
[architecture.md](architecture.md) and [upstream-lock.json](upstream-lock.json).

The published `gpui-pre-0.3.7/Cargo.toml.orig` declares Zed revision
`1a28cff4b409169bac058bca40dfbfeb7621d19b`. The cloned Zed repository was checked
out at that revision. Its `app/context.rs`, `app/async_context.rs` and
`app/entity_map.rs` are byte-identical to the downloaded snapshot's corresponding
files. The resolved dependency tree has one GPUI instance at 0.3.7, shared by
Kit, Base, Component and the platform/renderer crates. Cargo.lock retains exact
registry checksums and git commits.

`cargo check --locked`, `cargo clippy --locked -- -D warnings`, and
`cargo fmt --check` passed. `maturin develop --uv` built and installed a real
`cp312-abi3-linux_x86_64` extension. This was not a mock backend. The initial
development build took 3m 32s after dependency/toolchain setup.

The standard **`uv sync --locked`** path also passed and installed the optimized
extension; its initial release build took 13m 26s. Final checks ran against that
installation: `uv run --locked pytest -q` reported **27 passed, 6 skipped** (the
native scenarios are opt-in), followed by the native script's **6 passed in
6.40s**. Rust check/Clippy/format and Python lint/format all passed afterwards.

## Python and bridge behavior

27 tests passed in `tests/test_controls.py` and `tests/test_bridge.py`:

* Context-manager and explicit-child composition, task-local contexts, context
  restoration after errors, stable IDs, unique ownership and cycle rejection.
* Explicit State propagation, two-way input binding, equality guards and
  subscription disposal.
* Early property/handler validation and no orphan controls after failed callback
  registration; main-thread and existing-asyncio-loop entry restrictions.
* Real Rust tree/property schema validation, duplicate/invalid IDs, invalid
  batches, and explicit bounded-command-queue overload.
* A blocked Rust event receiver releases the GIL and wakes when closed.
* Missing-display startup failure shuts down the Python loop and executor thread
  and rejects reuse of the same Application.

Python Ruff lint and format checks passed.

## Native integration

`scripts/test-native.sh` launches a real X11 server using Xvfb and a real Vulkan
renderer using Mesa Lavapipe. Each scenario runs the installed extension in a
fresh Python process, types/clicks through XTest, and uses the normal public
Application snapshot barrier for assertions. It does not inject events into a
mock UI or invoke a click callback directly.

All six native scenarios passed together against the optimized uv installation
in **6.40s**. The scenarios cover:

1. **Synchronous Python callback:** type `Ada`, click the Kit button, apply a
   coalesced label update, and verify native `Hello, Ada!`. The sync callback
   returns an awaitable that reads the native snapshot.
2. **Async binding and keyboard activation:** type `Ada`, Tab to the button,
   activate with Space; verify a disabled button and `Preparing greeting…`, then
   a re-enabled button and `Hello, Ada!` after an asyncio sleep.
3. **Close during an awaiting handler:** close the native window during a long
   async wait; verify the handler's finally block runs and no Python callback or
   asyncio executor thread remains after run returns.
4. **Callback failure:** a Python ValueError reaches on_error and app.errors,
   and app.close terminates the native loop cleanly.
5. **Native editing ownership:** initialize the native value from Python, type
   `X` to get `AdaX`, activate Python's label update, refocus and Undo; verify
   the native value, bound Python State, and label return to `Ada`. This checks
   that native edits do not get echoed through set_value and destroy history.
6. **Queued activation order:** deliberately pause Python dispatch while native
   input and two activations queue. The first callback reads `Ada`, the second
   reads `Grace`, and the final native label is `Hello, Grace!`. Callbacks begin
   with their activation snapshot before later input events advance mirrors.

The Xvfb harness was corrected after initial reruns exposed a stale display-file
race. The Xlib close request now uses a server round-trip before disconnecting.
The library does not substitute a fake window when native startup fails.

Actual captured native windows were visually inspected. See
`artifacts/sync.png` and
`artifacts/async.png` for the rendered outcome, and
the corresponding JSON files for native state. Artifacts are local and
gitignored; regenerate them with the native test script.

## Scope of the evidence

Validated: native X11/Vulkan rendering, real Kit controls, typing and undo,
pointer and keyboard activation, foreground updates from Python, queued callbacks,
asyncio waits, explicit state binding, failure handling and clean Python shutdown.

The measurements above come from Linux/X11. Subsequent release CI validated
installed wheels on Linux, macOS and Windows on x64 and ARM64, including native
window/state/lifecycle smoke tests on macOS and Windows. See the
[release matrix](releases.md) for exact Python versions and coverage.

Still outside this evidence: Wayland, hardware GPUs, high-DPI/multiple monitors,
AT-SPI interaction on a full desktop, IME/composition, manylinux portability,
multiwindow or high-volume performance. Coordinates are used
as an Xvfb fallback because this environment lacks a desktop accessibility bus;
screenshots substantiate rendered facts and snapshots substantiate native state.

The initial maturin development install warned that patchelf was unavailable.
The installed extension's runtime dependencies resolve in this workspace, but
that is not an auditwheel or portable-wheel certification. Release CI now audits
Linux dependencies; the Linux wheels retain system libraries and Linux tags.
Version `0.1.0` is published on PyPI with macOS/Windows wheels and a source archive;
Linux wheels are available on GitHub Releases. The project is licensed under MIT.
