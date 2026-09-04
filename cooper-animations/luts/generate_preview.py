#!/usr/bin/env python3
"""
Erzeugt luts/day-one-v1-preview.png: sechs Farbbaender (neutral, Holz/Haut,
Amber, Stahlblau, Gruen, Beton), links Original / rechts mit der Grade aus
generate_lut.py. Nur Python-Standardbibliothek (kein Pillow noetig).

Aufruf (aus diesem Verzeichnis): python3 generate_preview.py
"""
import struct
import zlib

from generate_lut import grade

WIDTH, HEIGHT = 800, 420
BAND_H = HEIGHT // 6
OUTPUT_PATH = "day-one-v1-preview.png"

BANDS = [
    ("neutral", (1.0, 1.0, 1.0)),
    ("holz/haut", (0.85, 0.55, 0.35)),
    ("amber", (1.0, 0.55, 0.10)),
    ("stahlblau", (0.30, 0.45, 0.75)),
    ("gruen", (0.35, 0.55, 0.25)),
    ("beton", (0.55, 0.58, 0.62)),
]


def to_byte(v):
    return max(0, min(255, int(round(v * 255))))


def render_rows():
    rows = []
    for y in range(HEIGHT):
        band_idx = min(y // BAND_H, len(BANDS) - 1)
        _, base = BANDS[band_idx]
        row = bytearray()
        for x in range(WIDTH):
            half = x < WIDTH // 2
            t = (x if half else x - WIDTH // 2) / (WIDTH / 2 - 1)
            r, g, b = base[0] * t, base[1] * t, base[2] * t
            if not half:
                r, g, b = grade(r, g, b)
            row += bytes((to_byte(r), to_byte(g), to_byte(b)))
        mid = (WIDTH // 2) * 3
        row[mid : mid + 3] = bytes((40, 40, 40))  # Trennlinie Original|Grade
        rows.append(bytes(row))
    return rows


def write_png(path, width, height, rows):
    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + r for r in rows)
    idat = zlib.compress(raw, 9)
    with open(path, "wb") as f:
        f.write(sig)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


if __name__ == "__main__":
    write_png(OUTPUT_PATH, WIDTH, HEIGHT, render_rows())
    print(f"wrote {OUTPUT_PATH}")
