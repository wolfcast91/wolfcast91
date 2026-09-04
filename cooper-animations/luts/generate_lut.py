#!/usr/bin/env python3
"""
Erzeugt luts/day-one-v1.cube — die Season-1-Grade fuer CapCut.

Gefuehle -> Parameter (siehe docs/REGELWERK.md):
  cinematisch  -> ACES-Filmic-Kontrastkurve, weicher Highlight-Rolloff
  bodenstaendig-> Entsaettigung, angehobene statt abgesoffene Schwarzwerte
  ruhig        -> gedeckte, warme Toene statt Hochglanz-Kontrast
  naiv         -> warme Schatten/Lichter statt kaltes Blockbuster-Teal

"witzig" und "fleissig" werden bewusst NICHT ueber Farbe transportiert,
sondern ueber Schreibweise (MarkerLine-Captions) und Struktur
(MonoReadout-Zaehler) - siehe Regelwerk Abschnitt "Gefuehlswelt".

Nur Python-Standardbibliothek, kein externes Paket noetig.
Aufruf: python3 generate_lut.py
"""

# --- Grade parameters -------------------------------------------------
# out = ((in + lift*(1-in)) * gain) ** (1/gamma), pro Kanal.
LIFT = (0.015, 0.010, -0.015)  # warme, angehobene Schatten (nie crushed black)
GAMMA = (1.05, 1.02, 0.97)  # warme Mitten (>1 hellt hier den Kanal auf)
GAIN = (1.03, 1.00, 0.95)  # warme Lichter, zurueckgenommenes Blau

DESAT = 0.12  # 12% Richtung Luma -> bodenstaendig, ruhig
LUMA = (0.2126, 0.7152, 0.0722)  # Rec.709

LUT_SIZE = 33
OUTPUT_PATH = "day-one-v1.cube"
TITLE = "Day One - Traumauto Season 1"


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lift_gamma_gain(x, lift, gamma, gain):
    x = gain * (x + lift * (1 - x))
    x = clamp(x, 0.0, 4.0)
    return x ** (1.0 / gamma) if x > 0 else 0.0


def aces_filmic(x):
    """Narkowicz ACES approximation: filmic contrast + highlight rolloff."""
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e))


def grade(r, g, b):
    r = lift_gamma_gain(r, LIFT[0], GAMMA[0], GAIN[0])
    g = lift_gamma_gain(g, LIFT[1], GAMMA[1], GAIN[1])
    b = lift_gamma_gain(b, LIFT[2], GAMMA[2], GAIN[2])

    r, g, b = aces_filmic(r), aces_filmic(g), aces_filmic(b)

    luma = LUMA[0] * r + LUMA[1] * g + LUMA[2] * b
    r = luma + (r - luma) * (1 - DESAT)
    g = luma + (g - luma) * (1 - DESAT)
    b = luma + (b - luma) * (1 - DESAT)

    return clamp(r), clamp(g), clamp(b)


def write_cube(path, size=LUT_SIZE, title=TITLE):
    with open(path, "w") as f:
        f.write(f'TITLE "{title}"\n')
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        for bi in range(size):
            for gi in range(size):
                for ri in range(size):
                    r = ri / (size - 1)
                    g = gi / (size - 1)
                    b = bi / (size - 1)
                    r2, g2, b2 = grade(r, g, b)
                    f.write(f"{r2:.6f} {g2:.6f} {b2:.6f}\n")


if __name__ == "__main__":
    write_cube(OUTPUT_PATH)
    print(f"wrote {OUTPUT_PATH}")
