"""L1 — the tier classifier: total, unique, and stable against its artifacts."""
from __future__ import annotations

import itertools
import subprocess
import sys

import pytest
import yaml

from rhe.l1_kernel.classify import (
    ClassificationError, attribute_domains, classify_category, classify_tier,
    handover_steps, resolve_attributes,
)


def _all_cells(ruleset):
    domains = attribute_domains(ruleset)
    names = sorted(domains)
    for combo in itertools.product(*(domains[n] for n in names)):
        yield dict(zip(names, combo))


def test_classifier_is_total_over_the_whole_input_space(ruleset):
    """Every cell of the cross-product resolves. No gaps, no default case."""
    count = 0
    for cell in _all_cells(ruleset):
        decision = classify_tier(cell, ruleset)
        assert decision.tier in (1, 2, 3, 4, 5)
        count += 1
    expected = 1
    for values in attribute_domains(ruleset).values():
        expected *= len(values)
    assert count == expected == 1152


def test_every_overlap_is_resolved_by_unique_precedence(ruleset):
    """Rows may overlap; the winner must always be decided by precedence."""
    rows = {r["id"]: r for r in ruleset.doc("tier_rules")["rows"]}
    for cell in _all_cells(ruleset):
        decision = classify_tier(cell, ruleset)
        matching = decision.all_matching_rows
        assert decision.row_id == min(matching, key=lambda rid: rows[rid]["precedence"])


def test_no_rule_row_is_dead(ruleset):
    won = {classify_tier(cell, ruleset).row_id for cell in _all_cells(ruleset)}
    assert won == {r["id"] for r in ruleset.doc("tier_rules")["rows"]}


def test_classification_is_repeatable(ruleset):
    for _ in range(20):
        assert classify_category("sewing_machine", ruleset)[0].tier == 3


def test_exhaustiveness_proof_script_passes(root):
    result = subprocess.run([sys.executable, str(root / "tools" / "prove_exhaustiveness.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PROOF HOLDS" in result.stdout


def test_decision_table_artifact_is_current(root):
    """The committed cross-product artifact must match what the rules produce."""
    artifact = root / "artifacts" / "tier_decision_table.tsv"
    before = artifact.read_bytes()
    subprocess.run([sys.executable, str(root / "tools" / "prove_exhaustiveness.py")],
                   check=True, capture_output=True)
    assert artifact.read_bytes() == before


def test_item_bench_artifact_is_current(root):
    artifact = root / "artifacts" / "item_bench.txt"
    before = artifact.read_bytes()
    result = subprocess.run([sys.executable, str(root / "tools" / "render_item_bench.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    assert artifact.read_bytes() == before


def test_every_bench_item_lands_on_its_expected_tier(ruleset, root):
    bench = yaml.safe_load((root / "sim" / "seed" / "item_bench.yaml").read_text())
    assert len(bench["items"]) >= 25
    for entry in bench["items"]:
        decision, _ = classify_category(entry["category"], ruleset, entry.get("overrides", {}))
        assert decision.tier == entry["expect_tier"], entry["ref"]


def test_owner_may_not_override_a_regulatory_attribute(ruleset):
    with pytest.raises(ClassificationError, match="never be overridden"):
        classify_category("mobile_crane", ruleset, {"requires_license": False})


def test_unknown_category_is_rejected(ruleset):
    with pytest.raises(ClassificationError, match="unknown category"):
        resolve_attributes("teleporter", ruleset)


def test_incomplete_attribute_set_is_rejected(ruleset):
    with pytest.raises(ClassificationError, match="incomplete attribute set"):
        classify_tier({"enclosable": "true"}, ruleset)


def test_out_of_domain_attribute_value_is_rejected(ruleset):
    with pytest.raises(ClassificationError, match="outside its declared domain"):
        classify_category("drill_driver", ruleset, {"value_band": "astronomical"})


def test_every_tier_has_ordered_handover_steps(ruleset):
    for tier in (1, 2, 3, 4, 5):
        steps = handover_steps(tier, ruleset)
        assert [s["step_index"] for s in steps] == sorted(s["step_index"] for s in steps)
        assert all(s["logs"] for s in steps)
