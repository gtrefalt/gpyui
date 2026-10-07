# Vendored native theme

`macos-classic.json` is an unchanged copy of Longbridge GPUI Kit’s
[theme at revision c1bda59e67f46266991a230ae94f749af496af2a](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/themes/macos-classic.json).
License: MIT (see GPUI Kit’s notice in `src/gpyui/THIRD_PARTY_NOTICES.txt`).
SHA-256: `d004038f480a44a68c82d82e08143bb0d919a1c9280524b68f8a9a9264c460dc`.

Both Classic configs are compiled into Rust. Kit parses colors and highlights;
gpyui supplies Kit’s omitted scalar defaults so switching from a custom theme
cannot leak typography, radius or shadows. Explicit Python overrides then apply.
