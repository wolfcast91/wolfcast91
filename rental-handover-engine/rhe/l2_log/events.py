"""L2 — The append-only event log. The single source of truth.

No UPDATE. No DELETE. Ever. A correction is a new compensating event, which
means the log tells you not just what is true but what was believed and when it
stopped being believed. Everything else in the system -- every projection, every
score, every availability calendar -- is a fold over this list and is therefore
disposable.

Each event carries the `ruleset_hash` in force when it was appended, so a
decision made under tier_rules v3 stays reproducible after v4 ships.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Iterator, Mapping, Sequence

from rhe.canonical import canonical_json, sha256_hex

# The closed event vocabulary. An event type not on this list cannot be appended.
EVENT_TYPES: tuple[str, ...] = (
    # registry
    "UserRegistered", "IdentityVerified", "LocationRegistered", "PartnerNodeRegistered",
    "ItemListed", "AttributeOverridden", "TierAssigned", "TierGraduated", "TierDemoted",
    # rental lifecycle
    "ItemReserved", "AccessGranted", "MeetupConfirmed", "AccessCodeValidated",
    "SpatialLandmarkVerified", "PartnerIntakeConfirmed", "CertificationVerified",
    "ContractExecuted", "ItemPickedUp", "RentalMarkedOverdue", "ItemReturnInitiated",
    "ReturnAccepted", "ReservationCancelled", "ItemDeclaredLost", "ItemRecovered",
    "RentalClosed",
    # condition chain
    "ConditionReportSubmitted", "ConditionReportCountersigned", "ConditionDiffComputed",
    "DamageReported", "DamageWaived", "DamageSettled", "RepairScheduled", "RepairCompleted",
    "DisputeOpened", "DisputeResolvedRepair", "DisputeResolvedNoFault",
    # value layer
    "InsuranceQuoted", "InsuranceBound", "PurchaseOpportunityDetected",
    "PurchaseOfferAccepted", "ItemSold", "ItemRetired",
    # derived facts
    "TrustSignalRecorded", "RiskFlagRaised", "AccessRevoked",
    # corrections
    "EventCompensated",
)


class LogError(Exception):
    """An append that would violate append-only-ness or the event vocabulary."""


@dataclass(frozen=True)
class Event:
    """One immutable fact. `event_seq` is the monotonic ordering key for the
    entire system -- timestamps are informational only, because two events in
    the same second are completely ordinary."""

    event_seq: int
    event_type: str
    payload: Mapping[str, Any]
    clock_utc: str
    ruleset_hash: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_seq": self.event_seq,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "clock_utc": self.clock_utc,
            "ruleset_hash": self.ruleset_hash,
        }

    @property
    def event_id(self) -> str:
        """Content hash over the whole event. Stable across machines and runs."""
        return f"evt_{sha256_hex(self.as_dict())[:12]}"


class EventLog:
    """An append-only sequence with a monotonic counter.

    The counter is seeded from the log itself, never from a clock or a random
    source (charter rule 1): rebuilding a log from disk and continuing to append
    produces exactly the sequence the original run produced.
    """

    def __init__(self, events: Sequence[Event] | None = None) -> None:
        self._events: list[Event] = list(events or ())
        self._next_seq = (self._events[-1].event_seq + 1) if self._events else 1
        for i, event in enumerate(self._events):
            if event.event_seq != i + 1:
                raise LogError(
                    f"log is not contiguous: position {i} carries event_seq {event.event_seq}"
                )

    # -- append ------------------------------------------------------------
    def append(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        clock_utc: str,
        ruleset_hash: str,
    ) -> Event:
        if event_type not in EVENT_TYPES:
            raise LogError(
                f"unknown event type {event_type!r}. The vocabulary is closed; "
                f"add it to EVENT_TYPES deliberately or use an existing type."
            )
        try:
            canonical_json(payload)   # fail loudly on floats, NaN, unserialisable values
        except (TypeError, ValueError) as exc:
            raise LogError(f"{event_type} payload is not canonically serialisable: {exc}") from None
        for key, value in payload.items():
            if isinstance(value, float):
                raise LogError(
                    f"{event_type}.{key} is a float. Money is integer cents, scores are "
                    f"integers, percentages are basis points (charter rule 3)."
                )
        event = Event(
            event_seq=self._next_seq,
            event_type=event_type,
            payload=dict(sorted(payload.items())),
            clock_utc=clock_utc,
            ruleset_hash=ruleset_hash,
        )
        self._events.append(event)
        self._next_seq += 1
        return event

    def compensate(self, target_event_seq: int, reason: str, clock_utc: str, ruleset_hash: str) -> Event:
        """The only way to "undo" anything: a new event that says so."""
        if not 1 <= target_event_seq <= len(self._events):
            raise LogError(f"cannot compensate non-existent event_seq {target_event_seq}")
        return self.append(
            "EventCompensated",
            {"target_event_seq": target_event_seq, "reason": reason},
            clock_utc,
            ruleset_hash,
        )

    # -- read --------------------------------------------------------------
    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    @property
    def next_seq(self) -> int:
        return self._next_seq

    def as_dicts(self) -> list[dict[str, Any]]:
        """The form L1 folds over -- plain mappings, no L2 types leaking down."""
        return [e.as_dict() for e in self._events]

    def of_type(self, *event_types: str) -> tuple[Event, ...]:
        wanted = set(event_types)
        return tuple(e for e in self._events if e.event_type in wanted)

    def compensated_seqs(self) -> frozenset[int]:
        return frozenset(
            e.payload["target_event_seq"] for e in self.of_type("EventCompensated")
        )

    @property
    def log_hash(self) -> str:
        """Content hash of the entire log. Two runs producing the same log hash
        are the same run; this is what --verify-determinism compares."""
        return sha256_hex([e.as_dict() for e in self._events])

    # -- persistence (JSONL, one canonical line per event) -----------------
    def write_jsonl(self, path: pathlib.Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(canonical_json(e.as_dict()) + "\n" for e in self._events),
            encoding="utf-8",
        )

    @classmethod
    def read_jsonl(cls, path: pathlib.Path) -> "EventLog":
        import json
        events = [
            Event(
                event_seq=d["event_seq"], event_type=d["event_type"],
                payload=d["payload"], clock_utc=d["clock_utc"], ruleset_hash=d["ruleset_hash"],
            )
            for d in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line)
        ]
        return cls(events)
