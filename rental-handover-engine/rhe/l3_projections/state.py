"""L3 — Projections. Derived state, entirely disposable.

Current state is a deterministic fold over L2 through L1. The database is a
cache: delete it, replay from event zero, get the same thing back. If a
projection ever disagrees with a replay, the replay wins and the projection is
the bug -- that is the whole reason state is never stored as truth.

This module is a pure function of (events, ruleset). It reads no clock, opens no
file and touches no database; persisting the result is sqlite_store's job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from rhe.l0_rules.loader import Ruleset
from rhe.l1_kernel.trust import compute_trust


class ProjectionError(Exception):
    """An event referenced an entity that the fold has never seen."""


@dataclass
class ProjectionState:
    """Everything the read side needs. Plain dicts, sorted on the way out."""

    users: dict[str, dict[str, Any]] = field(default_factory=dict)
    items: dict[str, dict[str, Any]] = field(default_factory=dict)
    locations: dict[str, dict[str, Any]] = field(default_factory=dict)
    partner_nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    rentals: dict[str, dict[str, Any]] = field(default_factory=dict)
    condition_reports: dict[str, dict[str, Any]] = field(default_factory=dict)
    condition_chains: dict[str, list[str]] = field(default_factory=dict)   # item_id -> [report_id]
    access_grants: dict[str, dict[str, Any]] = field(default_factory=dict)
    purchase_offers: dict[str, dict[str, Any]] = field(default_factory=dict)
    disputes: dict[str, dict[str, Any]] = field(default_factory=dict)
    risk_flags: list[dict[str, Any]] = field(default_factory=list)
    trust_scores: dict[str, int] = field(default_factory=dict)             # "kind:id" -> score
    events_applied: int = 0

    # -- ordered read accessors (charter rule 4) ---------------------------
    def items_sorted(self) -> list[dict[str, Any]]:
        # precedence.yaml:sort_keys.inventory_view = [owner_id, category_id, item_id]
        return sorted(self.items.values(), key=lambda i: (i["owner_id"], i["category_id"], i["item_id"]))

    def inventory_of(self, owner_id: str) -> list[dict[str, Any]]:
        return [i for i in self.items_sorted() if i["owner_id"] == owner_id]

    def chain_for(self, item_id: str) -> list[dict[str, Any]]:
        return [self.condition_reports[r] for r in self.condition_chains.get(item_id, [])]

    def rentals_sorted(self) -> list[dict[str, Any]]:
        return sorted(self.rentals.values(), key=lambda r: (r["opened_event_seq"], r["rental_id"]))

    def available_items(self) -> list[dict[str, Any]]:
        return [i for i in self.items_sorted() if i["state"] == "available"]

    def trust_of(self, kind: str, subject_id: str) -> int:
        return self.trust_scores.get(f"{kind}:{subject_id}", 0)


def _require(mapping: Mapping[str, Any], key: str, kind: str) -> dict[str, Any]:
    if key not in mapping:
        raise ProjectionError(f"event references unknown {kind}: {key!r}")
    return mapping[key]  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Per-event-type reducers. Each takes (state, payload, event) and mutates state.
# Registered in a table so an unhandled event type is a loud failure, not a
# silent no-op that quietly desynchronises the projection from the log.
# ---------------------------------------------------------------------------

def _user_registered(s: ProjectionState, p, e) -> None:
    s.users[p["user_id"]] = {
        "user_id": p["user_id"], "handle": p["handle"], "account_type": p["account_type"],
        "display_name": p.get("display_name", p["handle"]), "id_verified": False,
        "created_at_utc": e["clock_utc"], "event_seq": e["event_seq"],
        "overdue_returns_lifetime": 0, "items_declared_lost_lifetime": 0, "disputes_lifetime": 0,
    }


def _identity_verified(s, p, e) -> None:
    _require(s.users, p["user_id"], "user")["id_verified"] = True


def _location_registered(s, p, e) -> None:
    s.locations[p["location_id"]] = dict(p, created_at_utc=e["clock_utc"], event_seq=e["event_seq"])


def _partner_node_registered(s, p, e) -> None:
    s.partner_nodes[p["partner_node_id"]] = dict(p, created_at_utc=e["clock_utc"], event_seq=e["event_seq"])


def _item_listed(s, p, e) -> None:
    s.items[p["item_id"]] = {
        "item_id": p["item_id"], "owner_id": p["owner_id"], "category_id": p["category_id"],
        "model_name": p["model_name"], "serial_number": p.get("serial_number", ""),
        "replacement_value_cents": p["replacement_value_cents"],
        "purchase_price_cents": p["purchase_price_cents"],
        "day_rate_cents": p["day_rate_cents"],
        "location_id": p["location_id"], "partner_node_id": p.get("partner_node_id"),
        "state": "available", "classified_tier": p["tier"], "effective_tier": p["tier"],
        "tier_row_id": p["tier_row_id"], "tier_citation": p["tier_citation"],
        "attributes": p["attributes"], "attribute_sources": p.get("attribute_sources", {}),
        "clean_handovers_consecutive": 0, "disputes_lifetime": 0, "completed_rentals": 0,
        "accessory_manifest": p.get("accessory_manifest", []),
        "created_at_utc": e["clock_utc"], "event_seq": e["event_seq"],
        "ruleset_hash": e["ruleset_hash"], "graduated": False,
    }
    s.condition_chains.setdefault(p["item_id"], [])


def _tier_graduated(s, p, e) -> None:
    item = _require(s.items, p["item_id"], "item")
    item["effective_tier"] = p["to_tier"]
    item["graduated"] = True
    item["graduation_citation"] = p["citation"]


def _tier_demoted(s, p, e) -> None:
    item = _require(s.items, p["item_id"], "item")
    item["effective_tier"] = p["to_tier"]
    item["graduated"] = False
    item["demotion_reason"] = p["reason"]


def _item_reserved(s, p, e) -> None:
    s.rentals[p["rental_id"]] = {
        "rental_id": p["rental_id"], "item_id": p["item_id"], "renter_id": p["renter_id"],
        "owner_id": p["owner_id"], "tier": p["tier"],
        "window_start_utc": p["window_start_utc"], "window_end_utc": p["window_end_utc"],
        "window_start_epoch": p["window_start_epoch"], "window_end_epoch": p["window_end_epoch"],
        "duration_seconds": p["duration_seconds"], "rent_cents": p["rent_cents"],
        "quoted_premium_cents": p.get("quoted_premium_cents", 0),
        "deposit_cents": p.get("deposit_cents", 0),
        "state": "reserved", "item_state": "reserved",
        "pre_report_id": None, "post_report_id": None,
        "returned_late": False, "closed_at_utc": None, "closed_at_epoch": None,
        "settled_cents": None, "policy_ref": None, "insurance_status": "not_quoted",
        "opened_event_seq": e["event_seq"],
    }
    _require(s.items, p["item_id"], "item")["state"] = "reserved"


def _rental_state(s, p, to_state: str, item_state: str | None = None) -> dict[str, Any]:
    rental = _require(s.rentals, p["rental_id"], "rental")
    rental["state"] = to_state
    if item_state:
        _require(s.items, rental["item_id"], "item")["state"] = item_state
        rental["item_state"] = item_state
    return rental


def _access_granted(s, p, e) -> None:
    s.access_grants[p["rental_id"]] = dict(p, event_seq=e["event_seq"], revoked=False)
    _rental_state(s, p, "access_granted")


def _meetup_confirmed(s, p, e) -> None:
    _rental_state(s, p, "access_granted")


def _access_revoked(s, p, e) -> None:
    if p["rental_id"] in s.access_grants:
        s.access_grants[p["rental_id"]]["revoked"] = True


def _item_picked_up(s, p, e) -> None:
    _rental_state(s, p, "active", "out")


def _marked_overdue(s, p, e) -> None:
    rental = _rental_state(s, p, "overdue", "overdue_out")
    rental["returned_late"] = True
    _require(s.users, rental["renter_id"], "user")["overdue_returns_lifetime"] += 1


def _return_initiated(s, p, e) -> None:
    _rental_state(s, p, "return_initiated", "in_return_check")


def _condition_report(s, p, e) -> None:
    report = {
        "report_id": p["report_id"], "item_id": p["item_id"], "rental_id": p["rental_id"],
        "phase": p["phase"], "submitted_by": p["submitted_by"],
        "submitted_at_utc": e["clock_utc"], "event_seq": e["event_seq"],
        "damage_tags": p["damage_tags"], "photo_slots": p["photo_slots"],
        "photo_refs": p.get("photo_refs", []),
        "accessory_manifest": p.get("accessory_manifest", []),
        "prev_report_id": p.get("prev_report_id"), "countersigned_by": [],
    }
    s.condition_reports[p["report_id"]] = report
    s.condition_chains.setdefault(p["item_id"], []).append(p["report_id"])
    rental = s.rentals.get(p["rental_id"])
    if rental is not None:
        key = "pre_report_id" if p["phase"] in ("pre", "partner_intake") else "post_report_id"
        rental[key] = p["report_id"]


def _countersigned(s, p, e) -> None:
    _require(s.condition_reports, p["report_id"], "condition report")["countersigned_by"] = p["signed_by"]


def _diff_computed(s, p, e) -> None:
    report = _require(s.condition_reports, p["report_id"], "condition report")
    report["diff_appeared"] = p["appeared"]
    report["diff_blocking"] = p["blocking"]
    report["diff_missing_accessories"] = p["missing_accessories"]
    report["deposit_hold_cents"] = p["deposit_hold_cents"]


def _damage_reported(s, p, e) -> None:
    _rental_state(s, p, "damage_reported", "damage_hold")


def _damage_waived(s, p, e) -> None:
    _rental_state(s, p, "closed", "available")


def _damage_settled(s, p, e) -> None:
    _rental_state(s, p, "closed", "damage_hold")


def _repair_scheduled(s, p, e) -> None:
    rental = s.rentals.get(p["rental_id"])
    item_id = rental["item_id"] if rental else p["item_id"]
    _require(s.items, item_id, "item")["state"] = "under_repair"


def _repair_completed(s, p, e) -> None:
    _require(s.items, p["item_id"], "item")["state"] = "available"


def _dispute_opened(s, p, e) -> None:
    s.disputes[p["dispute_id"]] = dict(p, state="open", opened_event_seq=e["event_seq"], resolution=None)
    rental = _rental_state(s, p, "disputed", "disputed")
    _require(s.users, rental["renter_id"], "user")["disputes_lifetime"] += 1
    item = _require(s.items, rental["item_id"], "item")
    item["disputes_lifetime"] += 1
    item["clean_handovers_consecutive"] = 0


def _dispute_resolved(s, p, e, item_state: str) -> None:
    dispute = _require(s.disputes, p["dispute_id"], "dispute")
    dispute["state"] = "resolved"
    dispute["resolution"] = p["resolution"]
    dispute["resolved_by"] = p["resolved_by"]
    _rental_state(s, p, "closed", item_state)


def _return_accepted(s, p, e) -> None:
    rental = _rental_state(s, p, "closed", "available")
    rental["closed_at_utc"] = e["clock_utc"]
    item = _require(s.items, rental["item_id"], "item")
    item["completed_rentals"] += 1
    if p.get("clean", False):
        item["clean_handovers_consecutive"] += 1
    else:
        item["clean_handovers_consecutive"] = 0


def _rental_closed(s, p, e) -> None:
    rental = _require(s.rentals, p["rental_id"], "rental")
    rental["settled_cents"] = p["settled_cents"]
    rental["closed_at_utc"] = e["clock_utc"]
    rental["closed_at_epoch"] = p["closed_at_epoch"]
    rental["state"] = "closed"


def _declared_lost(s, p, e) -> None:
    rental = _rental_state(s, p, "written_off", "lost")
    _require(s.users, rental["renter_id"], "user")["items_declared_lost_lifetime"] += 1


def _item_recovered(s, p, e) -> None:
    _require(s.items, p["item_id"], "item")["state"] = "in_return_check"


def _reservation_cancelled(s, p, e) -> None:
    _rental_state(s, p, "cancelled", "available")


def _insurance_quoted(s, p, e) -> None:
    rental = _require(s.rentals, p["rental_id"], "rental")
    rental["quoted_premium_cents"] = p["premium_cents"]
    rental["deposit_cents"] = p["deposit_cents"]
    rental["coverage_tier"] = p["coverage_tier"]
    rental["insurance_status"] = "quoted"


def _insurance_bound(s, p, e) -> None:
    rental = _require(s.rentals, p["rental_id"], "rental")
    rental["policy_ref"] = p["policy_ref"]
    rental["insurance_status"] = "bound"


def _opportunity_detected(s, p, e) -> None:
    s.purchase_offers[p["offer_id"]] = dict(p, state="offered", event_seq=e["event_seq"])


def _offer_accepted(s, p, e) -> None:
    _require(s.purchase_offers, p["offer_id"], "purchase offer")["state"] = "accepted"


def _item_sold(s, p, e) -> None:
    item = _require(s.items, p["item_id"], "item")
    item["state"] = "sold"
    item["sold_to"] = p["buyer_id"]
    # Ownership history lives in the log, not in a mutable column: the chain of
    # ItemSold events IS the provenance record, and it survives the projection
    # being deleted.
    item["owner_id"] = p["buyer_id"]


def _item_retired(s, p, e) -> None:
    _require(s.items, p["item_id"], "item")["state"] = "retired"


def _risk_flag(s, p, e) -> None:
    s.risk_flags.append(dict(p, event_seq=e["event_seq"]))


def _noop(s, p, e) -> None:
    """Events that carry evidence but move no projected state."""


REDUCERS = {
    "UserRegistered": _user_registered,
    "IdentityVerified": _identity_verified,
    "LocationRegistered": _location_registered,
    "PartnerNodeRegistered": _partner_node_registered,
    "ItemListed": _item_listed,
    "AttributeOverridden": _noop,
    "TierAssigned": _noop,
    "TierGraduated": _tier_graduated,
    "TierDemoted": _tier_demoted,
    "ItemReserved": _item_reserved,
    "AccessGranted": _access_granted,
    "MeetupConfirmed": _meetup_confirmed,
    "AccessRevoked": _access_revoked,
    "AccessCodeValidated": _noop,
    "SpatialLandmarkVerified": _noop,
    "PartnerIntakeConfirmed": _noop,
    "CertificationVerified": _noop,
    "ContractExecuted": _noop,
    "ItemPickedUp": _item_picked_up,
    "RentalMarkedOverdue": _marked_overdue,
    "ItemReturnInitiated": _return_initiated,
    "ConditionReportSubmitted": _condition_report,
    "ConditionReportCountersigned": _countersigned,
    "ConditionDiffComputed": _diff_computed,
    "DamageReported": _damage_reported,
    "DamageWaived": _damage_waived,
    "DamageSettled": _damage_settled,
    "RepairScheduled": _repair_scheduled,
    "RepairCompleted": _repair_completed,
    "DisputeOpened": _dispute_opened,
    "DisputeResolvedRepair": lambda s, p, e: _dispute_resolved(s, p, e, "under_repair"),
    "DisputeResolvedNoFault": lambda s, p, e: _dispute_resolved(s, p, e, "available"),
    "ReturnAccepted": _return_accepted,
    "RentalClosed": _rental_closed,
    "ItemDeclaredLost": _declared_lost,
    "ItemRecovered": _item_recovered,
    "ReservationCancelled": _reservation_cancelled,
    "InsuranceQuoted": _insurance_quoted,
    "InsuranceBound": _insurance_bound,
    "PurchaseOpportunityDetected": _opportunity_detected,
    "PurchaseOfferAccepted": _offer_accepted,
    "ItemSold": _item_sold,
    "ItemRetired": _item_retired,
    "TrustSignalRecorded": _noop,      # trust is recomputed from scratch below
    "RiskFlagRaised": _risk_flag,
    "EventCompensated": _noop,
}


def fold(events: Sequence[Mapping[str, Any]], ruleset: Ruleset) -> ProjectionState:
    """Rebuild the entire world from the log. Pure, total, order-dependent only
    on event_seq."""
    state = ProjectionState()
    ordered = sorted(events, key=lambda e: e["event_seq"])
    compensated = {
        e["payload"]["target_event_seq"] for e in ordered if e["event_type"] == "EventCompensated"
    }

    for event in ordered:
        if event["event_seq"] in compensated:
            continue   # a compensated event is superseded, never deleted
        reducer = REDUCERS.get(event["event_type"])
        if reducer is None:
            raise ProjectionError(
                f"event type {event['event_type']!r} has no reducer. Every event must "
                f"have one, even if it is _noop -- silence here means drift."
            )
        reducer(state, event["payload"], event)
        state.events_applied += 1

    # Trust is never folded incrementally. It is recomputed from zero, every
    # time, for every subject -- charter rule for trust scoring.
    for user_id in sorted(state.users):
        state.trust_scores[f"user:{user_id}"] = compute_trust("user", user_id, ordered, ruleset).score
    for item_id in sorted(state.items):
        state.trust_scores[f"item:{item_id}"] = compute_trust("item", item_id, ordered, ruleset).score

    return state
