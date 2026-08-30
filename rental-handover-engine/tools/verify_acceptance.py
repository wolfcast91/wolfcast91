#!/usr/bin/env python3
"""The acceptance bar from the determinism charter, run literally.

    1. Run the full simulator suite twice into two separate output directories
       and diff them. Zero bytes of difference, or this fails.
    2. Delete the projection database, replay the event log from zero, and
       compare the rebuilt state against the original. Identical, or this fails.

Both must hold. The build is not done until they do.
"""
from __future__ import annotations

import filecmp
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rhe.l0_rules.loader import load_ruleset                    # noqa: E402
from rhe.l3_projections.sqlite_store import SqliteProjectionStore  # noqa: E402
from rhe.l3_projections.state import fold                       # noqa: E402
from rhe.l6_cli import render                                   # noqa: E402
from sim import runner                                          # noqa: E402


def run_suite_into(directory: pathlib.Path, ruleset) -> dict[str, str]:
    """Run every scenario, writing output and event log to `directory`."""
    directory.mkdir(parents=True, exist_ok=True)
    log_hashes = {}
    for path in runner.list_scenarios():
        result = runner.run_scenario(path, ruleset)
        (directory / f"{path.stem}.txt").write_text(result.output, encoding="utf-8")
        result.engine.log.write_jsonl(directory / f"{path.stem}.jsonl")
        log_hashes[path.stem] = result.engine.log.log_hash
    return log_hashes


def check_double_run(ruleset) -> bool:
    print("\n".join(render.section("1. THE SUITE, RUN TWICE, DIFFED BYTE FOR BYTE")))
    with tempfile.TemporaryDirectory() as tmp:
        base = pathlib.Path(tmp)
        first, second = base / "run_a", base / "run_b"
        hashes_a = run_suite_into(first, ruleset)
        hashes_b = run_suite_into(second, ruleset)

        names = sorted(p.name for p in first.iterdir())
        match, mismatch, errors = filecmp.cmpfiles(first, second, names, shallow=False)
        rows = [[name, "IDENTICAL" if name in match else "DIFFERS",
                 first.joinpath(name).stat().st_size] for name in names]
        print("\n".join(render.table(["file", "result", "bytes"], rows)))
        ok = not mismatch and not errors and hashes_a == hashes_b
        print("")
        print(f"  {len(match)}/{len(names)} files identical; "
              f"{len(mismatch)} differ, {len(errors)} unreadable")
        print(f"  event log hashes identical: {'YES' if hashes_a == hashes_b else 'NO'}")
        return ok


def check_replay_from_zero(ruleset) -> bool:
    print("\n".join(render.section("2. DELETE THE DATABASE, REPLAY THE LOG FROM ZERO")))
    ok = True
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for path in runner.list_scenarios():
            result = runner.run_scenario(path, ruleset)
            events = result.engine.log.as_dicts()
            database = pathlib.Path(tmp) / f"{path.stem}.sqlite3"

            live = SqliteProjectionStore(database)
            live.rebuild(result.engine.state, events, ruleset)
            before = live.fingerprint()
            live.close()

            database.unlink()                       # the cache is genuinely gone
            assert not database.exists()

            rebuilt = SqliteProjectionStore(database)
            rebuilt.rebuild(fold(events, ruleset), events, ruleset)
            after = rebuilt.fingerprint()
            rebuilt.close()

            identical = before == after
            ok &= identical
            rows.append([path.stem, len(events), before[:16], after[:16],
                         "IDENTICAL" if identical else "DIVERGED"])
    print("\n".join(render.table(
        ["scenario", "events", "before", "after replay", "result"], rows)))
    return ok


def main() -> int:
    ruleset = load_ruleset()
    print("\n".join(render.banner(
        "ACCEPTANCE BAR", f"ruleset {ruleset.ruleset_hash}")))
    double_run = check_double_run(ruleset)
    replay = check_replay_from_zero(ruleset)

    print("\n".join(render.section("VERDICT")))
    print("\n".join(render.kv([
        ("suite runs twice with zero byte difference", "PASS" if double_run else "FAIL"),
        ("state survives deleting and replaying", "PASS" if replay else "FAIL"),
    ])))
    passed = double_run and replay
    print("")
    print("  ACCEPTANCE BAR MET" if passed else "  ACCEPTANCE BAR NOT MET")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
