# Charts

Generated Python API reference from the repository (manifest version 0.6.0).
Follows the repository manifest; check [release status and coverage](../coverage.md) against your installed version.

## LineChart

Native line plot with data-following domain.

### Runnable example

```python
import gpyui as ui

control = ui.LineChart([["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]).style(
    height=190, full_width=True
)

app = ui.Application(ui.Column([control]), title="LineChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Data points are [label, value]. Reassign data to update the native plot.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L670) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## AreaChart

A native filled area plot.

### Runnable example

```python
import gpyui as ui

control = ui.AreaChart([["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]).style(
    height=190, full_width=True
)

app = ui.Application(ui.Column([control]), title="AreaChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L679) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## BarChart

A native bar plot.

### Runnable example

```python
import gpyui as ui

control = ui.BarChart([["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]).style(
    height=190, full_width=True
)

app = ui.Application(ui.Column([control]), title="BarChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L683) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## PieChart

A native pie plot with nonnegative values.

### Runnable example

```python
import gpyui as ui

control = ui.PieChart([["Mon", 12], ["Tue", 18], ["Wed", 15], ["Thu", 24], ["Fri", 28]]).style(
    height=190, full_width=True
)

app = ui.Application(ui.Column([control]), title="PieChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Each point is [label, nonnegative value].

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L687) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)

## CandlestickChart

Native OHLC candles.

### Runnable example

```python
import gpyui as ui

control = ui.CandlestickChart(
    [["Mon", 10, 18, 8, 16], ["Tue", 16, 21, 12, 14], ["Wed", 14, 25, 13, 24]]
).style(height=190, full_width=True)

app = ui.Application(ui.Column([control]), title="CandlestickChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

### Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](https://gtrefalt.github.io/gpyui/reference/core/).

### Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

### Contract and limits

Candles are [label, open, high, low, close], with low <= open/close <= high.

All controls accept [pixel layout and semantic theme styling](../styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L696) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../coverage.md)
