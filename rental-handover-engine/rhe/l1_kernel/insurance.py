"""L1 — Premium quoting. A lookup, not a model.

`quote_premium` reads one cell out of a 320-cell table keyed by four bands. It
does no arithmetic beyond band selection, performs no interpolation, and has no
fallback: a key miss raises RateNotFound rather than inventing a number. An
insurer can audit the entire pricing surface by reading one YAML file.

The real integration seam (Tint.ai or similar) slots in at L5 behind
InsurancePartner; this function is what the platform quotes locally and what a
partner's response is reconciled against.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from rhe.l0_rules.loader import Ruleset


class RateNotFound(Exception):
    """No cell for this band combination. Never silently defaulted."""


@dataclass(frozen=True)
class InsuranceQuote:
    """A quote, plus enough provenance to reproduce it years later."""

    premium_cents: int
    deposit_cents: int
    coverage_tier: str
    deductible_cents: int
    covers: tuple[str, ...]
    value_band: str
    trust_band: str
    duration_band: str
    tier: int
    lookup_key: str
    citation: str
    insurance_status: str = "quoted"   # quoted | bound | declined | not_required

    def explain(self) -> str:
        return (
            f"{self.premium_cents} cents, because {self.citation} cell "
            f"'{self.lookup_key}'"
        )


def _band_for(value: int, bands: Mapping[str, Mapping[str, int]], what: str) -> str:
    """First band (in declared order) whose integer range contains `value`."""
    for name in bands:                      # dict order == YAML file order, which is declared
        spec = bands[name]
        if spec["min"] <= value <= spec["max"]:
            return name
    raise RateNotFound(f"{value} falls outside every declared {what} band")


def value_band(replacement_value_cents: int, ruleset: Ruleset) -> str:
    if not isinstance(replacement_value_cents, int):
        raise RateNotFound("money must be integer cents; floats are banned (charter rule 3)")
    return _band_for(replacement_value_cents, ruleset.doc("insurance_rates")["bands"]["value_band_cents"], "value")


def duration_band(duration_seconds: int, ruleset: Ruleset) -> str:
    if not isinstance(duration_seconds, int):
        raise RateNotFound("duration must be integer seconds")
    return _band_for(duration_seconds, ruleset.doc("insurance_rates")["bands"]["duration_band_seconds"], "duration")


def trust_band(trust_score: int, ruleset: Ruleset) -> str:
    for band in ruleset.doc("trust_weights")["trust_bands"]:
        if band["min"] <= trust_score <= band["max"]:
            return band["band"]
    raise RateNotFound(f"trust score {trust_score} falls outside every declared band")


def quote_premium(
    replacement_value_cents: int,
    tier: int,
    renter_trust_score: int,
    duration_seconds: int,
    ruleset: Ruleset,
) -> InsuranceQuote:
    """(value, tier, trust, duration) -> a premium from the rate table."""
    doc = ruleset.doc("insurance_rates")
    vb = value_band(replacement_value_cents, ruleset)
    tb = trust_band(renter_trust_score, ruleset)
    db = duration_band(duration_seconds, ruleset)
    key = f"{vb}|{tier}|{tb}|{db}"

    try:
        premium = doc["premium_cents"][key]
    except KeyError:
        raise RateNotFound(
            f"no premium cell for '{key}' in {ruleset.citation('insurance_rates')}"
        ) from None

    coverage_tier = doc["coverage_tier_by_handover_tier"][tier]
    coverage = doc["coverage_tiers"][coverage_tier]

    return InsuranceQuote(
        premium_cents=premium,
        deposit_cents=doc["deposit_cents"][vb],
        coverage_tier=coverage_tier,
        deductible_cents=coverage["deductible_cents"],
        covers=tuple(coverage["covers"]),
        value_band=vb,
        trust_band=tb,
        duration_band=db,
        tier=tier,
        lookup_key=key,
        citation=ruleset.citation("insurance_rates"),
    )
