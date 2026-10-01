"""A small paper-trading workspace, written entirely with the public Python API."""

from __future__ import annotations

import argparse
import asyncio
import inspect
from dataclasses import dataclass

from market import SimulatedMarket

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
    tape: Table
    feed: Label
    price: Label
    market: SimulatedMarket


def create_workspace(
    theme: str = "dark", *, streaming: bool = True, on_start=None, on_error=None
) -> Workspace:
    market = SimulatedMarket()

    async def stream() -> None:
        while True:
            await asyncio.sleep(0.65)
            market.advance()
            with app.batch():
                watchlist.rows = market.quotes()
                update_quote(symbol_select.value)
                tape.rows = market.trades[:4]
                feed.text = f"Simulated live feed · Tick {market.tick:03} · {market.histories['NVDA'][-1][0]}"

    async def started(event) -> None:
        async def external() -> None:
            if on_start is not None:
                result = on_start(event)
                if inspect.isawaitable(result):
                    await result

        if streaming:
            await asyncio.gather(stream(), external())
        else:
            await external()

    app = Application(
        title="gpyui · Paper trading",
        width=1180,
        height=790,
        theme=theme,
        on_start=started,
        on_error=on_error,
    )

    def update_quote(symbol: str) -> None:
        instrument.text = symbol
        price.text = f"${market.prices[symbol]:,.2f}"
        change.text = f"{market.change(symbol):+.2f}%"
        change.variant = "success" if market.change(symbol) >= 0 else "danger"
        chart.data = market.series(symbol, period.value)

    def select_symbol(symbol: str) -> None:
        update_quote(symbol)
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
        symbol = symbol_select.value
        action = "Buy" if side.value == 0 else "Sell"
        order.disabled = True
        status.text = "Placing paper order…"
        await asyncio.sleep(0.15)
        positions.rows = [*positions.rows, [symbol, action, str(count), f"${market.prices[symbol]:.2f}"]]
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
                Label("Simulated markets · Built in Python").style(color="muted_foreground", font_size=13)
                Avatar("GP")
        Separator()
        with Row().style(full_width=True, flex=1, align="stretch", gap=20):
            with Column().style(width=220, gap=16):
                Label("Watchlist").style(bold=True, font_size=16)
                watchlist = Table(
                    columns=["Symbol", "Price", "Change"],
                    rows=market.quotes(),
                    column_width=73,
                    on_change=lambda event: select_symbol(list(market.prices)[event.value]),
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
                        Label("Local simulation · Accelerated quotes").style(
                            color="muted_foreground", font_size=12
                        )
                    with Row():
                        price = Label("$192.60").style(font_size=26, bold=True)
                        change = Tag("+0.82%", variant="success")
                period = Tabs(
                    ["Intraday", "1 week", "1 month"],
                    on_change=lambda: setattr(
                        chart, "data", market.series(symbol_select.value, period.value)
                    ),
                )
                chart = LineChart(market.series("NVDA")).style(full_width=True, height=250)
                with Row().style(full_width=True, gap=12, align="stretch"):
                    with Column().style(flex=1, gap=12):
                        Label("Market tape").style(font_size=16, bold=True)
                        tape = Table(columns=["Symbol", "Side", "Size", "Price"], column_width=73)
                        tape.style(full_width=True, height=175)
                    with Column().style(flex=1, gap=12):
                        Label("Paper orders").style(font_size=16, bold=True)
                        positions = Table(
                            columns=["Symbol", "Side", "Quantity", "Price"],
                            column_width=73,
                            rows=[
                                ["NVDA", "Buy", "10", "$190.20"],
                                ["AAPL", "Buy", "5", "$253.80"],
                            ],
                        ).style(full_width=True, height=175)
            with Column().style(width=250, gap=16):
                with GroupBox("New paper order").style(full_width=True):
                    Label("Symbol").style(font_size=12, color="muted_foreground")
                    symbol_select = Select(
                        list(market.prices), value="NVDA", on_change=lambda e: select_symbol(e.value)
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
            feed = Label(
                "Simulated live feed · Starting…" if streaming else "Local demo · Static market data"
            )
            Label("Python API / Native GPUI Kit")
    return Workspace(
        app,
        watchlist,
        chart,
        symbol_select,
        quantity,
        side,
        positions,
        status,
        order,
        tape,
        feed,
        price,
        market,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=("light", "dark"), default="dark")
    parser.add_argument("--static", action="store_true", help="Disable the local simulated market stream")
    args = parser.parse_args()
    create_workspace(args.theme, streaming=not args.static).app.run()
