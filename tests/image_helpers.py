"""Deterministic encoded image fixtures without an image-processing dependency."""

import struct
import zlib


def png(color=(220, 40, 40), width=200, height=100):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    pixels = (b"\0" + bytes(color) * width) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def animated_gif():
    header = b"GIF89a\x02\x00\x01\x00\x80\x00\x00\xff\x00\x00\x00\x00\xff"
    # Two opaque frames, each lasting 0.5 s, with red/blue palette indices.
    control = b"\x21\xf9\x04\x00\x32\x00\x00\x00"
    descriptor = b"\x2c\x00\x00\x00\x00\x02\x00\x01\x00\x00"
    return (
        header
        + control
        + descriptor
        + b"\x02\x02\x04\x0a\x00"
        + control
        + descriptor
        + b"\x02\x02\x4c\x0a\x00\x3b"
    )
