"""L5 — Photo storage. Content-addressed, and never a decision input.

Photos are EVIDENCE attached to a structured claim. Nothing in this system reads
a pixel: no classifier, no premium, no trust delta depends on image content. The
store hands back a content-addressed reference so a condition report can point
at an immutable blob, and that is the entire contract.

Real integration target: S3-compatible object storage with content-addressed
keys and object-lock retention, so evidence cannot be swapped after a dispute
opens. The fake stores a hash of a caption string -- enough to make the reference
stable across replays without any binary data in the repo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from rhe.canonical import sha256_hex


@dataclass(frozen=True)
class PhotoRef:
    slot: str
    photo_ref: str          # content-addressed key
    captured_at_utc: str


class PhotoStore(Protocol):
    def put(self, rental_id: str, slot: str, descriptor: str, at_utc: str) -> PhotoRef: ...


class FakePhotoStore:
    """Deterministic stand-in. The `descriptor` is a scenario-authored stand-in
    for image bytes; identical descriptors yield identical refs, which is what
    keeps a replay byte-identical."""

    def __init__(self) -> None:
        self._objects: dict[str, str] = {}

    def put(self, rental_id: str, slot: str, descriptor: str, at_utc: str) -> PhotoRef:
        key = f"pho_{sha256_hex({'rental_id': rental_id, 'slot': slot, 'descriptor': descriptor})[:16]}"
        self._objects[key] = descriptor
        return PhotoRef(slot=slot, photo_ref=key, captured_at_utc=at_utc)

    def get_descriptor(self, photo_ref: str) -> str | None:
        return self._objects.get(photo_ref)

    @property
    def object_count(self) -> int:
        return len(self._objects)
