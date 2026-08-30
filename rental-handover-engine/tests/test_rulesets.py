"""L0 — the rules themselves must be well formed before anything reads them."""
from __future__ import annotations

import subprocess
import sys

import pytest

from rhe.l0_rules.loader import RULESET_FILES, RulesetError, load_ruleset


def test_every_declared_file_loads(ruleset):
    assert len(ruleset.documents) == len(RULESET_FILES)
    for stem, version in ruleset.versions.items():
        assert isinstance(version, int) and version >= 1, stem


def test_loading_twice_produces_the_same_hash():
    assert load_ruleset().ruleset_hash == load_ruleset().ruleset_hash


def test_ruleset_is_immutable_at_runtime(ruleset):
    with pytest.raises(TypeError):
        ruleset.doc("tier_rules")["rows"] = []


def test_tier_rule_precedence_is_unique(ruleset):
    precedences = [r["precedence"] for r in ruleset.doc("tier_rules")["rows"]]
    assert len(set(precedences)) == len(precedences)


def test_no_catch_all_row_exists(ruleset):
    assert ruleset.doc("precedence")["decision_tables"]["allow_catch_all_row"] is False
    for row in ruleset.doc("tier_rules")["rows"]:
        assert row["when"], f"row {row['id']} is a catch-all"


def test_damage_taxonomy_is_internally_consistent(ruleset):
    tax = ruleset.doc("damage_taxonomy")
    components = {c["component_id"] for c in tax["components"]}
    tag_ids = {t["tag_id"] for t in tax["tags"]}
    for tag in tax["tags"]:
        assert tag["component"] in components
        assert tag["severity"] in tax["severity_scale"]
        assert tag["repair_cost_band"] in tax["repair_cost_bands"]
    assert set(tax["blocking_on_new_appearance"]) <= tag_ids
    for phase in tax["report_phases"].values():
        assert phase["chain_position"] in ("pre", "post")


def test_every_leaf_category_resolves_to_a_complete_attribute_set(ruleset):
    from rhe.l1_kernel.classify import attribute_domains, resolve_attributes

    tree = ruleset.doc("category_tree")
    parents = {n.get("parent") for n in tree["nodes"]}
    required = set(attribute_domains(ruleset))
    for node in tree["nodes"]:
        if node["id"] in parents:
            continue
        resolution = resolve_attributes(node["id"], ruleset)
        assert set(resolution.attributes) >= required, node["id"]


def test_every_transition_guard_has_an_implementation(ruleset):
    from rhe.l1_kernel.guards import GUARDS

    for machine in ruleset.doc("state_transitions")["machines"].values():
        for transition in machine["transitions"]:
            for guard in transition["guards"]:
                assert guard in GUARDS, f"guard {guard!r} has no implementation"


def test_insurance_table_is_reproducible(root):
    """The generated rate table must regenerate byte for byte."""
    path = root / "rhe" / "l0_rules" / "rulesets" / "insurance_rates.yaml"
    before = path.read_bytes()
    subprocess.run([sys.executable, str(root / "tools" / "gen_insurance_rates.py")],
                   check=True, capture_output=True)
    assert path.read_bytes() == before, "regenerating the rate table changed it"


def test_a_duplicate_precedence_is_rejected_at_load(tmp_path, root):
    import shutil

    source = root / "rhe" / "l0_rules" / "rulesets"
    shutil.copytree(source, tmp_path / "rulesets")
    target = tmp_path / "rulesets" / "tier_rules.yaml"
    target.write_text(target.read_text().replace("precedence: 100", "precedence: 90"))
    with pytest.raises(RulesetError, match="duplicate precedence"):
        load_ruleset(tmp_path / "rulesets")
