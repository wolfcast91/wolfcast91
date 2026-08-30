"""L1 — Tier classifier.

A thin evaluator over tier_rules.yaml. It contains no thresholds, no item
knowledge and no default case. Read it and you will find: resolve attributes,
find matching rows, take the lowest precedence, return a decision with its
citation. That is the whole classifier -- the intelligence is in the table.

Pure: no I/O, no clock, no mutable state. The `ruleset` argument is the only
way facts enter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from rhe.l0_rules.loader import Ruleset, canonical_attr_value


class ClassificationError(Exception):
    """The classifier could not produce exactly one tier. Never swallowed."""


@dataclass(frozen=True)
class AttributeResolution:
    """How each attribute value was arrived at -- the audit trail for a listing."""

    attributes: Mapping[str, str]
    sources: Mapping[str, str]        # attribute -> "category:<node_id>" | "owner_override"
    category_path: tuple[str, ...]    # root -> leaf


@dataclass(frozen=True)
class TierDecision:
    """A classification plus everything needed to defend it to an underwriter."""

    tier: int
    row_id: str
    precedence: int
    rationale: str
    citation: str
    ruleset_hash: str
    ruleset_version: int
    attributes: Mapping[str, str]
    all_matching_rows: tuple[str, ...] = field(default=())

    def explain(self) -> str:
        return f"Tier {self.tier}, because {self.citation}"


def attribute_domains(ruleset: Ruleset) -> dict[str, tuple[str, ...]]:
    """Declared domain of every classifier attribute, canonicalised to strings."""
    attrs = ruleset.doc("tier_rules")["attributes"]
    return {
        name: tuple(canonical_attr_value(v) for v in spec["domain"])
        for name, spec in attrs.items()
    }


def resolve_attributes(
    category_id: str,
    ruleset: Ruleset,
    owner_overrides: Mapping[str, Any] | None = None,
) -> AttributeResolution:
    """Walk the category tree root -> leaf, then apply permitted owner overrides.

    Every value carries where it came from, so a surprising tier can always be
    traced to either a category default or a specific owner's claim.
    """
    tree = ruleset.doc("category_tree")
    nodes = {n["id"]: n for n in tree["nodes"]}
    if category_id not in nodes:
        raise ClassificationError(f"unknown category: {category_id!r}")

    # Build the root -> leaf path first, so parents are applied before children.
    path: list[str] = []
    cursor: str | None = category_id
    while cursor is not None:
        if cursor in path:
            raise ClassificationError(f"cycle in category tree at {cursor!r}")
        path.append(cursor)
        cursor = nodes[cursor].get("parent")
    path.reverse()

    attributes: dict[str, str] = {}
    sources: dict[str, str] = {}
    for node_id in path:
        for key, value in sorted((nodes[node_id].get("defaults") or {}).items()):
            attributes[key] = canonical_attr_value(value)
            sources[key] = f"category:{node_id}"

    overridable = set(tree["owner_overridable"])
    forbidden = set(tree["overrides_never_allowed"])
    for key, value in sorted((owner_overrides or {}).items()):
        if key in forbidden:
            raise ClassificationError(
                f"attribute {key!r} may never be overridden by an owner "
                f"({ruleset.citation('category_tree')})"
            )
        if key not in overridable:
            raise ClassificationError(f"attribute {key!r} is not owner-overridable")
        attributes[key] = canonical_attr_value(value)
        sources[key] = "owner_override"

    domains = attribute_domains(ruleset)
    missing = sorted(set(domains) - set(attributes))
    if missing:
        raise ClassificationError(
            f"category {category_id!r} resolves to an incomplete attribute set; "
            f"missing {missing}. A leaf category must be total."
        )
    for name, value in sorted(attributes.items()):
        if name in domains and value not in domains[name]:
            raise ClassificationError(
                f"attribute {name}={value!r} is outside its declared domain "
                f"{list(domains[name])}"
            )

    return AttributeResolution(
        attributes=dict(sorted(attributes.items())),
        sources=dict(sorted(sources.items())),
        category_path=tuple(path),
    )


def _row_matches(row: Mapping[str, Any], attributes: Mapping[str, str]) -> bool:
    """A row matches when every constrained attribute is in its accepted set.

    An attribute absent from `when` is a wildcard. There is no negation and no
    expression language on purpose: a rule you cannot read is a rule you cannot
    hand to an insurer.
    """
    for attr, accepted in row["when"].items():
        accepted_values = {canonical_attr_value(v) for v in accepted}
        if attributes.get(attr) not in accepted_values:
            return False
    return True


def classify_tier(attributes: Mapping[str, str], ruleset: Ruleset) -> TierDecision:
    """Map a complete attribute set to exactly one tier.

    Total by construction: rows R09 and R10 partition the `enclosable` domain
    between them, so at least one row always matches. Unique by construction:
    precedence values are unique (enforced at load) and the lowest wins.
    """
    doc = ruleset.doc("tier_rules")
    domains = attribute_domains(ruleset)

    missing = sorted(set(domains) - set(attributes))
    if missing:
        raise ClassificationError(f"incomplete attribute set; missing {missing}")

    # Deterministic evaluation order: by precedence, never by file order.
    rows = sorted(doc["rows"], key=lambda r: r["precedence"])
    matching = [r for r in rows if _row_matches(r, attributes)]

    if not matching:
        # Unreachable if the exhaustiveness proof passes. Loud, not silent.
        raise ClassificationError(
            f"no rule row matched {dict(sorted(attributes.items()))} -- "
            f"tier_rules.yaml is not total. Run tools/prove_exhaustiveness.py."
        )

    winner = matching[0]
    return TierDecision(
        tier=winner["tier"],
        row_id=winner["id"],
        precedence=winner["precedence"],
        rationale=" ".join(winner["rationale"].split()),
        citation=ruleset.citation("tier_rules", winner["id"]),
        ruleset_hash=ruleset.ruleset_hash,
        ruleset_version=doc["ruleset_version"],
        attributes=dict(sorted(attributes.items())),
        all_matching_rows=tuple(r["id"] for r in matching),
    )


def classify_category(
    category_id: str,
    ruleset: Ruleset,
    owner_overrides: Mapping[str, Any] | None = None,
) -> tuple[TierDecision, AttributeResolution]:
    """Convenience: resolve a category to attributes, then classify them."""
    resolution = resolve_attributes(category_id, ruleset, owner_overrides)
    return classify_tier(resolution.attributes, ruleset), resolution


def handover_steps(tier: int, ruleset: Ruleset) -> tuple[Mapping[str, Any], ...]:
    """The ordered choreography for a tier, sorted by step_index (never file order)."""
    tiers = ruleset.doc("handover_steps")["tiers"]
    if tier not in tiers:
        raise ClassificationError(f"no handover choreography defined for tier {tier}")
    return tuple(sorted(tiers[tier]["steps"], key=lambda s: s["step_index"]))


def tier_name(tier: int, ruleset: Ruleset) -> str:
    return ruleset.doc("handover_steps")["tiers"][tier]["name"]
