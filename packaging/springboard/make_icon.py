#!/usr/bin/env python3
"""Write KernelLab SpringBoard icons into an app bundle directory.

Stdlib only. The mark is a geometric K on the console navy field.
"""

import struct
import sys
import zlib


def _chunk(tag, data):
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _png(width, height, pixel):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for x in range(width):
            raw.extend(pixel(x, y, width, height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def _pixel(x, y, width, height):
    margin = max(4, width // 10)
    if margin <= x < width - margin and margin <= y < height - margin:
        red, green, blue = (22, 34, 58)
    else:
        red, green, blue = (11, 14, 20)

    # Stem of the K.
    stem_x0 = int(width * 0.30)
    stem_x1 = int(width * 0.42)
    stem_y0 = int(height * 0.22)
    stem_y1 = int(height * 0.78)
    on_stem = stem_x0 <= x < stem_x1 and stem_y0 <= y < stem_y1

    # Two arms meeting the stem at mid-height.
    mid = height * 0.50
    arm_x0 = stem_x1 - width * 0.02
    arm_x1 = width * 0.74
    thickness = max(2.0, width * 0.055)
    on_arm = False
    if arm_x0 <= x <= arm_x1 and stem_y0 <= y < stem_y1:
        t = (x - arm_x0) / (arm_x1 - arm_x0)
        upper = mid - t * (mid - stem_y0)
        lower = mid + t * (stem_y1 - mid)
        if abs(y - upper) <= thickness or abs(y - lower) <= thickness:
            on_arm = True

    if on_stem or on_arm:
        red, green, blue = (138, 180, 255)
    return (red, green, blue, 255)


def write_icons(directory):
    sizes = {
        "icon.png": 120,
        "icon@2x.png": 120,
        "icon@3x.png": 180,
    }
    for name, size in sizes.items():
        path = os_path(directory, name)
        with open(path, "wb") as handle:
            handle.write(_png(size, size, _pixel))


def os_path(directory, name):
    import os
    return os.path.join(directory, name)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_icon.py <KernelLab.app directory>")
    write_icons(sys.argv[1])


if __name__ == "__main__":
    main()
