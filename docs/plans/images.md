# Image binding: verified sources and implementation

## Compatibility

The current dependency baseline is Kit 0.7.1 at revision
`c1bda59e67f46266991a230ae94f749af496af2a` and GPUI `0.3.8`.
The original image implementation used Kit 0.7.0 / GPUI 0.3.7; see
[validation](../validation.md) for dependency-upgrade checks.
Kit [re-exports GPUI](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/crates/kit/src/lib.rs).
Image is the native `img()` element, not a separate themed Kit component class.
The pinned [Images guide](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/website/docs/image.md)
and [Image patterns](https://github.com/longbridge/gpui-kit/blob/c1bda59e67f46266991a230ae94f749af496af2a/website/component/image.md)
match `gpui-pre 0.3.8/src/elements/img.rs`, rather than assuming
the live site's newer release matches the pin.

Verified native APIs: `ImageSource`, `Resource::{Path, Uri, Embedded}`,
`ImageAssetLoader::load`, `img`, `StyledImage::{object_fit, grayscale,
with_loading, with_fallback}`, stable element IDs and `RenderImage` frame data.
The native application has no working HTTP client by default. We add the matching
`gpui-pre-reqwest-client = 0.3.8` and install it before starting the window;
base64 `0.22.1` is pinned for the existing JSON transport. Cargo.lock records
their resolved dependency graph.

Pixel testing found a documentation mismatch: the pinned ObjectFit::None
implementation uses the element's origin (top left), although upstream's guide
calls it centered. The Python guide records the verified implementation.

## Architecture and delivered surface

1. Python validates source descriptors, fit and aspect ratio before attachment.
   Strings mean files/HTTP(S); embedded assets use `ImageSource.asset` explicitly.
2. Rust retains one image entity per control. It starts GPUI's loader on the
   background executor when first rendered, then owns the decoded frame result.
3. Encoded bytes are registered temporarily in a composite AssetSource which
   also preserves all Kit bundled assets. This reuses GPUI's exact decoder,
   including animated GIF/WebP and full-color SVG, without a Python codec.
4. The result is passed to the real `img()` through a Rust custom source. Its
   stable ID includes a replacement revision, resetting animation/loading state
   on replacement while preserving the Python control identity.
5. Native completion events cross the existing transport to the owned asyncio
   loop. Native cancellation and Python revision checks discard stale work.
6. Results are scoped to the current source, not an application-wide history.
   Hide/show retains the result; replacement, reload and disposal release it.
   `App::drop_image(..., Some(window))` explicitly evicts all native frame atlas
   entries; merely dropping an Arc would leave GPU textures cached.

Acceptance covers paths, encoded PNG/GIF, Kit SVG assets, local HTTP, corrupt and
missing sources, same-path retry through a real button, late URL completion,
grayscale, displayed pixels and animation, hide/show/moves/disposal, and untouched
native editor undo. Installed-wheel smoke covers image loading/replacement/retry
on the release platforms. The catalog and viewer have real native light PNGs.

## Deferred work

Shared caches, durable HTTP caches, authenticated source providers, custom
placeholder controls and image avatars can extend this binding separately.
Video needs a dedicated native capture/decoder and bounded frame handoff; the
JSON encoded-image source is not suitable for high-rate video. No video format,
camera or playback capability is claimed by this milestone.
