#!/usr/bin/env python3
"""Render the item bench to artifacts/item_bench.txt (a golden artifact).

The bench is the human-readable half of the classifier's proof: the
cross-product proof shows the table is total, and this shows it is SENSIBLE.
"""
from __future__ import annotations

import pathlib
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rhe.l0_rules.loader import load_ruleset            # noqa: E402
from rhe.l1_kernel import classify                      # noqa: E402
from rhe.l6_cli import render                           # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BENCH = ROOT / "sim" / "seed" / "item_bench.yaml"
ARTIFACT = ROOT / "artifacts" / "item_bench.txt"


def build() -> tuple[str, list[str]]:
    ruleset = load_ruleset()
    bench = yaml.safe_load(BENCH.read_text(encoding="utf-8"))
    lines = render.banner(
        "ITEM CLASSIFICATION BENCH",
        f"{len(bench['items'])} items, bench v{bench['bench_version']}, ruleset {ruleset.short}")
    rows, plans, mismatches = [], {}, []
    for entry in bench["items"]:
        decision, _ = classify.classify_category(
            entry["category"], ruleset, entry.get("overrides", {}))
        if decision.tier != entry["expect_tier"]:
            mismatches.append(
                f"{entry['ref']}: expected T{entry['expect_tier']}, got T{decision.tier} "
                f"via {decision.row_id}")
        rows.append([
            entry["ref"], entry["category"], f"T{decision.tier}",
            classify.tier_name(decision.tier, ruleset), decision.row_id,
            "OK" if decision.tier == entry["expect_tier"] else "MISMATCH",
        ])
        plans.setdefault(decision.tier, None)
    lines += render.table(
        ["item", "category", "tier", "mechanism", "row", "vs expected"], rows)

    lines += render.section("WHY - the ambiguous ones in the author's own words")
    for entry in bench["items"]:
        if entry["note"].startswith("AMBIGUOUS"):
            lines.append(f"  {entry['ref']}")
            lines.append(f"      {' '.join(entry['note'].split())}")

    lines += render.section("HANDOVER STEPS PER TIER REACHED BY THIS BENCH")
    for tier in sorted(plans):
        lines += render.handover_plan(
            tier, classify.tier_name(tier, ruleset),
            classify.handover_steps(tier, ruleset),
            ruleset.citation("handover_steps"))
    return "\n".join(lines) + "\n", mismatches


if __name__ == "__main__":
    text, mismatches = build()
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text, encoding="utf-8")
    print(f"wrote {ARTIFACT.relative_to(ROOT)}")
    for m in mismatches:
        print("  MISMATCH:", m)
    raise SystemExit(1 if mismatches else 0)
