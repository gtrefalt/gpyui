"""Image sources and a retained native GPUI image control."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from .widgets import BOOL, TEXT, KitControl, choice, integer, number

MAX_IMAGE_BYTES = 32 * 1024 * 1024


@dataclass(frozen=True)
class ImageSource:
    """Immutable source descriptor. Ordinary strings are files or HTTP(S) URLs.

    Use ImageSource.asset(key) for Kit's bundled assets. Files become absolute at
    assignment; their existence and image content are checked asynchronously in Rust.
    """

    kind: Literal["file", "url", "asset", "bytes"]
    value: str | bytes

    def __post_init__(self) -> None:
        if self.kind == "bytes":
            if not isinstance(self.value, bytes):
                raise TypeError("image bytes require bytes")
            if not 0 < len(self.value) <= MAX_IMAGE_BYTES:
                raise ValueError("encoded image bytes must be nonempty and at most 32 MiB")
            return
        if self.kind not in {"file", "url", "asset"}:
            raise ValueError("unsupported image source kind")
        if not isinstance(self.value, str):
            raise TypeError("image location requires str")
        if not self.value or len(self.value) > 32768 or any(ord(c) < 32 for c in self.value):
            raise ValueError("image location must be nonempty, bounded and contain no control characters")
        if self.kind == "url":
            url = urlsplit(self.value)
            if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
                raise ValueError("image URLs require HTTP(S), a hostname and no embedded credentials")
            try:
                _ = url.port
            except ValueError as error:
                raise ValueError("invalid image URL port") from error
        elif self.kind == "file":
            object.__setattr__(self, "value", str(Path(self.value).expanduser().absolute()))

    @classmethod
    def asset(cls, key: str) -> ImageSource:
        """Look up an exact key in the bundled Kit AssetSource."""
        return cls("asset", key)

    def _spec(self) -> dict[str, str]:
        value = self.value
        return {
            "kind": self.kind,
            "value": base64.b64encode(value).decode("ascii") if isinstance(value, bytes) else value,
        }


def image_source(value: Any) -> ImageSource | None:
    if value is None or isinstance(value, ImageSource):
        return value
    if isinstance(value, bytes):
        return ImageSource("bytes", value)
    if isinstance(value, os.PathLike):
        return ImageSource("file", os.fsdecode(value))
    if isinstance(value, str):
        kind = "url" if value.lower().startswith(("http:", "https:")) else "file"
        # Reject other URI schemes rather than treating them as a filesystem path.
        if "://" in value and kind != "url":
            raise ValueError("only HTTP(S) image URLs are supported")
        return ImageSource(kind, value)
    raise TypeError("image source requires str, PathLike, bytes, ImageSource or None")


def aspect_ratio(value: Any) -> float:
    value = number(value)
    if value < 0:
        raise ValueError("aspect_ratio must be nonnegative; zero uses the image's intrinsic ratio")
    return value


class Image(KitControl):
    """Native image display, asynchronous decoding and scoped resource ownership.

    Assign source to replace an image or None to clear it; call reload() to retry
    the same file/URL. source reads back as an immutable ImageSource (or None).
    on_load receives {width, height, frames}; on_error receives a message string.
    This displays images and animated GIF/WebP, not video or a camera stream.
    """

    native = "image"
    fields = {
        "source": (None, image_source),
        "fit": ("contain", choice("contain", "cover", "fill", "scale_down", "none")),
        "grayscale": BOOL,
        "aspect_ratio": (0, aspect_ratio),
        "loading_text": ("Loading image…", TEXT[1]),
        "error_text": ("Image unavailable", TEXT[1]),
        "_revision": (0, integer),
    }
    readonly = ("_revision",)
    events = ("load", "error")

    @property
    def source(self) -> ImageSource | None:
        return self._properties["props"]["source"]

    @source.setter
    def source(self, value: str | os.PathLike[str] | bytes | ImageSource | None) -> None:
        self.__setattr__("source", value)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "source" and "_properties" in self.__dict__:
            value = image_source(value)
            changed = self.source != value
            super().__setattr__(name, value)
            if changed:
                self.reload()
        else:
            super().__setattr__(name, value)

    def _encode_property(self, name: str, value: Any) -> Any:
        return value._spec() if name == "source" and value is not None else value

    def reload(self) -> None:
        """Discard the current decoded result and retry, retaining this control."""
        self._ensure_alive()
        if self._app:
            self._app._check_mutation()
        props = self._properties["props"]
        props["_revision"] = (props["_revision"] + 1) % 1_000_001
        if self._app:
            self._app._queue(self.id, "_revision", props["_revision"])

    def _accept_image_event(self, revision: int) -> bool:
        return revision == self._properties["props"]["_revision"]
