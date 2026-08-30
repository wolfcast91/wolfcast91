"""Canonical serialisation. The single definition of "the same value" in this
system.

Everything that gets hashed -- ruleset files, entity IDs, golden output -- goes
through here first. One function, one encoding, no options: that is what makes a
hash computed on one machine equal to a hash computed on another.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace, ASCII only.

    Sorted keys defeat dict insertion order (charter rule 4). ASCII escaping
    defeats locale- and terminal-dependent encoding. Compact separators defeat
    pretty-printer drift.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,   # floats are banned anyway; NaN would break equality
    )


def sha256_hex(value: Any) -> str:
    """SHA-256 of the canonical JSON encoding of `value`."""
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def short_hash(hex_digest: str, length: int = 8) -> str:
    """The form used in human-facing decision citations: `a3f91b2c`."""
    return hex_digest[:length]
