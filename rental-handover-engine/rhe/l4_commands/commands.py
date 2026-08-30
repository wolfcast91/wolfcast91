"""L4 — The typed command vocabulary.

Every mutation in the system is one of these. There is no other write path: no
direct event append, no projection poke, no "just this once" shortcut. Each one
goes through the same pipeline in engine.py:

    validate  ->  evaluate against L1  ->  append to L2  ->  rebuild L3

Commands carry intent and nothing else. They hold no decisions -- a command says
"the renter wants the item", never "the premium is 1450 cents". Decisions belong
to the kernel, which is why they are reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class Command:
    """Marker base. Subclasses are plain data."""


@dataclass(frozen=True)
class RegisterUser(Command):
    handle: str
    display_name: str
    account_type: str          # private | sole_trader | business | partner_staff
    verify_identity: bool = False


@dataclass(frozen=True)
class RegisterLocation(Command):
    owner_handle: str
    label: str
    access_type: str           # pin | gate_code | meetup | staffed | depot
    lat_micro: int
    lon_micro: int
    spatial_instruction: str | None = None
    landmark_photo_slot: str | None = None
    partner_node_id: str | None = None


@dataclass(frozen=True)
class RegisterPartnerNode(Command):
    operator_name: str
    node_type: str             # hardware_store | workshop | repair_cafe | locker_bank
    lat_micro: int
    lon_micro: int
    intake_fee_cents: int


@dataclass(frozen=True)
class ListItem(Command):
    owner_handle: str
    category_id: str
    model_name: str
    serial_number: str
    replacement_value_cents: int
    purchase_price_cents: int
    day_rate_cents: int
    location_label: str
    accessory_manifest: tuple[str, ...] = ()
    attribute_overrides: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReserveItem(Command):
    item_id: str
    renter_handle: str
    window_start_utc: str
    window_end_utc: str


@dataclass(frozen=True)
class GrantAccess(Command):
    """Issue the credential appropriate to the item's tier: lockbox PIN, gate
    code, meetup confirmation, depot collection code."""
    rental_id: str


@dataclass(frozen=True)
class SubmitConditionReport(Command):
    rental_id: str
    phase: str                 # pre | post | partner_intake | inspection
    submitted_by_handle: str
    damage_tags: tuple[str, ...] = ()
    photo_descriptors: Mapping[str, str] = field(default_factory=dict)
    accessory_manifest: tuple[str, ...] | None = None
    countersigned_by_handles: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpenLockbox(Command):
    """Present the credential and take the item. Named for Tier 1; the same
    command covers a gate code, a depot counter and a meetup handshake."""
    rental_id: str
    presented_secret: str | None = None   # None -> present the issued credential


@dataclass(frozen=True)
class MarkOverdue(Command):
    rental_id: str


@dataclass(frozen=True)
class ReturnItem(Command):
    rental_id: str
    gps_confirmed: bool = True


@dataclass(frozen=True)
class AcceptReturn(Command):
    rental_id: str


@dataclass(frozen=True)
class ReportDamage(Command):
    rental_id: str
    reported_by_handle: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class WaiveDamage(Command):
    rental_id: str
    waived_by_handle: str


@dataclass(frozen=True)
class OpenDispute(Command):
    rental_id: str
    opened_by_handle: str
    contested_tags: tuple[str, ...]


@dataclass(frozen=True)
class ResolveDispute(Command):
    """`resolved_by_handle` is ALWAYS a human. The system records and routes
    disputes; it never decides them."""
    dispute_id: str
    resolved_by_handle: str
    outcome: str               # repair | no_fault
    note_tag: str = "other_requires_human"


@dataclass(frozen=True)
class DeclareLost(Command):
    rental_id: str


@dataclass(frozen=True)
class DetectPurchaseOpportunity(Command):
    renter_handle: str
    item_id: str


@dataclass(frozen=True)
class AcceptPurchaseOffer(Command):
    offer_id: str
    term_months: int


@dataclass(frozen=True)
class VerifySpatialLandmark(Command):
    """Tier 2. The renter photographs the landmark the instruction names ("third
    pallet, blue tarp") and declares whether it matches. The declaration is the
    logged fact; the photo is evidence for it, never a decision input."""
    rental_id: str
    landmark_photo_descriptor: str
    match_declared: bool = True


@dataclass(frozen=True)
class ConfirmPartnerIntake(Command):
    """Tier 5. Partner staff confirm the consigned item is present and matches
    the last entry in its condition chain before a collection code is issued."""
    rental_id: str
    confirmed_by_handle: str
    chain_match_declared: bool = True


@dataclass(frozen=True)
class VerifyCertification(Command):
    """Tier 4. Operator certification checked against the required set. Set
    membership, not judgement: a missing certificate refuses the command."""
    rental_id: str
    operator_handle: str
    presented_certificates: tuple[str, ...]
    required_certificates: tuple[str, ...]


@dataclass(frozen=True)
class ExecuteContract(Command):
    """Tier 4. The rental contract and liability annex, signed by both sides."""
    rental_id: str
    signed_by_owner_handle: str
    signed_by_renter_handle: str
