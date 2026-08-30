"""L1 — Trust scoring. A pure integer fold, never an incremental counter.

The score is recomputed from event zero every single time it is read. That is
deliberately "wasteful" and it is the whole point: a score that is only ever
derived cannot silently diverge from the log the way an incrementally-mutated
counter eventually always does. The projection table stores a cached copy that a
replay is entitled to overwrite without asking.

Trust reacts to SIGNALS, not raw events. The command layer (L4) translates a
domain event into zero or more `TrustSignalRecorded` events naming a signal from
trust_weights.yaml and the event that caused it. Two benefits: this function
stays a two-line fold, and every point a user's score ever moved is a row in the
log with a cause attached.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from rhe.l0_rules.loader import Ruleset


class TrustError(Exception):
    """An unknown signal, or an unknown subject kind."""


@dataclass(frozen=True)
class TrustContribution:
    """One movement of the score, with its cause."""

    event_seq: int
    signal: str
    delta: int
    running_total: int
    caused_by_event: str


@dataclass(frozen=True)
class TrustScore:
    """A score you can defend line by line."""

    subject_kind: str
    subject_id: str
    score: int
    band: str
    baseline: int
    contributions: tuple[TrustContribution, ...]
    events_considered: int
    citation: str

    def explain(self) -> str:
        return (
            f"{self.subject_kind} {self.subject_id}: {self.score}/1000 ({self.band}), "
            f"baseline {self.baseline} + {len(self.contributions)} signal(s), "
            f"per {self.citation}"
        )


def _weights(subject_kind: str, ruleset: Ruleset) -> Mapping[str, int]:
    doc = ruleset.doc("trust_weights")
    key = {"user": "user_weights", "item": "item_weights"}.get(subject_kind)
    if key is None:
        raise TrustError(f"no trust weights for subject kind {subject_kind!r}")
    return doc[key]


def band_for_score(score: int, ruleset: Ruleset) -> str:
    for band in ruleset.doc("trust_weights")["trust_bands"]:
        if band["min"] <= score <= band["max"]:
            return band["band"]
    raise TrustError(f"score {score} outside every declared band")


def compute_trust(
    subject_kind: str,
    subject_id: str,
    events: Sequence[Mapping[str, Any]],
    ruleset: Ruleset,
) -> TrustScore:
    """Fold every trust signal for one subject, in event_seq order, from zero.

    Clamping happens after EACH signal, not once at the end -- so the order of
    signals is significant and therefore fixed by event_seq, never by whatever
    order a caller happened to hand them over in.
    """
    doc = ruleset.doc("trust_weights")
    weights = _weights(subject_kind, ruleset)
    lo, hi = doc["scale"]["min"], doc["scale"]["max"]
    baseline = doc["subjects"][subject_kind]["baseline"]

    relevant = [
        e for e in events
        if e["event_type"] == "TrustSignalRecorded"
        and e["payload"]["subject_kind"] == subject_kind
        and e["payload"]["subject_id"] == subject_id
    ]
    relevant.sort(key=lambda e: e["event_seq"])   # charter rule 4

    total = baseline
    contributions: list[TrustContribution] = []
    for event in relevant:
        signal = event["payload"]["signal"]
        if signal not in weights:
            raise TrustError(
                f"signal {signal!r} is not defined for {subject_kind} in "
                f"{ruleset.citation('trust_weights')}"
            )
        delta = weights[signal]
        total = max(lo, min(hi, total + delta))
        contributions.append(
            TrustContribution(
                event_seq=event["event_seq"],
                signal=signal,
                delta=delta,
                running_total=total,
                caused_by_event=event["payload"].get("caused_by_event", ""),
            )
        )

    return TrustScore(
        subject_kind=subject_kind,
        subject_id=subject_id,
        score=total,
        band=band_for_score(total, ruleset),
        baseline=baseline,
        contributions=tuple(contributions),
        events_considered=len(relevant),
        citation=ruleset.citation("trust_weights"),
    )


# ---------------------------------------------------------------------------
# Tier graduation -- an item earning a cheaper handover mechanism by proving it.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraduationDecision:
    granted: bool
    from_tier: int
    to_tier: int | None
    reason: str
    citation: str
    unmet: tuple[str, ...] = ()


@dataclass(frozen=True)
class ItemHistory:
    """The integer facts graduation depends on. All derived from the log."""

    clean_handovers_consecutive: int
    disputes_lifetime: int
    item_trust: int
    enclosable: bool


def evaluate_graduation(
    classified_tier: int,
    history: ItemHistory,
    ruleset: Ruleset,
) -> GraduationDecision:
    """Explicit integer thresholds from the ruleset. No heuristics, no scoring."""
    doc = ruleset.doc("trust_weights")["tier_graduation"]
    citation = ruleset.citation("trust_weights")

    paths = [p for p in doc["enabled_paths"] if p["from_tier"] == classified_tier]
    if not paths:
        return GraduationDecision(
            granted=False, from_tier=classified_tier, to_tier=None,
            reason=f"no graduation path defined from tier {classified_tier}", citation=citation,
        )

    # Deterministic: consider paths in ascending target tier, take the first that
    # both applies to this item's physics and has all requirements met.
    considered: list[tuple[int, tuple[str, ...]]] = []
    for path in sorted(paths, key=lambda p: p["to_tier"]):
        req = path["requires"]
        if req["item_must_be_enclosable"] != history.enclosable:
            continue   # a graduation may not violate physics
        unmet: list[str] = []
        if history.clean_handovers_consecutive < req["clean_handovers"]:
            unmet.append(
                f"clean_handovers {history.clean_handovers_consecutive}/{req['clean_handovers']}"
            )
        if history.item_trust < req["min_item_trust"]:
            unmet.append(f"item_trust {history.item_trust}/{req['min_item_trust']}")
        if history.disputes_lifetime > req["max_disputes_lifetime"]:
            unmet.append(
                f"disputes {history.disputes_lifetime}>{req['max_disputes_lifetime']}"
            )
        if not unmet:
            return GraduationDecision(
                granted=True, from_tier=classified_tier, to_tier=path["to_tier"],
                reason=(
                    f"{history.clean_handovers_consecutive} consecutive clean handovers, "
                    f"item trust {history.item_trust}, {history.disputes_lifetime} disputes"
                ),
                citation=citation,
            )
        considered.append((path["to_tier"], tuple(unmet)))

    if not considered:
        return GraduationDecision(
            granted=False, from_tier=classified_tier, to_tier=None,
            reason="no graduation path matches this item's physical attributes",
            citation=citation,
        )
    to_tier, unmet = considered[0]
    return GraduationDecision(
        granted=False, from_tier=classified_tier, to_tier=to_tier,
        reason="requirements not yet met", citation=citation, unmet=unmet,
    )


def evaluate_risk_flags(facts: Mapping[str, Any], ruleset: Ruleset) -> tuple[Mapping[str, Any], ...]:
    """Hard-rule risk flags. Every flag names the exact rule that fired.

    `facts` supplies the named integers/booleans the rules reference. Rules are
    evaluated by an explicit dispatch table -- not by eval() -- so a ruleset file
    can never become a code-execution surface.
    """
    doc = ruleset.doc("trust_weights")
    # Absent facts must not accidentally trip a flag, so a missing trust score
    # reads as the top of the declared scale. That ceiling comes from the
    # ruleset, not from a literal in this file.
    no_trust_data = doc["scale"]["max"]
    bands = {b["band"]: b for b in doc["trust_bands"]}
    fair_floor = bands["fair"]["min"]        # below this is the `new` band
    good_floor = bands["good"]["min"]        # below this is not yet proven

    predicates = {
        "unverified_identity":   lambda f: f.get("id_verified") is False,
        "repeat_disputes":       lambda f: f.get("n_disputes_90d", 0) >= 2,
        "overdue_history":       lambda f: f.get("overdue_returns_lifetime", 0) >= 1,
        "low_trust":             lambda f: f.get("user_trust", no_trust_data) < fair_floor,
        "lost_item_history":     lambda f: f.get("items_declared_lost_lifetime", 0) >= 1,
        "high_value_new_renter": lambda f: (
            f.get("value_band") in ("high", "very_high")
            and f.get("user_trust", no_trust_data) < good_floor
        ),
    }
    fired: list[Mapping[str, Any]] = []
    for spec in doc["risk_flags"]:   # declared order
        flag_id = spec["flag_id"]
        predicate = predicates.get(flag_id)
        if predicate is None:
            raise TrustError(f"risk flag {flag_id!r} has no implemented predicate")
        if predicate(facts):
            fired.append({
                "flag_id": flag_id,
                "rule": spec["rule"],
                "severity": spec["severity"],
                "citation": ruleset.citation("trust_weights"),
            })
    return tuple(fired)
