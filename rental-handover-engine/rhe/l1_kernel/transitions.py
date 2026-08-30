"""L1 — Lifecycle state machines, evaluated against state_transitions.yaml.

An illegal transition raises IllegalTransition. It is never a silent no-op, it
never leaves the machine quietly in its old state, and the error always names
the current state, the trigger, and either the legal triggers from here or the
exact guard that refused.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from rhe.l0_rules.loader import Ruleset
from rhe.l1_kernel.guards import GUARDS


class IllegalTransition(Exception):
    """The transition was rejected. Typed, loud, and carrying its reason."""

    def __init__(self, machine: str, state: str, trigger: str, reason: str, citation: str):
        self.machine, self.state, self.trigger = machine, state, trigger
        self.reason, self.citation = reason, citation
        super().__init__(
            f"{machine}: {trigger!r} is illegal from {state!r} -- {reason} ({citation})"
        )


class MachineError(Exception):
    """The machine itself is misconfigured (unknown machine, unknown guard)."""


@dataclass(frozen=True)
class TransitionDecision:
    machine: str
    from_state: str
    trigger: str
    to_state: str
    actor: str
    guards_evaluated: tuple[str, ...]
    citation: str

    def explain(self) -> str:
        guards = ", ".join(self.guards_evaluated) or "no guards"
        return (
            f"{self.machine}: {self.from_state} --{self.trigger}--> {self.to_state} "
            f"[{guards}] per {self.citation}"
        )


def _machine(machine: str, ruleset: Ruleset) -> Mapping[str, Any]:
    machines = ruleset.doc("state_transitions")["machines"]
    if machine not in machines:
        raise MachineError(f"unknown machine {machine!r}; known: {sorted(machines)}")
    return machines[machine]


def initial_state(machine: str, ruleset: Ruleset) -> str:
    return _machine(machine, ruleset)["initial"]


def legal_triggers(machine: str, state: str, ruleset: Ruleset) -> tuple[str, ...]:
    """Every trigger accepted from this state, sorted. Used in error messages and
    by the CLI to show what could happen next."""
    spec = _machine(machine, ruleset)
    return tuple(sorted({t["trigger"] for t in spec["transitions"] if t["from"] == state}))


def is_terminal(machine: str, state: str, ruleset: Ruleset) -> bool:
    return state in _machine(machine, ruleset)["terminal"]


def evaluate_transition(
    machine: str,
    current_state: str,
    trigger: str,
    ruleset: Ruleset,
    context: Mapping[str, Any] | None = None,
    actor: str | None = None,
) -> TransitionDecision:
    """Resolve (state, trigger) to exactly one next state, or raise.

    Pure: reads the ruleset and the caller's context, touches nothing else.
    """
    spec = _machine(machine, ruleset)
    params = ruleset.doc("state_transitions")["guard_parameters"]
    context = context or {}

    if current_state not in spec["states"]:
        raise MachineError(f"{machine}: unknown state {current_state!r}")

    candidates = [
        t for t in spec["transitions"]
        if t["from"] == current_state and t["trigger"] == trigger
    ]
    if not candidates:
        legal = legal_triggers(machine, current_state, ruleset)
        raise IllegalTransition(
            machine, current_state, trigger,
            f"no such transition; legal triggers here: {list(legal) or 'none (terminal state)'}",
            ruleset.citation("state_transitions"),
        )
    if len(candidates) > 1:
        # The ruleset would be ambiguous. Refuse rather than pick.
        raise MachineError(
            f"{machine}: {len(candidates)} transitions match "
            f"({current_state}, {trigger}) -- state_transitions.yaml is ambiguous"
        )

    transition = candidates[0]
    if actor is not None and transition["actor"] not in (actor, "system"):
        raise IllegalTransition(
            machine, current_state, trigger,
            f"actor {actor!r} may not fire this trigger; it belongs to {transition['actor']!r}",
            ruleset.citation("state_transitions"),
        )

    evaluated: list[str] = []
    for guard_name in transition["guards"]:          # declared order, deterministic
        guard = GUARDS.get(guard_name)
        if guard is None:
            raise MachineError(
                f"{machine}: transition {current_state}--{trigger}--> names guard "
                f"{guard_name!r}, which has no implementation in l1_kernel/guards.py"
            )
        ok, reason = guard(context, params)
        evaluated.append(guard_name)
        if not ok:
            raise IllegalTransition(
                machine, current_state, trigger,
                f"guard {guard_name} refused: {reason}",
                ruleset.citation("state_transitions"),
            )

    return TransitionDecision(
        machine=machine,
        from_state=current_state,
        trigger=trigger,
        to_state=transition["to"],
        actor=transition["actor"],
        guards_evaluated=tuple(evaluated),
        citation=ruleset.citation("state_transitions"),
    )
