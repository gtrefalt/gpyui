# Content

Generated Python API reference for gpyui 0.5.0.

## Tag

Native text tags with semantic variants.

### Runnable example

```python
import gpyui as ui

control = ui.Tag("Ready", variant="success")

app = ui.Application(ui.Column([control]), title="Tag", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `variant` | `"secondary"` | primary · secondary · success · warning · danger · info | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L396) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Badge

Native count badges.

### Runnable example

```python
import gpyui as ui

control = ui.Badge(count=3, text="Inbox")

app = ui.Application(ui.Column([control]), title="Badge", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `count` | `0` | nonnegative int | Assignment |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L401) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Avatar

Native initials generated from a name.

### Runnable example

```python
import gpyui as ui

control = ui.Avatar("Ada Lovelace")

app = ui.Application(ui.Column([control]), title="Avatar", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `name` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Initials are exposed in this wrapper; image avatars remain future work.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L406) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Image

Full-color images decoded, cached and rendered natively.

### Runnable example

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

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `source` | `null` | str / PathLike / bytes / ImageSource / None; reads back as ImageSource / None | Assignment |
| `fit` | `"contain"` | contain · cover · fill · scale_down · none | Assignment |
| `grayscale` | `false` | bool | Assignment |
| `aspect_ratio` | `0` | nonnegative number; 0 uses the intrinsic ratio | Assignment |
| `loading_text` | `"Loading image…"` | str | Assignment |
| `error_text` | `"Image unavailable"` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

`on_load` receives `{width, height, frames}` in Event.value; `on_error` receives an error string. Callbacks may be sync or async and run on the owned callback loop. `reload()` retries an unchanged source. The source getter returns an immutable ImageSource or None. Source replacement discards stale callbacks. See [Images](../images.md) for source rules, ownership, placeholders and video limits.

### Contract and limits

Accepts paths, HTTP(S) URLs, encoded bytes and ImageSource.asset(key). Assign source to replace, None to clear, or call reload() to retry. on_load receives width/height/frame count; on_error receives an error message. Animated GIF/WebP are images, not a video streaming API. See the Images guide for ownership, loading and source rules.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/images.py#L88) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Markdown

Native rich text from Markdown.

### Runnable example

```python
import gpyui as ui

control = ui.Markdown(
    "### Native rich text\n**Bold**, *emphasis*, and `inline code`.\n\nRendered by GPUI Kit."
)

app = ui.Application(ui.Column([control]), title="Markdown", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Text rendering and selection stay native.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L689) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Html

Native rich text from supported HTML.

### Runnable example

```python
import gpyui as ui

control = ui.Html("<h3>Native rich text</h3><p><strong>Bold</strong> and <em>emphasis</em>.</p>")

app = ui.Application(ui.Column([control]), title="Html", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

This is Kit's native TextView HTML support, not an embedded browser or arbitrary webpage.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L694) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Bubble

Native bubble content composed in Python.

### Runnable example

```python
import gpyui as ui

control = ui.Bubble(children=[ui.Label("Hello from a Kit bubble.")])

app = ui.Application(ui.Column([control]), title="Bubble", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

This control has no component-specific constructor properties.

Accepts `children=[...]`, a `with` block, and runtime `add`, `insert`, `remove`, `clear`, `set_children` or assignment to `children`. Each child has one parent. Reuse existing instances to preserve native state; see [runtime composition](../composition.md#dynamic-composition).

Construct explicit child lists outside a composition context, as in the example. Inside a `with` block, construct the parent first and then its children.

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L547) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Message

Native authored message presentation.

### Runnable example

```python
import gpyui as ui

control = ui.Message("Compose your app in Python.", author="gpyui")

app = ui.Application(ui.Column([control]), title="Message", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `author` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L552) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Marker

Native message/date marker.

### Runnable example

```python
import gpyui as ui

control = ui.Marker("Today")

app = ui.Application(ui.Column([control]), title="Marker", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `text` | `""` | str | Assignment |
| `loading` | `false` | bool | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L557) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)

## Attachment

Native attachment presentation.

### Runnable example

```python
import gpyui as ui

control = ui.Attachment("report.csv", description="Sample file attachment")

app = ui.Application(ui.Column([control]), title="Attachment", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `title` | `""` | str | Assignment |
| `description` | `""` | str | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Presentation is exposed; file download/open behavior is an application concern.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L562) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](https://gtrefalt.github.io/gpyui/component-coverage/)
