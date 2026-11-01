#!/usr/bin/env python3
"""Placeholder SpringBoard icons for KernelLab.app. Geometric mark only."""

import pathlib
import struct
import zlib


def chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def in_mark(nx: float, ny: float) -> bool:
    if 0.34 <= nx <= 0.42 and 0.24 <= ny <= 0.76:
        return True
    span = (nx - 0.42) / 0.24
    if 0.0 <= span <= 1.0:
        upper = 0.48 - span * 0.22
        lower = 0.52 + span * 0.22
        if abs(ny - upper) <= 0.045 or abs(ny - lower) <= 0.045:
            return True
    return False


def pixel(x: int, y: int, width: int, height: int) -> bytes:
    nx = (x + 0.5) / width
    ny = (y + 0.5) / height
    cx = abs(nx - 0.5)
    cy = abs(ny - 0.5)
    radius = (cx ** 4 + cy ** 4) ** 0.25
    if radius > 0.50:
        return b"\x00\x00\x00\x00"
    edge = 1.0
    if radius > 0.46:
        edge = max(0.0, (0.50 - radius) / 0.04)
    sheen = max(0.0, 1.0 - (nx * 0.85 + ny * 1.05))
    red = int(10 + 18 * sheen)
    green = int(14 + 36 * sheen)
    blue = int(26 + 70 * sheen)
    if 0.445 < radius <= 0.50:
        red, green, blue = 190, 210, 255
    if in_mark(nx, ny):
        red, green, blue = 186, 214, 255
    alpha = int(255 * edge)
    return bytes((red, green, blue, alpha))


def png(width: int, height: int) -> bytes:
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend(pixel(x, y, width, height))
        rows.append(row)
    raw = b"".join(rows)
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def main() -> None:
    root = pathlib.Path(__file__).resolve().parent
    sizes = {
        "icon.png": 60,
        "icon@2x.png": 120,
        "icon@3x.png": 180,
    }
    for name, size in sizes.items():
        path = root / name
        path.write_bytes(png(size, size))
        print(path.name, size)


if __name__ == "__main__":
    main()
