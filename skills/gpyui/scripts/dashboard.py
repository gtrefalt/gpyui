"""A bounded simulated stream, native chart/table, and tracked async lifecycle."""

import asyncio
from collections import deque
from datetime import datetime
from random import Random

from gpyui import Application, Button, Column, Label, LineChart, Row, State, Table

status = State("Connecting to simulated stream…")
random = Random(42)
history: deque[list[str | float]] = deque(maxlen=60)


async def stream() -> None:
    price = 100.0
    status.value = "Live · simulated data"
    try:
        while True:
            price = round(max(1, price + random.uniform(-0.8, 0.8)), 2)
            stamp = datetime.now().strftime("%H:%M:%S")
            history.append([stamp, price])
            with app.batch():
                summary.text = f"SIM · {price:.2f} USD"
                chart.data = list(history)
                table.rows = [["SIM", f"{price:.2f}", stamp]]
            await asyncio.sleep(0.5)
    finally:
        # No native commands here: the bridge may already be closing.
        history.clear()


app = Application(title="Simulated market", width=820, height=560, theme="light", on_start=stream)
with app, Column().style(padding=24, gap=16, full_width=True, full_height=True, align="stretch"):
    with Row().style(gap=12, justify="between", full_width=True):
        Label("Market monitor").style(font_size=22, bold=True)
        Button("Close monitor", variant="outline", on_click=lambda: app.close())
    summary = Label("Waiting for first quote").style(font_size=20, bold=True)
    chart = LineChart().style(height=240, full_width=True)
    table = Table(columns=["Symbol", "Price (USD)", "Updated"], rows=[], column_width=200).style(
        height=100, full_width=True
    )
    Label().bind_text(status).style(color="muted_foreground")

if __name__ == "__main__":
    app.run()
