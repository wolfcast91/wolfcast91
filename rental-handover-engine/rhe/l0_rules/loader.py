"""L0 — Ruleset layer.

Versioned data files, hashed on load, immutable at runtime. Nothing below this
layer is allowed to contain a threshold, a weight, or a rate. If you find a
magic number anywhere in L1-L6, it is a bug, and the fix is to move it here.

The loaded `Ruleset` is frozen: attempting to mutate it raises. Every decision
produced anywhere in the system carries `ruleset_version` and `ruleset_hash` so
it can be re-derived years later against the rules that actually produced it.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from rhe.canonical import sha256_hex, short_hash

RULESET_DIR = pathlib.Path(__file__).resolve().parent / "rulesets"

# Explicit, ordered list. Loading is not a directory scan: a stray file must not
# silently change the composite hash, and a missing file must be a hard error.
RULESET_FILES: tuple[str, ...] = (
    "category_tree.yaml",
    "complementary_items.yaml",
    "damage_taxonomy.yaml",
    "handover_steps.yaml",
    "insurance_rates.yaml",
    "precedence.yaml",
    "state_transitions.yaml",
    "tier_rules.yaml",
    "trust_weights.yaml",
)


class RulesetError(Exception):
    """A ruleset file is malformed, inconsistent, or violates the charter."""


def _freeze(value: Any) -> Any:
    """Recursively make a loaded document read-only."""
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Ruleset:
    """An immutable, hashed snapshot of every L0 file."""

    documents: Mapping[str, Any]     # stem -> frozen document
    file_hashes: Mapping[str, str]   # stem -> sha256 hex of that document
    ruleset_hash: str                # sha256 over {stem: file_hash}
    versions: Mapping[str, int]      # stem -> ruleset_version

    # -- access ------------------------------------------------------------
    def doc(self, stem: str) -> Any:
        try:
            return self.documents[stem]
        except KeyError:
            raise RulesetError(f"no such ruleset document: {stem!r}") from None

    @property
    def short(self) -> str:
        return short_hash(self.ruleset_hash)

    def citation(self, stem: str, row_id: str | None = None) -> str:
        """The explainability primitive: a decision's provenance as one string.

        e.g. `tier_rules.yaml v3 row R07 (ruleset a3f91b2c)`
        """
        version = self.versions.get(stem, 0)
        row = f" row {row_id}" if row_id else ""
        return f"{stem}.yaml v{version}{row} (ruleset {self.short})"


def _validate(stem: str, doc: Any) -> None:
    """Charter checks that must hold before any rule is ever evaluated."""
    if not isinstance(doc, dict):
        raise RulesetError(f"{stem}: top level must be a mapping")
    if "ruleset_version" not in doc:
        raise RulesetError(f"{stem}: missing ruleset_version")

    if stem == "tier_rules":
        rows = doc["rows"]
        precedences = [r["precedence"] for r in rows]
        if len(set(precedences)) != len(precedences):
            raise RulesetError(
                f"{stem}: duplicate precedence values -- tie-breaking would fall "
                f"back to evaluation order, which charter rule 7 forbids"
            )
        ids = [r["id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise RulesetError(f"{stem}: duplicate row ids")
        domains = {a: set(_as_str_values(spec["domain"])) for a, spec in doc["attributes"].items()}
        for row in rows:
            for attr, accepted in (row.get("when") or {}).items():
                if attr not in domains:
                    raise RulesetError(f"{stem}: row {row['id']} matches unknown attribute {attr!r}")
                unknown = set(_as_str_values(accepted)) - domains[attr]
                if unknown:
                    raise RulesetError(
                        f"{stem}: row {row['id']} accepts values outside the "
                        f"declared domain of {attr!r}: {sorted(unknown)}"
                    )
            if not (row.get("when") or {}):
                raise RulesetError(
                    f"{stem}: row {row['id']} has an empty `when` -- that is a "
                    f"catch-all, and precedence.yaml sets allow_catch_all_row: false"
                )

    if stem == "state_transitions":
        for machine, spec in doc["machines"].items():
            states = set(spec["states"])
            for t in spec["transitions"]:
                if t["from"] not in states or t["to"] not in states:
                    raise RulesetError(f"{stem}: {machine} transition references an unknown state: {t}")

    if stem == "damage_taxonomy":
        tag_ids = [t["tag_id"] for t in doc["tags"]]
        if len(set(tag_ids)) != len(tag_ids):
            raise RulesetError(f"{stem}: duplicate tag_id")
        components = {c["component_id"] for c in doc["components"]}
        for t in doc["tags"]:
            if t["component"] not in components:
                raise RulesetError(f"{stem}: tag {t['tag_id']} has unknown component {t['component']!r}")
        unknown = set(doc["blocking_on_new_appearance"]) - set(tag_ids)
        if unknown:
            raise RulesetError(f"{stem}: blocking_on_new_appearance names unknown tags {sorted(unknown)}")


def _as_str_values(values: Any) -> list[str]:
    """YAML booleans become the strings "true"/"false".

    The classifier operates on strings only, so `enclosable: [true]` in the
    ruleset and `enclosable="true"` on an item compare equal without the
    evaluator ever knowing about Python's bool type.
    """
    out = []
    for v in values:
        out.append(canonical_attr_value(v))
    return out


def canonical_attr_value(value: Any) -> str:
    """The one place a raw attribute value becomes its canonical string form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def load_ruleset(directory: pathlib.Path | None = None) -> Ruleset:
    """Load, validate, hash and freeze every ruleset file. Call once, at boot."""
    directory = directory or RULESET_DIR
    documents: dict[str, Any] = {}
    file_hashes: dict[str, str] = {}
    versions: dict[str, int] = {}

    for filename in RULESET_FILES:  # explicit order, not a directory listing
        path = directory / filename
        if not path.is_file():
            raise RulesetError(f"missing ruleset file: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        stem = path.stem
        _validate(stem, raw)
        documents[stem] = _freeze(raw)
        # Hash the PARSED document, not the bytes: comments and formatting must
        # not change a decision's provenance, but any semantic edit must.
        file_hashes[stem] = sha256_hex(raw)
        versions[stem] = raw["ruleset_version"]

    return Ruleset(
        documents=MappingProxyType(documents),
        file_hashes=MappingProxyType(file_hashes),
        ruleset_hash=sha256_hex(file_hashes),
        versions=MappingProxyType(versions),
    )
