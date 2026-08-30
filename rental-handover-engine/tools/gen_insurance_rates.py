#!/usr/bin/env python3
"""BUILD-TIME generator for rulesets/insurance_rates.yaml.

The determinism charter forbids formulas in the RUNTIME decision path, not in
the workshop that produces the table. This script runs by hand, in integer
arithmetic, and its output -- a flat table of literal premiums -- is committed.
At runtime quote_premium() does a dict lookup and nothing else.

Re-running this script must reproduce the committed file byte for byte; that is
asserted by tests/test_rulesets.py::test_insurance_table_is_reproducible.
"""
import pathlib

VALUE_BANDS = ["low", "mid", "high", "very_high"]
TIERS = [1, 2, 3, 4, 5]
TRUST_BANDS = ["new", "fair", "good", "excellent"]
DURATION_BANDS = ["hours_24", "days_3", "days_7", "days_30_plus"]

# All multipliers are integer basis-of-100 factors. No floats, ever.
BASE_CENTS = {"low": 300, "mid": 900, "high": 2400, "very_high": 7000}
TIER_MUL = {1: 100, 2: 115, 3: 135, 4: 200, 5: 120}
TRUST_MUL = {"new": 140, "fair": 115, "good": 100, "excellent": 85}
DURATION_MUL = {"hours_24": 100, "days_3": 160, "days_7": 250, "days_30_plus": 600}
QUANTISE_CENTS = 25  # premiums are always a whole number of 25-cent steps


def premium(value_band: str, tier: int, trust_band: str, duration_band: str) -> int:
    cents = BASE_CENTS[value_band]
    cents = cents * TIER_MUL[tier] // 100
    cents = cents * TRUST_MUL[trust_band] // 100
    cents = cents * DURATION_MUL[duration_band] // 100
    # Round half up to the quantisation step, in integers.
    steps = (cents * 2 + QUANTISE_CENTS) // (QUANTISE_CENTS * 2)
    return steps * QUANTISE_CENTS


def render() -> str:
    lines = [
        "# insurance_rates.yaml",
        "# L0 RULESET — GENERATED FILE. Do not hand-edit.",
        "#",
        "# Regenerate with:  python3 tools/gen_insurance_rates.py",
        "# Runtime behaviour is a pure dict lookup on the composite key",
        "#   \"<value_band>|<tier>|<trust_band>|<duration_band>\"",
        "# There is no formula, no interpolation and no fallback at runtime: a key",
        "# miss raises RateNotFound rather than guessing a premium.",
        "",
        "ruleset_version: 2",
        "schema: insurance_rates/1",
        "",
        "bands:",
        "  value_band_cents:",
        "    low:       {min: 0,      max: 19999}",
        "    mid:       {min: 20000,  max: 99999}",
        "    high:      {min: 100000, max: 499999}",
        "    very_high: {min: 500000, max: 999999999}",
        "  duration_band_seconds:",
        "    hours_24:     {min: 0,       max: 86400}",
        "    days_3:       {min: 86401,   max: 259200}",
        "    days_7:       {min: 259201,  max: 604800}",
        "    days_30_plus: {min: 604801,  max: 999999999}",
        "",
        "coverage_tiers:",
        "  basic:    {deductible_cents: 15000, covers: [theft, fire, third_party]}",
        "  standard: {deductible_cents: 7500,  covers: [theft, fire, third_party, accidental_damage]}",
        "  full:     {deductible_cents: 2500,  covers: [theft, fire, third_party, accidental_damage, misuse]}",
        "",
        "# Deposit held on the renter, by value band. Integer cents.",
        "deposit_cents:",
        "  low:       2500",
        "  mid:       10000",
        "  high:      50000",
        "  very_high: 250000",
        "",
        "# Coverage tier assigned per handover tier. Higher-touch handovers carry",
        "# more evidence, so they earn a lower deductible.",
        "coverage_tier_by_handover_tier:",
        "  1: standard",
        "  2: basic",
        "  3: full",
        "  4: basic",
        "  5: standard",
        "",
        "# premium_cents[value_band|tier|trust_band|duration_band] -> integer cents",
        "premium_cents:",
    ]
    for vb in VALUE_BANDS:
        for tier in TIERS:
            for tb in TRUST_BANDS:
                for db in DURATION_BANDS:
                    key = f"{vb}|{tier}|{tb}|{db}"
                    lines.append(f"  \"{key}\": {premium(vb, tier, tb, db)}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = pathlib.Path(__file__).resolve().parent.parent / "rhe" / "l0_rules" / "rulesets" / "insurance_rates.yaml"
    out.write_text(render(), encoding="utf-8")
    print(f"wrote {out} ({len(VALUE_BANDS) * len(TIERS) * len(TRUST_BANDS) * len(DURATION_BANDS)} premium cells)")
