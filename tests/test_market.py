"""Simulation invariants, replay and independent workspace state."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from market import SimulatedMarket


def test_stream_replays_without_sharing_mutable_state():
    first, replay, untouched = SimulatedMarket(), SimulatedMarket(), SimulatedMarket()
    initial = untouched.quotes()
    for _ in range(20):
        first.advance()
        replay.advance()
    assert first.quotes() == replay.quotes()
    assert first.trades == replay.trades
    assert first.quotes() != initial
    assert untouched.quotes() == initial and untouched.trades == []


def test_long_stream_keeps_consistent_positive_prices_and_bounded_history():
    market = SimulatedMarket()
    for _ in range(1000):
        market.advance()
        for symbol, price, change in market.quotes():
            assert float(price) > 0
            assert abs(float(change.rstrip("%")) - market.change(symbol)) <= 0.0051
            for period in (0, 1, 2):
                history = market.series(symbol, period)
                assert len(history) == 12
                assert history[-1][1] == float(price)
        assert 1 <= len(market.trades) <= 5
        symbol, side, size, price = market.trades[0]
        assert symbol in market.prices and side in {"Buy", "Sell"}
        assert int(size) > 0 and float(price.lstrip("$")) == market.prices[symbol]
