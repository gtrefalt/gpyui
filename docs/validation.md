# First milestone validation

Validation target: Debian 13, x86_64 Linux, Python 3.12.14, Rust 1.99.0,
GPUI Kit 0.7.0 at the pinned git revision, GPUI snapshot 0.3.7.

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
[`artifacts/sync.png`](../artifacts/sync.png) and
[`artifacts/async.png`](../artifacts/async.png) for the rendered outcome, and
the corresponding JSON files for native state. Artifacts are local and
gitignored; regenerate them with the native test script.

## Scope of the evidence

Validated: native X11/Vulkan rendering, real Kit controls, typing and undo,
pointer and keyboard activation, foreground updates from Python, queued callbacks,
asyncio waits, explicit state binding, failure handling and clean Python shutdown.

Not validated: macOS, Windows, Wayland, hardware GPUs, high-DPI/multiple monitors,
AT-SPI interaction on a full desktop, IME/composition, wheel portability,
multiwindow, dynamic topology or high-volume performance. Coordinates are used
as an Xvfb fallback because this environment lacks a desktop accessibility bus;
screenshots substantiate rendered facts and snapshots substantiate native state.

The initial maturin development install warned that patchelf was unavailable.
The installed extension's runtime dependencies resolve in this workspace, but
that is not an auditwheel or portable-wheel certification. No wheel was published.
Package-name availability and the project's distribution license remain undecided.
