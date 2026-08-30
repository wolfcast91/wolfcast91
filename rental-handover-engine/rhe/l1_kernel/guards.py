"""L1 — Guard predicates for the state machines.

state_transitions.yaml names guards; this module implements them. The split
matters: adding a guard to a transition is a data edit, but what a guard MEANS
is code, reviewed and unit-tested. A ruleset file can never introduce new
behaviour, only recombine behaviour that already exists here.

Every guard is `(context, params) -> (bool, reason)`. The reason is an enum-like
string that ends up verbatim in the IllegalTransition message, so a rejected
command always says exactly which guard refused and why.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

GuardResult = tuple[bool, str]
Guard = Callable[[Mapping[str, Any], Mapping[str, Any]], GuardResult]


def _g(ok: bool, reason: str) -> GuardResult:
    return (ok, "ok" if ok else reason)


def item_has_location(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(bool(ctx.get("location_id")), "item_has_no_location")


def item_has_tier(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(ctx.get("tier") in (1, 2, 3, 4, 5), "item_has_no_valid_tier")


def renter_id_verified(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(ctx.get("renter_id_verified") is True, "renter_identity_not_verified")


def no_overlapping_reservation(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(not ctx.get("has_overlapping_reservation", False), "window_overlaps_existing_reservation")


def access_granted_for_rental(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(ctx.get("access_granted") is True, "no_access_credential_issued")


def pre_condition_report_exists(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    """The whole product thesis in one guard: no unlock without documentation."""
    return _g(ctx.get("pre_report_id") is not None, "pre_rental_condition_report_missing")


def post_condition_report_exists(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(ctx.get("post_report_id") is not None, "post_rental_condition_report_missing")


def window_end_passed(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    now = ctx.get("now_epoch")
    end = ctx.get("window_end_epoch")
    if now is None or end is None:
        return _g(False, "missing_window_or_clock")
    grace = params["overdue_grace_seconds"]
    return _g(now > end + grace, f"window_not_yet_overdue_by_{grace}s")


def lost_grace_elapsed(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    now = ctx.get("now_epoch")
    end = ctx.get("window_end_epoch")
    if now is None or end is None:
        return _g(False, "missing_window_or_clock")
    grace = params["lost_grace_seconds"]
    return _g(now > end + grace, f"lost_grace_of_{grace}s_not_elapsed")


def human_resolution_recorded(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    """The system never adjudicates a dispute. It refuses to close one that no
    human has ruled on -- which is the point of the guard existing at all."""
    return _g(bool(ctx.get("resolution_recorded_by")), "no_human_resolution_on_record")


def deposit_or_claim_recorded(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(
        ctx.get("deposit_hold_cents") is not None or bool(ctx.get("claim_id")),
        "no_deposit_hold_or_claim_recorded",
    )


def purchase_offer_accepted(ctx: Mapping[str, Any], params: Mapping[str, Any]) -> GuardResult:
    return _g(bool(ctx.get("accepted_purchase_offer_id")), "no_accepted_purchase_offer")


GUARDS: Mapping[str, Guard] = {
    "item_has_location": item_has_location,
    "item_has_tier": item_has_tier,
    "renter_id_verified": renter_id_verified,
    "no_overlapping_reservation": no_overlapping_reservation,
    "access_granted_for_rental": access_granted_for_rental,
    "pre_condition_report_exists": pre_condition_report_exists,
    "post_condition_report_exists": post_condition_report_exists,
    "window_end_passed": window_end_passed,
    "lost_grace_elapsed": lost_grace_elapsed,
    "human_resolution_recorded": human_resolution_recorded,
    "deposit_or_claim_recorded": deposit_or_claim_recorded,
    "purchase_offer_accepted": purchase_offer_accepted,
}
