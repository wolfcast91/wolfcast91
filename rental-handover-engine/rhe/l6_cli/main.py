"""L6 — The command-line interface.

Read-only against projections, writes only by issuing commands, contains no
logic. Everything it prints comes from the ruleset or the log.

    rhe scenarios                    list the built-in scenarios
    rhe run <id|all>                 run one scenario, or all of them
    rhe classify <category>          classify a category and show the citation
    rhe classify --all               classify every category in the tree
    rhe tiers                        show the tier system and its choreography
    rhe prove                        run the classifier exhaustiveness proof
    rhe golden [--update]            compare (or refresh) the golden files
    rhe verify-determinism           run every scenario twice, in-process
    rhe rulesets                     list every ruleset file, version and hash
"""
from __future__ import annotations

import argparse
import pathlib
import sys

from rhe.l0_rules.loader import RULESET_FILES, load_ruleset
from rhe.l1_kernel import classify
from rhe.l6_cli import render
from sim import runner


def _scenario_path(scenario_id: str) -> pathlib.Path:
    for path in runner.list_scenarios():
        if path.stem == scenario_id or path.stem.split("_", 1)[1] == scenario_id:
            return path
    raise SystemExit(
        f"no such scenario: {scenario_id!r}\n"
        f"available: {', '.join(p.stem for p in runner.list_scenarios())}"
    )


def cmd_scenarios(args) -> int:
    import yaml
    print("\n".join(render.banner("SCENARIOS")))
    rows = []
    for path in runner.list_scenarios():
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        steps = sum(1 for s in doc["script"] if "cmd" in s)
        rows.append([path.stem, doc["id"], steps, doc["subtitle"]])
    print("\n".join(render.table(["file", "id", "cmds", "about"], rows)))
    print(f"\n  run one with:  python3 -m rhe.l6_cli.main run {runner.list_scenarios()[0].stem}")
    print("  run them all:  python3 -m rhe.l6_cli.main run all")
    return 0


def cmd_run(args) -> int:
    if args.scenario == "all":
        paths = runner.list_scenarios()
    else:
        paths = [_scenario_path(args.scenario)]
    ruleset = load_ruleset()
    for path in paths:
        sys.stdout.write(runner.run_scenario(path, ruleset).output)
        if len(paths) > 1:
            sys.stdout.write("\n\n")
    return 0


def cmd_classify(args) -> int:
    ruleset = load_ruleset()
    tree = ruleset.doc("category_tree")
    parents = {n.get("parent") for n in tree["nodes"]}
    leaves = [n["id"] for n in tree["nodes"] if n["id"] not in parents]

    targets = sorted(leaves) if args.all else [args.category]
    if args.all:
        print("\n".join(render.banner("CLASSIFICATION OF EVERY LEAF CATEGORY")))
        rows = []
        for category in targets:
            decision, _ = classify.classify_category(category, ruleset)
            rows.append([category, f"T{decision.tier}",
                         classify.tier_name(decision.tier, ruleset), decision.row_id,
                         decision.precedence, ",".join(decision.all_matching_rows)])
        print("\n".join(render.table(
            ["category", "tier", "mechanism", "row", "prec", "all rows that matched"], rows)))
        return 0

    decision, resolution = classify.classify_category(args.category, ruleset)
    print("\n".join(render.banner(
        f"{args.category} -> TIER {decision.tier}: {classify.tier_name(decision.tier, ruleset)}")))
    print("\n".join(render.kv([
        ("citation", decision.citation),
        ("winning row", f"{decision.row_id} (precedence {decision.precedence})"),
        ("rows that matched", ", ".join(decision.all_matching_rows)),
        ("rationale", decision.rationale),
        ("category path", " > ".join(resolution.category_path)),
    ])))
    print("\n".join(render.section("ATTRIBUTES AND WHERE EACH CAME FROM")))
    print("\n".join(render.table(
        ["attribute", "value", "source"],
        [[k, v, resolution.sources[k]] for k, v in sorted(decision.attributes.items())])))
    print("\n".join(render.handover_plan(
        decision.tier, classify.tier_name(decision.tier, ruleset),
        classify.handover_steps(decision.tier, ruleset), decision.citation)))
    return 0


def cmd_tiers(args) -> int:
    ruleset = load_ruleset()
    print("\n".join(render.banner("THE HANDOVER TIER SYSTEM", "grouped by mechanism, not by item type")))
    for tier in sorted(ruleset.doc("handover_steps")["tiers"]):
        spec = ruleset.doc("handover_steps")["tiers"][tier]
        print("\n".join(render.section(f"TIER {tier} - {spec['name']}")))
        print("\n".join(render.kv([
            ("human contact", spec["human_contact"]),
            ("photo slots", ", ".join(spec["photo_slots"])),
        ])))
        print("\n".join(render.table(
            ["#", "actor", "step", "logs"],
            [[s["step_index"], s["actor"], s["label"], ", ".join(s["logs"])]
             for s in classify.handover_steps(tier, ruleset)])))
    print("\n".join(render.section("THE RULE ROWS THAT ASSIGN THEM")))
    print("\n".join(render.table(
        ["row", "prec", "tier", "matches when"],
        [[r["id"], r["precedence"], r["tier"],
          "; ".join(f"{k} in {list(v)}" for k, v in sorted(r["when"].items()))]
         for r in sorted(ruleset.doc("tier_rules")["rows"], key=lambda r: r["precedence"])])))
    return 0


def cmd_prove(args) -> int:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))
    import prove_exhaustiveness
    return prove_exhaustiveness.main()


def cmd_golden(args) -> int:
    ruleset = load_ruleset()
    runner.GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for path in runner.list_scenarios():
        golden = runner.GOLDEN_DIR / f"{path.stem}.txt"
        produced = runner.run_scenario(path, ruleset).output
        if args.update:
            golden.write_text(produced, encoding="utf-8")
            print(f"  wrote {golden.relative_to(runner.SIM_DIR.parent)} ({len(produced)} bytes)")
            continue
        if not golden.is_file():
            failures.append(f"{path.stem}: no golden file (run with --update)")
        elif golden.read_text(encoding="utf-8") != produced:
            failures.append(f"{path.stem}: output differs from its golden file")
        else:
            print(f"  OK  {path.stem}")
    if failures:
        print("\n".join(["", "GOLDEN COMPARISON FAILED:"] + render.bullets(failures)))
        return 1
    if not args.update:
        print(f"\n  {len(runner.list_scenarios())} scenario(s) match their golden files byte for byte")
    return 0


def cmd_verify_determinism(args) -> int:
    """Run every scenario twice, in one process, and compare the bytes."""
    ruleset = load_ruleset()
    print("\n".join(render.banner("DETERMINISM VERIFICATION", "every scenario, twice, in-process")))
    rows, ok = [], True
    for path in runner.list_scenarios():
        first = runner.run_scenario(path, ruleset)
        second = runner.run_scenario(path, ruleset)
        same_output = first.output == second.output
        same_log = first.engine.log.log_hash == second.engine.log.log_hash
        ok &= same_output and same_log
        rows.append([path.stem, len(first.output), first.engine.log.log_hash[:16],
                     "YES" if same_output else "NO", "YES" if same_log else "NO"])
    print("\n".join(render.table(
        ["scenario", "bytes", "log hash", "output identical", "log identical"], rows)))
    print("")
    print("  ALL SCENARIOS DETERMINISTIC" if ok else "  DETERMINISM VIOLATED")
    return 0 if ok else 1


def cmd_rulesets(args) -> int:
    ruleset = load_ruleset()
    print("\n".join(render.banner("L0 RULESETS", f"composite hash {ruleset.ruleset_hash}")))
    print("\n".join(render.table(
        ["file", "version", "sha-256 of the parsed document"],
        [[f, ruleset.versions[pathlib.Path(f).stem], ruleset.file_hashes[pathlib.Path(f).stem]]
         for f in RULESET_FILES])))
    print("\n  Every decision this system makes is stamped with the composite hash above.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rhe", description="Rental Handover Engine - deterministic, local, no AI in the runtime path.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scenarios", help="list the built-in scenarios").set_defaults(fn=cmd_scenarios)

    run = sub.add_parser("run", help="run a scenario (or 'all')")
    run.add_argument("scenario")
    run.set_defaults(fn=cmd_run)

    classify_parser = sub.add_parser("classify", help="classify a category and explain the result")
    classify_parser.add_argument("category", nargs="?", default=None)
    classify_parser.add_argument("--all", action="store_true", help="classify every leaf category")
    classify_parser.set_defaults(fn=cmd_classify)

    sub.add_parser("tiers", help="show the tier system and its choreography").set_defaults(fn=cmd_tiers)
    sub.add_parser("prove", help="run the classifier exhaustiveness proof").set_defaults(fn=cmd_prove)

    golden = sub.add_parser("golden", help="compare scenario output against the golden files")
    golden.add_argument("--update", action="store_true", help="rewrite the golden files")
    golden.set_defaults(fn=cmd_golden)

    sub.add_parser("verify-determinism", help="run every scenario twice and diff the bytes").set_defaults(
        fn=cmd_verify_determinism)
    sub.add_parser("rulesets", help="list every ruleset file, its version and its hash").set_defaults(
        fn=cmd_rulesets)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "classify" and not args.all and not args.category:
        raise SystemExit("classify needs a category id, or --all")
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
