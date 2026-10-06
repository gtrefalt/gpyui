# CandlestickChart

Native OHLC candles.

![Native CandlestickChart preview](../screenshots/components/candlestick-chart.png?v=c9ab63153cea)

A real Linux/X11 native capture in light appearance. The same control also supports the initial dark theme.

## Runnable example

```python
import gpyui as ui

control = ui.CandlestickChart(
    [["Mon", 10, 18, 8, 16], ["Tue", 16, 21, 12, 14], ["Wed", 14, 25, 13, 24]]
).style(height=190, full_width=True)

app = ui.Application(ui.Column([control]), title="CandlestickChart", width=640, height=340)
app.run()
```

Run this in a fresh Python process on a desktop with the native build installed.

## Properties

| Property | Default | Type / accepted values | Update |
| --- | --- | --- | --- |
| `data` | `[]` | list[chart point] | Assignment |

All controls support `visible` and `dispose()`. Hiding or detaching retains native state; disposal permanently releases it. See [Control](../reference/core.md).

## Events and state

This wrapper exposes no Python activation/change handler. Update its mutable properties by assignment from a running callback. Native behavior remains in Rust.

## Contract and limits

Candles are [label, open, high, low, close], with low <= open/close <= high.

All controls accept [pixel layout and semantic theme styling](../guide/styling.md) through `.style(...)`. Collections are copied on assignment/read: reassign them to submit updates.

[Python implementation](https://github.com/gtrefalt/gpyui/blob/main/src/gpyui/widgets.py#L525) · [Native builders](https://github.com/gtrefalt/gpyui/blob/main/src/kit.rs) · [Full coverage and remaining Kit APIs](../component-coverage.md)
