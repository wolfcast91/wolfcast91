"""L5 — Access providers. Fake implementations with real-provider shapes.

Every method here has a real counterpart:

  issue_credential  -> Lockii `POST /access` on igloohome hardware: a
                       time-limited PIN computed on the lock's own clock, so it
                       works with no network at the door.
  validate          -> the lock validates offline; the platform learns about it
                       when the lock syncs. We model that as an explicit event
                       rather than pretending validation is synchronous.
  revoke            -> Lockii access revocation / PIN invalidation.
  access_log        -> the provider's audit trail, which the platform mirrors
                       into its own event log so custody is never provider-only.

The fake is deterministic: PINs come from rhe.l1_kernel.access.derive_secret,
never from a random source, and the access log is ordered by event_seq rather
than by timestamp because two door events in the same second are normal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from rhe.l1_kernel.access import AccessCredential, issue_credential, validate_credential


@dataclass(frozen=True)
class AccessLogEntry:
    event_seq: int
    rental_id: str
    location_id: str
    action: str          # issued | validated | rejected | revoked
    result: str
    at_utc: str


class AccessProvider(Protocol):
    def issue(self, rental_id: str, location_id: str, access_type: str,
              valid_from_epoch: int, valid_until_epoch: int,
              valid_from_utc: str, valid_until_utc: str) -> AccessCredential: ...
    def validate(self, rental_id: str, presented_secret: str, at_epoch: int, at_utc: str) -> tuple[bool, str]: ...
    def revoke(self, rental_id: str, at_utc: str) -> str: ...


class FakeAccessProvider:
    """In-memory smart-lock / gate-controller / depot-counter stand-in.

    Real integration target: Lockii (booking + identity + digital lock access +
    GPS-confirmed returns) running on igloohome locks. Swapping this class for
    an HTTP client is the entire integration; nothing in L0-L4 changes.
    """

    def __init__(self) -> None:
        self._credentials: dict[str, AccessCredential] = {}
        self._revoked: set[str] = set()
        self._log: list[AccessLogEntry] = []
        self._seq = 0

    def _record(self, rental_id: str, location_id: str, action: str, result: str, at_utc: str) -> None:
        self._seq += 1
        self._log.append(AccessLogEntry(self._seq, rental_id, location_id, action, result, at_utc))

    def issue(self, rental_id, location_id, access_type, valid_from_epoch,
              valid_until_epoch, valid_from_utc, valid_until_utc) -> AccessCredential:
        credential = issue_credential(
            rental_id, location_id, access_type,
            valid_from_epoch, valid_until_epoch, valid_from_utc, valid_until_utc,
        )
        self._credentials[rental_id] = credential
        self._revoked.discard(rental_id)
        self._record(rental_id, location_id, "issued", credential.access_type, valid_from_utc)
        return credential

    def validate(self, rental_id: str, presented_secret: str, at_epoch: int, at_utc: str) -> tuple[bool, str]:
        credential = self._credentials.get(rental_id)
        if credential is None:
            self._record(rental_id, "", "rejected", "no_credential_issued", at_utc)
            return False, "no_credential_issued"
        ok, reason = validate_credential(
            credential, presented_secret, at_epoch, revoked=rental_id in self._revoked
        )
        self._record(rental_id, credential.location_id, "validated" if ok else "rejected", reason, at_utc)
        return ok, reason

    def revoke(self, rental_id: str, at_utc: str) -> str:
        credential = self._credentials.get(rental_id)
        if credential is None:
            return "no_credential_issued"
        self._revoked.add(rental_id)
        self._record(rental_id, credential.location_id, "revoked", "revoked", at_utc)
        return credential.secret

    def credential_for(self, rental_id: str) -> AccessCredential | None:
        return self._credentials.get(rental_id)

    @property
    def access_log(self) -> tuple[AccessLogEntry, ...]:
        # Ordered by event_seq, never by timestamp (precedence.yaml:sort_keys.access_log)
        return tuple(sorted(self._log, key=lambda e: e.event_seq))
