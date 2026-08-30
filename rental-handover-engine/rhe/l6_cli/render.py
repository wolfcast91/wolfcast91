"""L6 — Terminal rendering. Presentation only, zero logic.

Everything here reads projections and formats them. No decision is made in this
module and none may ever be: if you find yourself wanting an `if` that changes
an outcome rather than a layout, it belongs in L1.

Deterministic output rules, because every line lands in a golden file:
  * no wall-clock timestamps -- only the injected clock's own time
  * no run ids, no durations, no memory addresses
  * no ANSI colour (a terminal setting must not change the bytes)
  * every collection is rendered in its declared sort order
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

WIDTH = 96
H1, H2, H3 = "=", "-", "."


def cents(amount: int | None) -> str:
    """Integer cents -> a human amount. Formatting only; the value stays integer."""
    if amount is None:
        return "-"
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    return f"{sign}{amount // 100},{amount % 100:02d} EUR"


def rule(char: str = H2, width: int = WIDTH) -> str:
    return char * width


def banner(title: str, subtitle: str = "") -> list[str]:
    lines = [rule(H1), f"  {title}"]
    if subtitle:
        lines.append(f"  {subtitle}")
    lines.append(rule(H1))
    return lines


def section(label: str) -> list[str]:
    return ["", f"{label}", rule(H2, min(WIDTH, max(len(label), 24)))]


def kv(pairs: Sequence[tuple[str, Any]], indent: int = 2) -> list[str]:
    if not pairs:
        return []
    width = max(len(str(k)) for k, _ in pairs)
    pad = " " * indent
    return [f"{pad}{str(k).ljust(width)}  {v}" for k, v in pairs]


def bullets(items: Iterable[str], marker: str = "-", indent: int = 2) -> list[str]:
    pad = " " * indent
    return [f"{pad}{marker} {item}" for item in items]


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]], indent: int = 2) -> list[str]:
    """Fixed-width table. Column widths derive only from content, never from a
    terminal size, so the same data always renders the same bytes."""
    if not rows:
        return [" " * indent + "(none)"]
    cells = [[str(c) for c in row] for row in rows]
    widths = [
        max(len(str(headers[i])), max((len(row[i]) for row in cells), default=0))
        for i in range(len(headers))
    ]
    pad = " " * indent
    out = [pad + "  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))]
    out.append(pad + "  ".join("-" * w for w in widths))
    for row in cells:
        out.append(pad + "  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
    return out


def step_header(index: int, total: int, actor: str, label: str, clock_utc: str) -> list[str]:
    return [
        "",
        f"  [{index}/{total}] {label}",
        f"        actor: {actor:<14} clock: {clock_utc}",
    ]


def handover_plan(tier: int, tier_label: str, steps: Sequence[Mapping[str, Any]], citation: str) -> list[str]:
    """The choreography the item's tier prescribes, straight out of the ruleset."""
    out = section(f"HANDOVER PLAN - Tier {tier}: {tier_label}")
    out += bullets([f"per {citation}"], marker="*")
    out.append("")
    out += table(
        ["#", "actor", "step", "logs"],
        [
            [s["step_index"], s["actor"], s["label"], ", ".join(s["logs"])]
            for s in steps
        ],
    )
    return out


def condition_chain(chain: Sequence[Mapping[str, Any]], user_names: Mapping[str, str]) -> list[str]:
    """The item's timestamped condition history -- the risk data an insurer wants."""
    out = section("CONDITION CHAIN")
    if not chain:
        return out + ["  (empty)"]
    rows = []
    for index, report in enumerate(chain):
        appeared = report.get("diff_appeared") or []
        rows.append([
            index,
            report["phase"],
            report["submitted_at_utc"],
            user_names.get(report["submitted_by"], report["submitted_by"]),
            ", ".join(report["damage_tags"]) or "(none)",
            ("+" + ", ".join(appeared)) if appeared else "",
            report["report_id"],
        ])
    return out + table(
        ["#", "phase", "logged at", "by", "tags on record", "new", "report"], rows
    )


def trust_ledger(score, label: str) -> list[str]:
    """Every point the score ever moved, with its cause. Recomputed from zero."""
    out = section(f"TRUST LEDGER - {label}")
    out += kv([("baseline", score.baseline)])
    if score.contributions:
        out.append("")
        out += table(
            ["seq", "signal", "delta", "running"],
            [[c.event_seq, c.signal, f"{c.delta:+d}", c.running_total] for c in score.contributions],
        )
    out.append("")
    out += kv([("final", f"{score.score}/1000 ({score.band})"), ("citation", score.citation)])
    return out


def event_tail(events: Sequence[Mapping[str, Any]], limit: int = 0) -> list[str]:
    shown = events[-limit:] if limit else events
    return table(
        ["seq", "clock (UTC)", "event", "key payload"],
        [
            [
                e["event_seq"], e["clock_utc"], e["event_type"],
                ", ".join(
                    f"{k}={e['payload'][k]}"
                    for k in sorted(e["payload"])
                    if k in ("item_id", "rental_id", "report_id", "tier", "signal",
                             "pin", "premium_cents", "settled_cents", "signal_id",
                             "resolution", "to_tier", "flag_id", "validation_result")
                )[:64],
            ]
            for e in shown
        ],
    )


def decision_citations(citations: Sequence[str]) -> list[str]:
    if not citations:
        return []
    return ["", "  WHY:"] + bullets(citations, marker=">", indent=4)
