# Image

Full-color images decoded, cached and rendered natively.

![Native Image preview](../screenshots/components/image.png?v=a192dfe0da56)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.Image(
    b'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="160" viewBox="0 0 360 160"><rect width="360" height="160" fill="#e0f2fe"/><circle cx="290" cy="36" r="18" fill="#fbbf24"/><path d="M0 160L110 45L230 160Z" fill="#0f766e"/><path d="M130 160L245 70L360 160Z" fill="#115e59"/></svg>',
    fit="cover",
).style(width=480, height=180, radius=12)

app = ui.Application(ui.Column([control]), title="Image", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `source` | `null` | str / PathLike / bytes / ImageSource / None; reads back as ImageSource / None | Assignment |
| `fit` | `"contain"` | contain · cover · fill · scale_down · none | Assignment |
| `grayscale` | `false` | bool | Assignment |
| `aspect_ratio` | `0` | nonnegative number; 0 uses the intrinsic ratio | Assignment |
| `loading_text` | `"Loading image…"` | str | Assignment |
| `error_text` | `"Image unavailable"` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

`on_load` receives `{width, height, frames}` in Event.value; `on_error` receives an error string. Callbacks may be sync or async and run on the owned callback loop. `reload()` retries an unchanged source. The source getter returns an immutable ImageSource or None. Source replacement discards stale callbacks. See [Images](../guide/images.md) for source rules, ownership, placeholders and video limits.

## Contract and limits

Accepts paths, HTTP(S) URLs, encoded bytes and ImageSource.asset(key). Assign source to replace, None to clear, or call reload() to retry. on_load receives width/height/frame count; on_error receives an error message. Animated GIF/WebP are images, not a video streaming API. See the Images guide for ownership, loading and source rules.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/images.py#L88) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
