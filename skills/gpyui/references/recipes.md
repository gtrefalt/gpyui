# Complete application recipes

These scripts are bundled with the skill, so they work in an application project
without a checkout of gpyui. Install gpyui in your project using
[the setup guide](runtime.md), copy the chosen script to your project and run it
with `uv run python <script>.py` (or `python <script>.py` with pip).
Do not point uv at the library checkout when you intend to use a released wheel.

| Recipe | File | What to preserve |
| --- | --- | --- |
| Profile form | [profile.py](../scripts/profile.py) | State binding, submission-time snapshot, validation, to_thread I/O, recoverable failure, finally restoration |
| Simulated stream | [dashboard.py](../scripts/dashboard.py) | on_start tracked coroutine, bounded deque, table/plot reassignment, synchronous batch, cancellation-safe teardown |
| Confirmation | [dialog.py](../scripts/dialog.py) | Dialog mounted before run, specific affected object, explicit open/close and cancel command |

The profile recipe writes `profile.json` in the current directory. Replace that
worker with your application's persistence layer; keep it free of UI mutations.
Cancellation of `asyncio.to_thread` does not stop a function that is already
executing in the worker thread. Use an atomic persistence strategy when partial
writes matter; do not mistake cancellation for rollback.

The dashboard is deliberately simulated, with a deterministic random seed and
a maximum of 60 points at two display updates per second. Replace its input
with your async client while preserving bounds and ownership. No unbounded
background task or arbitrary threaded mutation is necessary. Its fixed table
columns and basic chart are within the current Python wrapper's capabilities.

The dialog recipe changes only local demo status. Replace the operation with
your actual command; an asynchronous delete needs disabled/busy handling and
error feedback before reporting success. The native dialog's Boolean value
tracks dismissal through its change event.

## Verification

All three scripts can be imported to construct the control tree without starting
a window, using `if __name__ == "__main__": app.run()`. That catches unsupported
properties, invalid constructor values and parenting mistakes. Test domain logic
and mocked I/O separately. Then launch each application in a fresh process on a
native desktop to exercise editing, activation, layout and shutdown.

The gpyui repository runs skill reference/snippet checks without compiling Rust
and tests the form's success, failure and cancellation behavior. Library native
interaction tests remain distinct from these construction and logic checks.

For a larger app, separate model/data functions from builders and callbacks.
Pass stable model/handle references to callbacks; build each control once. Use
State for values that need bindings, plain Python objects for domain data that
does not need observation, and explicit collection assignment for rendered
snapshots. Do not create an additional rendering or lifecycle framework on top.
