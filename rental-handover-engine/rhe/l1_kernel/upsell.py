"""L1 — The upsell engine. Integer thresholds, not a recommender.

Three signals, each an explicit integer comparison against a threshold in
complementary_items.yaml:

  cumulative_spend_threshold : cumulative_rental_cents >= price * bp // 10000
  repeat_rental_threshold    : same renter + same item, N completed rentals
  complementary_pair         : both halves of a declared pair, inside the window

When several fire, precedence.yaml:upsell_signal_rank decides the headline. This
is the "rent-to-try-then-buy" path: the moment the renter has effectively paid a
large fraction of the purchase price, the platform says so out loud and attaches
financing (Mondu-shaped, stubbed at L5) rather than quietly collecting rent
forever.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from rhe.l0_rules.loader import Ruleset


class UpsellError(Exception):
    """Malformed rental history, or a float where cents belong."""


@dataclass(frozen=True)
class CompletedRental:
    """The minimum history the engine needs. All integers, all from the log."""

    rental_id: str
    item_id: str
    category_id: str
    renter_id: str
    closed_at_epoch: int      # integer seconds, from the injected clock
    rent_paid_cents: int


@dataclass(frozen=True)
class FinancingOffer:
    """The Mondu-shaped seam. Integer cents, integer months, no interest maths
    in the prototype -- the partner prices it, we only shape the request."""

    principal_cents: int
    terms_months: tuple[int, ...]
    monthly_cents_by_term: Mapping[int, int]   # floor division, integers only
    rent_credited_cents: int
    status: str = "offer_available"


@dataclass(frozen=True)
class PurchaseOpportunity:
    """A structured, explainable purchase offer."""

    renter_id: str
    item_id: str
    category_id: str
    signal_id: str
    signal_rank: int
    headline: str
    evidence: Mapping[str, int | str]
    purchase_price_cents: int
    cumulative_rental_cents: int
    financing: FinancingOffer | None
    purchase_conversion_eligible: bool
    blocked_reason: str | None
    citation: str

    def explain(self) -> str:
        return f"{self.signal_id} for {self.item_id}, because {self.citation}"


def _financing(
    purchase_price_cents: int,
    cumulative_rental_cents: int,
    ruleset: Ruleset,
) -> FinancingOffer:
    """Rent already paid is credited against the price -- that is the pitch."""
    thresholds = ruleset.doc("complementary_items")["thresholds"]
    credited = min(cumulative_rental_cents, purchase_price_cents)
    principal = purchase_price_cents - credited
    terms = tuple(thresholds["financing_terms_months"])
    # Integer floor division; the remainder rides on the final instalment, which
    # is a partner concern. No float ever touches money.
    monthly = {t: principal // t for t in terms}
    return FinancingOffer(
        principal_cents=principal,
        terms_months=terms,
        monthly_cents_by_term=monthly,
        rent_credited_cents=credited,
    )


def detect_upsell(
    renter_id: str,
    item_id: str,
    category_id: str,
    purchase_price_cents: int,
    history: Sequence[CompletedRental],
    now_epoch: int,
    renter_trust: int,
    ruleset: Ruleset,
) -> tuple[PurchaseOpportunity, ...]:
    """Every signal that fires, ordered by precedence.yaml:upsell_signal_rank."""
    if not isinstance(purchase_price_cents, int) or not isinstance(now_epoch, int):
        raise UpsellError("purchase price and clock must be integers (charter rule 3)")

    doc = ruleset.doc("complementary_items")
    thresholds = doc["thresholds"]
    ranks = ruleset.doc("precedence")["upsell_signal_rank"]
    citation = ruleset.citation("complementary_items")
    window_start = now_epoch - thresholds["window_seconds"]

    in_window = sorted(
        (h for h in history if h.renter_id == renter_id and h.closed_at_epoch >= window_start),
        key=lambda h: (h.closed_at_epoch, h.rental_id),   # explicit, total ordering
    )

    same_item = [h for h in in_window if h.item_id == item_id]
    same_category = [h for h in in_window if h.category_id == category_id]
    cumulative = sum(h.rent_paid_cents for h in same_item)

    eligible = renter_trust >= thresholds["min_renter_trust_for_offer"]
    blocked = None if eligible else (
        f"renter trust {renter_trust} below "
        f"min_renter_trust_for_offer {thresholds['min_renter_trust_for_offer']}"
    )
    financing = _financing(purchase_price_cents, cumulative, ruleset) if eligible else None

    def opportunity(signal_id: str, headline: str, evidence: dict) -> PurchaseOpportunity:
        return PurchaseOpportunity(
            renter_id=renter_id, item_id=item_id, category_id=category_id,
            signal_id=signal_id, signal_rank=ranks[signal_id],
            headline=headline, evidence=dict(sorted(evidence.items())),
            purchase_price_cents=purchase_price_cents,
            cumulative_rental_cents=cumulative,
            financing=financing,
            purchase_conversion_eligible=eligible,
            blocked_reason=blocked,
            citation=citation,
        )

    found: list[PurchaseOpportunity] = []

    # 1. Cumulative spend. Integer arithmetic, division last.
    trigger_at = purchase_price_cents * thresholds["cumulative_spend_bp"] // 10000
    if cumulative >= trigger_at:
        found.append(opportunity(
            "cumulative_spend_threshold",
            doc["offer_copy"]["cumulative_spend_threshold"],
            {
                "cumulative_rental_cents": cumulative,
                "trigger_at_cents": trigger_at,
                "purchase_price_cents": purchase_price_cents,
                "threshold_bp": thresholds["cumulative_spend_bp"],
            },
        ))

    # 2. Repeat rentals of the same item.
    if len(same_item) >= thresholds["repeat_rental_count"]:
        found.append(opportunity(
            "repeat_rental_threshold",
            doc["offer_copy"]["repeat_rental_threshold"],
            {
                "rentals_of_this_item": len(same_item),
                "threshold": thresholds["repeat_rental_count"],
                "window_seconds": thresholds["window_seconds"],
            },
        ))

    # 3. Complementary pairs. Directed graph, both directions considered.
    rented_categories = {h.category_id for h in in_window}
    partners = sorted(
        {p["partner"] for p in doc["pairs"] if p["primary"] == category_id}
        | {p["primary"] for p in doc["pairs"] if p["partner"] == category_id}
    )
    matched = [c for c in partners if c in rented_categories]
    if len(matched) >= 1 and len(same_category) >= 1:
        found.append(opportunity(
            "complementary_pair",
            doc["offer_copy"]["complementary_pair"],
            {
                "matched_partner_categories": ",".join(matched),
                "this_category_rentals": len(same_category),
            },
        ))

    return tuple(sorted(found, key=lambda o: (o.signal_rank, o.item_id)))


def complementary_partners(category_id: str, ruleset: Ruleset) -> tuple[Mapping[str, str], ...]:
    """What the platform would suggest renting next. Sorted, never ranked by a model."""
    pairs = ruleset.doc("complementary_items")["pairs"]
    out = [
        {"category_id": p["partner"], "note": p["note"], "signal_strength": p["signal_strength"]}
        for p in pairs if p["primary"] == category_id
    ]
    return tuple(sorted(out, key=lambda p: (p["signal_strength"], p["category_id"])))
