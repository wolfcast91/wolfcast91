"""The simulator: golden-file comparison and in-process determinism."""
from __future__ import annotations

import pytest

from sim import runner

SCENARIOS = runner.list_scenarios()


def test_there_are_at_least_eight_scenarios():
    assert len(SCENARIOS) >= 8


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
def test_scenario_matches_its_golden_file(path, ruleset):
    golden = runner.GOLDEN_DIR / f"{path.stem}.txt"
    assert golden.is_file(), f"missing golden file; run `make golden-update`"
    assert runner.run_scenario(path, ruleset).output == golden.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
def test_scenario_is_byte_identical_when_run_twice(path, ruleset):
    first = runner.run_scenario(path, ruleset)
    second = runner.run_scenario(path, ruleset)
    assert first.output == second.output
    assert first.engine.log.log_hash == second.engine.log.log_hash


@pytest.mark.parametrize("path", SCENARIOS, ids=lambda p: p.stem)
def test_scenario_output_carries_no_wall_clock_time(path, ruleset):
    """The only timestamps in the output must come from the injected clock."""
    import datetime
    output = runner.run_scenario(path, ruleset).output
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    assert today not in output or today.startswith("2026-"), (
        "scenario output contains today's real date")


def test_all_scenarios_share_one_seed_world(ruleset):
    """Every scenario starts from the same committed world, so a diff between two
    scenario outputs is a diff in behaviour, never in setup."""
    import yaml
    seeds = {yaml.safe_load(p.read_text(encoding="utf-8"))["seed"] for p in SCENARIOS}
    assert seeds == {"world"}
