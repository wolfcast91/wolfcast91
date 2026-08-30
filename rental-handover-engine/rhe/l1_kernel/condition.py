"""L1 — Condition chain and the diff that drives it.

Every renter documents the item before use, confirming or extending what the
previous renter logged. The result is a timestamped chain per item -- the risk
data that makes automated insurance pricing possible.

The diff is ORDER-INDEPENDENT by construction: reports carry tag SETS, and every
output collection is sorted by the canonical key from precedence.yaml. Comparing
A to B yields the same result no matter how either report's tags were entered.

No photo is ever read. Photos are evidence slots referenced by name; the
decision inputs are tags from the closed taxonomy and nothing else.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from rhe.l0_rules.loader import Ruleset


class ConditionError(Exception):
    """A tag outside the closed taxonomy, or a malformed report."""


@dataclass(frozen=True)
class ConditionReport:
    """One link in an item's condition chain.

    Structured throughout: no free text anywhere a tag would do. `note_tags`
    exists for observations that are not damage; genuinely unrepresentable
    findings use the single escape tag `other_requires_human`, which always
    routes out of the automated path.
    """

    report_id: str
    item_id: str
    rental_id: str
    phase: str                        # "pre" | "post" | "partner_intake" | "inspection"
    submitted_by: str                 # user_id / partner staff id
    submitted_at_utc: str             # ISO 8601, second precision, injected clock
    event_seq: int
    damage_tags: tuple[str, ...]      # canonical sorted order
    photo_slots: tuple[str, ...]      # slot names filled, canonical sorted order
    accessory_manifest: tuple[str, ...] = ()
    prev_report_id: str | None = None
    countersigned_by: tuple[str, ...] = ()

    def with_canonical_ordering(self) -> "ConditionReport":
        """Sorting is not cosmetic here -- it is what makes the diff total-order-free."""
        return ConditionReport(
            report_id=self.report_id,
            item_id=self.item_id,
            rental_id=self.rental_id,
            phase=self.phase,
            submitted_by=self.submitted_by,
            submitted_at_utc=self.submitted_at_utc,
            event_seq=self.event_seq,
            damage_tags=tuple(sorted(set(self.damage_tags))),
            photo_slots=tuple(sorted(set(self.photo_slots))),
            accessory_manifest=tuple(sorted(set(self.accessory_manifest))),
            prev_report_id=self.prev_report_id,
            countersigned_by=tuple(sorted(set(self.countersigned_by))),
        )


@dataclass(frozen=True)
class Finding:
    """One damage tag with everything the ruleset says about it."""

    tag_id: str
    component_id: str
    severity: str
    severity_rank: int
    repair_cost_band: str
    deposit_hold_cents: int
    label: str


@dataclass(frozen=True)
class ConditionDiff:
    """The comparison of a report against its predecessor in the chain."""

    prev_report_id: str | None
    report_id: str
    appeared: tuple[Finding, ...]       # in this report, not in the previous one
    confirmed: tuple[Finding, ...]      # present in both -- the chain agrees
    disappeared: tuple[Finding, ...]    # in the previous, gone now (repair, or a disagreement)
    blocking: tuple[str, ...]           # newly appeared tags that block the next rental
    missing_accessories: tuple[str, ...]
    deposit_hold_cents: int             # integer sum over newly appeared findings
    requires_human: bool
    citation: str

    @property
    def is_clean(self) -> bool:
        return not self.appeared and not self.missing_accessories

    @property
    def chain_disagreement(self) -> bool:
        """A tag vanishing without a repair event is two renters contradicting
        each other. The system records it and routes it; it never adjudicates."""
        return bool(self.disappeared)


def _tag_index(ruleset: Ruleset) -> Mapping[str, Finding]:
    tax = ruleset.doc("damage_taxonomy")
    severities = tax["severity_scale"]
    bands = tax["repair_cost_bands"]
    return {
        t["tag_id"]: Finding(
            tag_id=t["tag_id"],
            component_id=t["component"],
            severity=t["severity"],
            severity_rank=severities[t["severity"]]["rank"],
            repair_cost_band=t["repair_cost_band"],
            deposit_hold_cents=bands[t["repair_cost_band"]]["deposit_hold_cents"],
            label=t["label"],
        )
        for t in tax["tags"]
    }


def validate_tags(tags: Iterable[str], ruleset: Ruleset) -> tuple[str, ...]:
    """Reject anything outside the closed vocabulary. No free text gets in."""
    index = _tag_index(ruleset)
    unknown = sorted(set(tags) - set(index))
    if unknown:
        raise ConditionError(
            f"tags outside the closed taxonomy: {unknown} "
            f"({ruleset.citation('damage_taxonomy')})"
        )
    return tuple(sorted(set(tags)))


def _sorted_findings(tag_ids: Iterable[str], index: Mapping[str, Finding]) -> tuple[Finding, ...]:
    # precedence.yaml:sort_keys.damage_findings = [component_id, tag_id]
    return tuple(sorted((index[t] for t in tag_ids), key=lambda f: (f.component_id, f.tag_id)))


def diff_condition(
    previous: ConditionReport | None,
    current: ConditionReport,
    ruleset: Ruleset,
) -> ConditionDiff:
    """Compare a report against the previous chain entry.

    Pure set arithmetic over sorted tag sets. Given the same two reports it
    returns the same diff regardless of tag insertion order, dict iteration
    order, or which machine it runs on.
    """
    index = _tag_index(ruleset)
    tax = ruleset.doc("damage_taxonomy")

    current = current.with_canonical_ordering()
    prev_tags = set(validate_tags(previous.damage_tags, ruleset)) if previous else set()
    curr_tags = set(validate_tags(current.damage_tags, ruleset))

    appeared_ids = curr_tags - prev_tags
    confirmed_ids = curr_tags & prev_tags
    disappeared_ids = prev_tags - curr_tags

    blocking_set = set(tax["blocking_on_new_appearance"])
    blocking = tuple(sorted(appeared_ids & blocking_set))

    prev_manifest = set(previous.accessory_manifest) if previous else set()
    missing_accessories = tuple(sorted(prev_manifest - set(current.accessory_manifest)))

    appeared = _sorted_findings(appeared_ids, index)
    deposit_hold = sum(f.deposit_hold_cents for f in appeared)   # integers only

    return ConditionDiff(
        prev_report_id=previous.report_id if previous else None,
        report_id=current.report_id,
        appeared=appeared,
        confirmed=_sorted_findings(confirmed_ids, index),
        disappeared=_sorted_findings(disappeared_ids, index),
        blocking=blocking,
        missing_accessories=missing_accessories,
        deposit_hold_cents=deposit_hold,
        requires_human="other_requires_human" in appeared_ids,
        citation=ruleset.citation("damage_taxonomy"),
    )


def required_photo_slots(tier: int, ruleset: Ruleset) -> tuple[str, ...]:
    """Photo slots a report must fill, per handover tier."""
    tiers = ruleset.doc("handover_steps")["tiers"]
    if tier not in tiers:
        raise ConditionError(f"no photo slots defined for tier {tier}")
    return tuple(tiers[tier]["photo_slots"])
