"""Validated immutable creation options for GPUI's native window."""

from __future__ import annotations

import math
from dataclasses import dataclass


def _pixel(value: float, name: str, minimum: float = 1) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} requires finite pixels of at least {minimum:g}")


@dataclass(frozen=True)
class _WindowOptions:
    resizable: bool = True
    minimizable: bool = True
    movable: bool = True
    min_width: float = 240
    min_height: float = 160
    position: tuple[float, float] | None = None
    state: str = "normal"

    def __post_init__(self) -> None:
        for key in ("resizable", "minimizable", "movable"):
            if type(getattr(self, key)) is not bool:
                raise TypeError(f"{key} requires bool")
        _pixel(self.min_width, "min_width")
        _pixel(self.min_height, "min_height")
        if self.position is not None:
            if not isinstance(self.position, tuple) or len(self.position) != 2:
                raise TypeError("position requires an (x, y) tuple or None")
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in self.position):
                raise ValueError("position requires finite screen coordinates")
        if self.state not in ("normal", "maximized", "fullscreen"):
            raise ValueError("window_state requires normal, maximized or fullscreen")
        if not self.resizable and self.state == "maximized":
            raise ValueError("a fixed-size window cannot start maximized")

    def validate_size(self, width: float, height: float) -> None:
        _pixel(width, "width", self.min_width)
        _pixel(height, "height", self.min_height)
