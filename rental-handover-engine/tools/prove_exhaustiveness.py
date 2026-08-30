#!/usr/bin/env python3
"""Exhaustiveness proof for tier_rules.yaml (charter rule 6: total functions).

Enumerates the COMPLETE attribute cross-product and asserts three things:

  1. NO GAPS      -- every cell is matched by at least one rule row, with no
                     catch-all row in the table to make that trivially true.
  2. NO AMBIGUITY -- where several rows match a cell, the winner is decided by a
                     unique integer precedence, never by evaluation order.
  3. NO DEAD ROWS -- every row wins at least one cell. A row that never wins is
                     either shadowed by a higher-precedence row or wrong, and
                     either way it is a lie in a file an underwriter will read.

Writes the full decision table to artifacts/tier_decision_table.tsv, which is
committed and byte-compared by the test suite.

Exit code 0 on proof, 1 on failure.
"""
from __future__ import annotations

import itertools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rhe.l0_rules.loader import canonical_attr_value, load_ruleset  # noqa: E402
from rhe.l1_kernel.classify import attribute_domains, classify_tier  # noqa: E402

ARTIFACT = pathlib.Path(__file__).resolve().parent.parent / "artifacts" / "tier_decision_table.tsv"


def enumerate_cells(ruleset):
    """Every point in the classifier's input space, in a fixed, sorted order."""
    domains = attribute_domains(ruleset)
    names = sorted(domains)                       # ordered iteration, charter rule 4
    for combo in itertools.product(*(domains[n] for n in names)):
        yield dict(zip(names, combo))


def main() -> int:
    ruleset = load_ruleset()
    doc = ruleset.doc("tier_rules")
    rows = sorted(doc["rows"], key=lambda r: r["precedence"])
    domains = attribute_domains(ruleset)
    names = sorted(domains)

    expected = 1
    for n in names:
        expected *= len(domains[n])

    gaps: list[dict] = []
    winners: dict[str, int] = {r["id"]: 0 for r in rows}
    tier_counts: dict[int, int] = {}
    overlapping_cells = 0
    table_lines = ["\t".join(names + ["tier", "winning_row", "precedence", "all_matching_rows"])]

    for cell in enumerate_cells(ruleset):
        try:
            decision = classify_tier(cell, ruleset)
        except Exception:
            gaps.append(cell)
            continue
        winners[decision.row_id] += 1
        tier_counts[decision.tier] = tier_counts.get(decision.tier, 0) + 1
        if len(decision.all_matching_rows) > 1:
            overlapping_cells += 1
        table_lines.append(
            "\t".join(
                [cell[n] for n in names]
                + [str(decision.tier), decision.row_id, str(decision.precedence),
                   ",".join(decision.all_matching_rows)]
            )
        )

    cells = len(table_lines) - 1
    precedences = [r["precedence"] for r in rows]
    unique_precedence = len(set(precedences)) == len(precedences)
    catch_all_rows = [r["id"] for r in rows if not r.get("when")]
    dead_rows = sorted(rid for rid, n in winners.items() if n == 0)

    print(f"attribute space : {' x '.join(f'{n}({len(domains[n])})' for n in names)}")
    print(f"expected cells  : {expected}")
    print(f"resolved cells  : {cells}")
    print(f"gaps            : {len(gaps)}")
    print(f"catch-all rows  : {catch_all_rows or 'none'}")
    print(f"unique precedence: {unique_precedence}")
    print(f"cells matched by >1 row (resolved by precedence): {overlapping_cells}")
    print(f"dead rows       : {dead_rows or 'none'}")
    print("cells won per row:")
    for r in rows:
        print(f"  {r['id']} (prec {r['precedence']:>3}) -> tier {r['tier']}: {winners[r['id']]:>5} cells")
    print("cells per tier:")
    for tier in sorted(tier_counts):
        print(f"  tier {tier}: {tier_counts[tier]:>5} cells")

    ok = True
    if gaps:
        ok = False
        print(f"\nFAIL: {len(gaps)} cell(s) matched no rule row, e.g. {gaps[0]}")
    if cells != expected:
        ok = False
        print(f"\nFAIL: resolved {cells} cells but the space has {expected}")
    if not unique_precedence:
        ok = False
        print("\nFAIL: precedence values are not unique -- ties would fall to file order")
    if catch_all_rows:
        ok = False
        print(f"\nFAIL: catch-all row(s) present: {catch_all_rows}")
    if dead_rows:
        ok = False
        print(f"\nFAIL: dead row(s) that never win a cell: {dead_rows}")

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text("\n".join(table_lines) + "\n", encoding="utf-8")
    print(f"\nwrote {ARTIFACT.relative_to(ARTIFACT.parent.parent)} ({cells} rows)")

    print("\nPROOF HOLDS" if ok else "\nPROOF FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
