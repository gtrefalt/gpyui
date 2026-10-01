"""A small paper-trading workspace, written entirely with the public Python API."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass

from gpyui import (
    Application,
    Avatar,
    Button,
    Column,
    DescriptionList,
    GroupBox,
    Icon,
    Label,
    LineChart,
    Link,
    NumberInput,
    RadioGroup,
    Row,
    Select,
    Separator,
    StatusBar,
    Switch,
    Table,
    Tabs,
    Tag,
)

QUOTES = [
    ["NVDA", "192.60", "+0.82%"],
    ["AAPL", "255.30", "+0.50%"],
    ["MSFT", "522.06", "+0.24%"],
    ["TSLA", "439.89", "+1.00%"],
    ["AMD", "164.82", "−0.31%"],
    ["GOOG", "245.10", "+0.67%"],
]
PRICES = dict((row[0], float(row[1])) for row in QUOTES)


def series(symbol: str, period: int = 0) -> list[list[str | float]]:
    price = PRICES[symbol]
    offsets = [-4.2, -3.5, -3.9, -2.8, -1.7, -2.1, -1.1, -1.9, -0.9, -0.3, -0.8, 0]
    return [
        [f"{9 + i // 4:02}:{(i % 4) * 15:02}", round(price + d * (1 + period * 0.3), 2)]
        for i, d in enumerate(offsets)
    ]


@dataclass
class Workspace:
    app: Application
    watchlist: Table
    chart: LineChart
    symbol: Select
    quantity: NumberInput
    side: RadioGroup
    positions: Table
    status: Label
    order: Button


def create_workspace(theme: str = "dark", *, on_start=None, on_error=None) -> Workspace:
    app = Application(
        title="gpyui · Paper trading",
        width=1180,
        height=790,
        theme=theme,
        on_start=on_start,
        on_error=on_error,
    )

    def select_symbol(symbol: str) -> None:
        instrument.text = symbol
        price.text = f"${PRICES[symbol]:,.2f}"
        chart.data = series(symbol, period.value)
        symbol_select.value = symbol
        status.text = f"Ready to trade {symbol}"

    async def place_order() -> None:
        try:
            count = int(quantity.value)
        except ValueError:
            count = 0
        if count <= 0:
            status.text = "Enter a whole quantity above zero."
            return
        order.disabled = True
        status.text = "Placing paper order…"
        await asyncio.sleep(0.15)
        symbol = symbol_select.value
        action = "Buy" if side.value == 0 else "Sell"
        positions.rows = [*positions.rows, [symbol, action, str(count), f"${PRICES[symbol]:.2f}"]]
        status.text = f"Filled: {action} {count} {symbol}"
        order.disabled = False
        if not remember.value:
            quantity.value = ""
        app.notify(status.text, title="Paper order", variant="success")

    with app, Column().style(full_width=True, full_height=True, gap=16):
        with Row().style(full_width=True, justify="between"):
            with Row():
                Icon("chart-no-axes-combined").style(width=24, height=24, color="primary")
                Label("Market workspace").style(font_size=22, bold=True)
                Tag("Paper account", variant="secondary")
            with Row():
                Label("A quieter desktop, built in Python").style(color="muted_foreground", font_size=13)
                Avatar("GP")
        Separator()
        with Row().style(full_width=True, flex=1, align="stretch", gap=20):
            with Column().style(width=220, gap=16):
                Label("Watchlist").style(bold=True, font_size=16)
                watchlist = Table(
                    columns=["Symbol", "Price", "Change"],
                    rows=QUOTES,
                    column_width=73,
                    on_change=lambda event: select_symbol(QUOTES[event.value][0]),
                )
                watchlist.style(full_width=True, height=340)
                Separator()
                Label("Paper account").style(bold=True)
                DescriptionList([["Cash", "$25,000.00"], ["Buying power", "$50,000.00"]])
                Link("GPUI Kit ↗", href="https://gpui-kit.com").style(color="primary")
            with Column().style(flex=1, gap=12):
                with Row().style(full_width=True, justify="between"):
                    with Column():
                        instrument = Label("NVDA").style(font_size=20, bold=True)
                        Label("NVIDIA · Demo prices").style(color="muted_foreground", font_size=12)
                    with Row():
                        price = Label("$192.60").style(font_size=26, bold=True)
                        Tag("+0.82%", variant="success")
                period = Tabs(
                    ["Intraday", "1 week", "1 month"],
                    on_change=lambda: setattr(chart, "data", series(symbol_select.value, period.value)),
                )
                chart = LineChart(series("NVDA")).style(full_width=True, height=250)
                with Row().style(full_width=True, justify="between"):
                    Label("Paper orders").style(font_size=16, bold=True)
                    Tag("Local simulation")
                positions = Table(
                    columns=["Symbol", "Side", "Quantity", "Price"],
                    rows=[
                        ["NVDA", "Buy", "10", "$190.20"],
                        ["AAPL", "Buy", "5", "$253.80"],
                    ],
                ).style(full_width=True, height=175)
            with Column().style(width=250, gap=16):
                with GroupBox("New paper order").style(full_width=True):
                    Label("Symbol").style(font_size=12, color="muted_foreground")
                    symbol_select = Select(
                        list(PRICES), value="NVDA", on_change=lambda e: select_symbol(e.value)
                    )
                    side = RadioGroup(["Buy", "Sell"])
                    Label("Quantity").style(font_size=12, color="muted_foreground")
                    quantity = NumberInput("10", placeholder="Shares")
                    Label("Order type").style(font_size=12, color="muted_foreground")
                    Tag("Market")
                    remember = Switch("Remember quantity", value=True)
                    order = Button("Place paper order", variant="primary", on_click=place_order)
                status = Label("Ready to trade NVDA").style(font_size=12, color="muted_foreground")
                Separator()
                DescriptionList([["Session", "Demo"], ["Currency", "USD"], ["Execution", "Simulated"]])
        with StatusBar().style(full_width=True):
            Icon("circle-check").style(width=14, height=14, color="success")
            Label("Local demo · Sample market data")
            Label("Python API / Native GPUI Kit")
    return Workspace(app, watchlist, chart, symbol_select, quantity, side, positions, status, order)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("light", "dark"), default="dark")
    create_workspace(parser.parse_args().theme).app.run()
