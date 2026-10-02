# Simulated trading stream

![Native workspace with simulated quotes and paper fills](../screenshots/workspace-stream.gif)

A small trading workspace composed entirely through the public Python API.
The 12-second recording shows changing quotes, a rolling chart, the market tape,
paper Buy/Sell fills and switching from NVDA to AAPL.

```bash
uv run python examples/workspace.py --theme dark
uv run python examples/workspace.py --theme light
uv run python examples/workspace.py --static
```

## What runs where

Python's seeded `SimulatedMarket` generates local quotes and trades every 650 ms.
The `on_start` coroutine batches watchlist rows, quote text, change tag, chart
data, tape rows and the feed counter. The native window stays responsive while
the coroutine awaits the next tick. Native close cancels the stream.

Rust retains the native controls and renders Kit's chart/table builders. The
order button queues an async Python callback that validates quantity, captures
the chosen symbol/side, waits for a simulated fill, and appends a paper order at
the current generated price. A native notification confirms the fill.

All data and trades are simulated locally. No market-feed or broker connections
are made. The example is intended to demonstrate Python UI composition and
streaming updates.

## Record the real window

Install Xvfb, xdotool, ImageMagick and FFmpeg with the native prerequisites,
then run:

```bash
uv run python scripts/record-workspace.py
```

The recorder starts a free Xvfb display if needed, sends real mouse/keyboard
events, records 120 native frames at 10 fps, and checks snapshots for both fills,
the changed chart and clean shutdown. The GIF is written to
`docs/screenshots/workspace-stream.gif`; source video and logs are gitignored.

[Workspace source](https://github.com/gtrefalt/gpyui/blob/main/examples/workspace.py) ·
[Simulation source](https://github.com/gtrefalt/gpyui/blob/main/examples/market.py) ·
[Recorder source](https://github.com/gtrefalt/gpyui/blob/main/scripts/record-workspace.py)
