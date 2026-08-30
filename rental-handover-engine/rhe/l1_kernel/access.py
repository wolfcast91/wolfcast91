"""L1 — Access credential derivation. Deterministic by construction.

A real smart lock (igloohome via Lockii, say) generates offline-capable,
time-limited PINs. The fake here reproduces that SHAPE exactly -- a PIN valid
only inside a window, revocable, verifiable without a network -- while being a
pure function of (rental_id, location_id, window start). Same inputs, same PIN,
on any machine, forever, which is what lets a whole rental replay bit-for-bit.

This module derives and validates. It does not store anything: the access LOG
lives in L2 and is ordered by event_seq, never by timestamp, because two access
events inside the same second are entirely normal.
"""
from __future__ import annotations

from dataclasses import dataclass

from rhe.canonical import sha256_hex
from rhe.l0_rules.loader import Ruleset

PIN_LENGTH = 6
GATE_CODE_LENGTH = 4

# access_type -> credential shape. The discriminator that makes one Location
# schema cover lockboxes, yards, meetup points, depots and partner nodes.
ACCESS_TYPES = {
    "pin":       {"credential": "numeric_pin",   "length": PIN_LENGTH,       "revocable": True},
    "gate_code": {"credential": "numeric_pin",   "length": GATE_CODE_LENGTH, "revocable": True},
    "meetup":    {"credential": "none",          "length": 0,                "revocable": False},
    "staffed":   {"credential": "collection_ref", "length": PIN_LENGTH,      "revocable": True},
    "depot":     {"credential": "collection_ref", "length": PIN_LENGTH,      "revocable": True},
}


class AccessError(Exception):
    """An unknown access type, or a credential request that makes no sense."""


@dataclass(frozen=True)
class AccessCredential:
    """A time-boxed credential. `secret` is empty for meetup handovers, where the
    counterparty IS the credential."""

    rental_id: str
    location_id: str
    access_type: str
    secret: str
    valid_from_utc: str
    valid_until_utc: str
    valid_from_epoch: int
    valid_until_epoch: int
    derivation: str          # the exact input that produced the secret

    @property
    def is_revocable(self) -> bool:
        return ACCESS_TYPES[self.access_type]["revocable"]


def derive_secret(rental_id: str, location_id: str, valid_from_epoch: int, length: int) -> str:
    """PIN = first `length` decimal digits of sha256 over the canonical inputs.

    Digits are taken from the hash's decimal expansion rather than from hex, so
    the output is a real keypad-enterable code and still uniformly derived.
    """
    if length == 0:
        return ""
    digest = sha256_hex({
        "rental_id": rental_id,
        "location_id": location_id,
        "valid_from_epoch": valid_from_epoch,
    })
    digits = "".join(c for c in str(int(digest[:32], 16)) if c.isdigit())
    if len(digits) < length:                     # astronomically unlikely, still handled
        digits = (digits * ((length // max(len(digits), 1)) + 1))
    return digits[:length]


def issue_credential(
    rental_id: str,
    location_id: str,
    access_type: str,
    valid_from_epoch: int,
    valid_until_epoch: int,
    valid_from_utc: str,
    valid_until_utc: str,
    ruleset: Ruleset | None = None,
) -> AccessCredential:
    """Derive a time-boxed credential. Pure: no clock read, no storage, no I/O."""
    if access_type not in ACCESS_TYPES:
        raise AccessError(f"unknown access_type {access_type!r}; known: {sorted(ACCESS_TYPES)}")
    if valid_until_epoch <= valid_from_epoch:
        raise AccessError("credential window must be strictly positive")

    length = ACCESS_TYPES[access_type]["length"]
    return AccessCredential(
        rental_id=rental_id,
        location_id=location_id,
        access_type=access_type,
        secret=derive_secret(rental_id, location_id, valid_from_epoch, length),
        valid_from_utc=valid_from_utc,
        valid_until_utc=valid_until_utc,
        valid_from_epoch=valid_from_epoch,
        valid_until_epoch=valid_until_epoch,
        derivation=f"sha256(rental_id={rental_id}, location_id={location_id}, valid_from_epoch={valid_from_epoch})",
    )


def validate_credential(
    credential: AccessCredential,
    presented_secret: str,
    at_epoch: int,
    revoked: bool = False,
) -> tuple[bool, str]:
    """(accepted, reason). Reasons are enum-like strings, never prose."""
    if revoked:
        return False, "revoked"
    if at_epoch < credential.valid_from_epoch:
        return False, "too_early"
    if at_epoch > credential.valid_until_epoch:
        return False, "expired"
    if credential.access_type == "meetup":
        return True, "meetup_no_credential_required"
    if presented_secret != credential.secret:
        return False, "wrong_secret"
    return True, "accepted"


def qr_payload(rental_id: str, location_id: str) -> str:
    """What the lockbox sticker encodes. Content-derived, so it is stable across
    replays and printable long before the rental exists."""
    return f"rhe://{location_id}/{sha256_hex({'rental_id': rental_id, 'location_id': location_id})[:16]}"
