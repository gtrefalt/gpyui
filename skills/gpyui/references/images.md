# Images (0.6.0)

This binding is available from gpyui 0.6.0.
Image uses Kit's actual GPUI `img()`, with native loading/decoding/rendering.

```python
import gpyui as ui

status = ui.Label("Loading image…")
image = ui.Image(
    "photos/landscape.png",
    fit="contain",
    on_load=lambda event: setattr(status, "text", f"Loaded {event.value['width']} px wide"),
    on_error=lambda event: setattr(status, "text", "Check the file and retry."),
).style(width=480, height=270, radius=12, background="muted")
app = ui.Application(
    ui.Column([image, status, ui.Button("Retry", on_click=image.reload)]),
    title="Image preview",
    width=540,
    height=400,
    theme="light",
)
app.run()
```

- A string is a local path or HTTP(S) URL. PathLike works too. Files become
  absolute at assignment. Use `ImageSource.asset("icons/inbox.svg")` for an exact
  bundled key; a relative string is never implicitly an asset lookup.
- Encoded bytes (nonempty, at most 32 MiB) use the same native decoder, including
  PNG/JPEG, full-color SVG and animated GIF/WebP. None clears the image. The getter
  returns an immutable ImageSource(kind, value) or None. There is no raw-frame API.
- Reserve size with width/height styles, or width plus aspect_ratio. Zero ratio
  uses the image's intrinsic ratio. Radius rounds the image itself.
- Fit is contain, cover, fill, scale_down or none. Grayscale, fit and style can
  change without loading again. loading_text/error_text are native placeholders;
  the loading placeholder appears after GPUI's 200 ms delay.
- on_load receives Event.value = {width, height, frames}; on_error receives a
  message string. Both accept zero/one arguments and sync/async callbacks on the
  owned callback loop. Exceptions raised by handlers follow Application.on_error.
- Assign source to replace it. reload() retries an unchanged location. Old
  results and callbacks are discarded. Hide/detach retains the result; suppressed
  completion events are not replayed on show. dispose() releases pending delivery
  and the current result. Native editing controls are untouched by image changes.
- Results are cached per control/current source; separate controls decode
  separately. Shared/durable caches, custom headers, image avatars and custom
  placeholder trees are not exposed.
- Use Icon for theme-following monochrome glyphs. Image preserves SVG colors.

For occasional snapshots, hand external thread results to app.call_soon() and
bound both update rate and retained history. Repeated encoded bytes cross
JSON/base64 and decode each image; this is not efficient video streaming. There
is no camera/MP4/RTSP/HLS/audio pipeline. Live video requires native capture and
decoding with bounded frame delivery, dropped old frames and explicit disposal.
