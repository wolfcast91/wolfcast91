"""L1 — Identity without randomness.

Charter rule 1: no uuid4, no random, no time-seeded ids. Every identifier here
is either a content hash over an explicitly ordered field set, or a monotonic
counter that the event log itself supplies.

The canonical field ordering per entity is declared once, in ENTITY_ID_FIELDS,
and is part of the system's contract: change an entry and every id of that
entity type changes, which is exactly the loud failure you want.
"""
from __future__ import annotations

from typing import Any, Mapping

from rhe.canonical import sha256_hex

# entity kind -> the ORDERED tuple of fields hashed to produce its id.
# Ordering here is documentation; the hash itself sorts keys, so the tuple's job
# is to pin down *which* fields participate, unambiguously.
ENTITY_ID_FIELDS: dict[str, tuple[str, ...]] = {
    "user":            ("kind", "handle", "account_type"),
    "item":            ("kind", "owner_id", "category_id", "model_name", "serial_number"),
    "location":        ("kind", "owner_id", "access_type", "geo_cell", "label"),
    "partner_node":    ("kind", "operator_name", "geo_cell"),
    "rental":          ("kind", "item_id", "renter_id", "window_start_utc", "window_end_utc"),
    "condition_report":("kind", "rental_id", "phase", "submitted_by", "event_seq"),
    "purchase_offer":  ("kind", "renter_id", "item_id", "signal_id", "event_seq"),
    "dispute":         ("kind", "rental_id", "opened_by", "event_seq"),
    "access_grant":    ("kind", "rental_id", "location_id", "valid_from_utc"),
}

# Human-readable prefixes so ids are greppable in terminal output.
ID_PREFIX: dict[str, str] = {
    "user": "usr", "item": "itm", "location": "loc", "partner_node": "pnd",
    "rental": "rnt", "condition_report": "cnd", "purchase_offer": "pof",
    "dispute": "dsp", "access_grant": "acg",
}

ID_HASH_LENGTH = 12


class IdError(Exception):
    """A field required by the canonical id field set was missing."""


def content_id(kind: str, fields: Mapping[str, Any]) -> str:
    """Deterministic id: `<prefix>_<12 hex chars of sha256(canonical fields)>`.

    Same content, same id, on any machine, forever. Two entities that differ in
    any canonical field get different ids; two that agree on all of them are, by
    definition, the same entity.
    """
    if kind not in ENTITY_ID_FIELDS:
        raise IdError(f"unknown entity kind for id generation: {kind!r}")
    required = ENTITY_ID_FIELDS[kind]
    payload: dict[str, Any] = {}
    for field in required:
        if field == "kind":
            payload["kind"] = kind
            continue
        if field not in fields:
            raise IdError(f"{kind} id requires field {field!r}; got {sorted(fields)}")
        payload[field] = fields[field]
    return f"{ID_PREFIX[kind]}_{sha256_hex(payload)[:ID_HASH_LENGTH]}"


def geo_cell(lat_micro: int, lon_micro: int, precision: int = 1000) -> str:
    """A coarse integer grid cell. Integer microdegrees in, string cell out.

    Coordinates never enter the system as floats -- microdegrees are integers,
    so two machines can never disagree about which cell a location falls in.
    """
    if not isinstance(lat_micro, int) or not isinstance(lon_micro, int):
        raise IdError("geo_cell takes integer microdegrees, not floats")
    return f"{lat_micro // precision}:{lon_micro // precision}"
