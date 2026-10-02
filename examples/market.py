"""Seeded, local market simulation: no broker, sockets or real trading."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import cast

QUOTES = [
    ["NVDA", "192.60", "+0.82%"],
    ["AAPL", "255.30", "+0.50%"],
    ["MSFT", "522.06", "+0.24%"],
    ["TSLA", "439.89", "+1.00%"],
    ["AMD", "164.82", "−0.31%"],
    ["GOOG", "245.10", "+0.67%"],
]


class SimulatedMarket:
    """One accelerated quote/trade tick; histories and tape stay bounded."""

    def __init__(self, seed: int = 7):
        self.random = random.Random(seed)
        self.tick = 0
        self.prices = {row[0]: float(row[1]) for row in QUOTES}
        self.opening = {
            symbol: float(price) / (1 + float(change.replace("−", "-").rstrip("%")) / 100)
            for symbol, price, change in QUOTES
        }
        offsets = [-4.2, -3.5, -3.9, -2.8, -1.7, -2.1, -1.1, -1.9, -0.9, -0.3, -0.8, 0]
        self.histories = {
            symbol: [
                [f"{9 + i // 4:02}:{(i % 4) * 15:02}", round(price + delta, 2)]
                for i, delta in enumerate(offsets)
            ]
            for symbol, price in self.prices.items()
        }
        self.trades: list[list[str]] = []

    def advance(self) -> None:
        self.tick += 1
        stamp = (datetime(2026, 1, 1, 11, 45) + timedelta(minutes=15 * self.tick)).strftime("%H:%M")
        for symbol, price in self.prices.items():
            price = round(max(0.01, price * (1 + self.random.gauss(0, 0.002))), 2)
            self.prices[symbol] = price
            self.histories[symbol] = [*self.histories[symbol][-11:], [stamp, price]]
        symbol = self.random.choice(list(self.prices))
        self.trades.insert(
            0,
            [
                symbol,
                self.random.choice(["Buy", "Sell"]),
                str(self.random.choice([5, 10, 25, 50, 100])),
                f"${self.prices[symbol]:.2f}",
            ],
        )
        del self.trades[5:]

    def change(self, symbol: str) -> float:
        return (self.prices[symbol] / self.opening[symbol] - 1) * 100

    def quotes(self) -> list[list[str]]:
        return [
            [symbol, f"{price:.2f}", f"{self.change(symbol):+.2f}%"] for symbol, price in self.prices.items()
        ]

    def series(self, symbol: str, period: int = 0) -> list[list[str | float]]:
        price = self.prices[symbol]
        return [
            [stamp, round(price + (cast(float, value) - price) * (1 + period * 0.3), 2)]
            for stamp, value in self.histories[symbol]
        ]
