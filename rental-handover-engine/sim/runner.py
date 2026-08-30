"""The scenario simulator. The primary deliverable and the fun part.

A scenario is a committed data file: a seed world, a FixedClock start time, and
an ordered script of commands. The runner applies the script and renders the
whole handover -- assigned tier, every step in order, every fact logged, the
resulting condition chain, and any insurance quote or purchase offer that fired.

Nothing here decides anything. It resolves references, issues commands, and
formats what came back. That is why running it twice produces identical bytes.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import Any, Mapping

import yaml

from rhe.l0_rules.loader import Ruleset, load_ruleset
from rhe.l1_kernel import classify
from rhe.l1_kernel.trust import compute_trust
from rhe.l3_projections.sqlite_store import SqliteProjectionStore
from rhe.l3_projections.state import fold
from rhe.l4_commands import commands as cmd
from rhe.l1_kernel.transitions import IllegalTransition
from rhe.l4_commands.engine import CommandRejected, Engine
from rhe.l5_adapters.clock import FixedClock, utc_to_epoch
from rhe.l6_cli import render

SIM_DIR = pathlib.Path(__file__).resolve().parent
SEED_DIR = SIM_DIR / "seed"
SCENARIO_DIR = SIM_DIR / "scenarios"
GOLDEN_DIR = SIM_DIR / "golden"

COMMAND_TYPES = {
    name: getattr(cmd, name)
    for name in dir(cmd)
    if isinstance(getattr(cmd, name), type)
    and issubclass(getattr(cmd, name), cmd.Command)
    and getattr(cmd, name) is not cmd.Command
}


class ScenarioError(Exception):
    """A scenario file is malformed or references something that does not exist."""


@dataclass
class ScenarioRun:
    """Everything one scenario produced. `lines` is what gets golden-compared."""

    scenario_id: str
    title: str
    lines: list[str] = field(default_factory=list)
    engine: Engine | None = None

    @property
    def output(self) -> str:
        return "\n".join(self.lines) + "\n"


class ScenarioRunner:
    """Loads a seed world and replays a scenario script against a fresh Engine."""

    def __init__(self, scenario_path: pathlib.Path, ruleset: Ruleset | None = None) -> None:
        self.path = scenario_path
        self.scenario = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
        self.ruleset = ruleset or load_ruleset()
        self.refs: dict[str, str] = {}          # "@name" -> real content-hash id
        self.item_refs: dict[str, str] = {}
        self.out: list[str] = []

    # -- helpers -----------------------------------------------------------
    def _emit(self, lines: list[str] | str) -> None:
        self.out.extend([lines] if isinstance(lines, str) else lines)

    def _resolve(self, value: Any) -> Any:
        """`@ref` -> the real id. Anything else passes through untouched."""
        if isinstance(value, str) and value.startswith("@"):
            name = value[1:]
            if name in self.refs:
                return self.refs[name]
            raise ScenarioError(f"unresolved reference @{name} in {self.path.name}")
        if isinstance(value, dict):
            return {k: self._resolve(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve(v) for v in value]
        return value

    def _user_names(self) -> dict[str, str]:
        return {u["user_id"]: u["handle"] for u in self.engine.state.users.values()}

    # -- seed --------------------------------------------------------------
    def _load_seed(self, engine: Engine) -> None:
        seed = yaml.safe_load((SEED_DIR / f"{self.scenario['seed']}.yaml").read_text(encoding="utf-8"))
        for user in seed["users"]:
            engine.execute(cmd.RegisterUser(
                handle=user["handle"], display_name=user["display_name"],
                account_type=user["account_type"], verify_identity=user["verify_identity"],
            ))
            self.refs[user["handle"]] = user["handle"]
        node_ids: dict[str, str] = {}
        for node in seed["partner_nodes"]:
            result = engine.execute(cmd.RegisterPartnerNode(
                operator_name=node["operator_name"], node_type=node["node_type"],
                lat_micro=node["lat_micro"], lon_micro=node["lon_micro"],
                intake_fee_cents=node["intake_fee_cents"],
            ))
            node_id = engine.log.events[-1].payload["partner_node_id"]
            node_ids[node["ref"]] = node_id
            self.refs[node["ref"]] = node_id
        for location in seed["locations"]:
            engine.execute(cmd.RegisterLocation(
                owner_handle=location["owner"], label=location["label"],
                access_type=location["access_type"],
                lat_micro=location["lat_micro"], lon_micro=location["lon_micro"],
                spatial_instruction=location.get("spatial_instruction"),
                landmark_photo_slot=location.get("landmark_photo_slot"),
                partner_node_id=node_ids.get(location.get("partner_node", "")),
            ))
        location_labels = {loc["ref"]: loc["label"] for loc in seed["locations"]}
        for item in seed["items"]:
            engine.execute(cmd.ListItem(
                owner_handle=item["owner"], category_id=item["category"],
                model_name=item["model_name"], serial_number=item["serial"],
                replacement_value_cents=item["value_cents"],
                purchase_price_cents=item["price_cents"],
                day_rate_cents=item["day_rate_cents"],
                location_label=location_labels[item["location"]],
                accessory_manifest=tuple(item["accessories"]),
                attribute_overrides=item.get("overrides", {}),
            ))
            item_id = engine.log.events[-2].payload["item_id"]   # ItemListed, then TierAssigned
            self.refs[item["ref"]] = item_id
            self.item_refs[item["ref"]] = item_id

    # -- script ------------------------------------------------------------
    def _bind_new(self, name: str, before: set[str], collection: Mapping[str, Any]) -> None:
        created = sorted(set(collection) - before)
        if not created:
            raise ScenarioError(f"step declared `as: {name}` but created nothing")
        self.refs[name] = created[0]

    def _run_command(self, step: Mapping[str, Any], index: int, total: int) -> None:
        name = step["cmd"]
        if name not in COMMAND_TYPES:
            raise ScenarioError(f"unknown command {name!r}; known: {sorted(COMMAND_TYPES)}")
        args = {k: self._resolve(v) for k, v in (step.get("args") or {}).items()}
        for key in ("damage_tags", "tags", "contested_tags", "accessory_manifest", "countersigned_by_handles"):
            if key in args and isinstance(args[key], list):
                args[key] = tuple(args[key])

        rentals_before = set(self.engine.state.rentals)
        offers_before = set(self.engine.state.purchase_offers)
        disputes_before = set(self.engine.state.disputes)

        self._emit(render.step_header(
            index, total, step.get("actor", "-"), step.get("label", name), self.engine.clock.now_utc()))

        expect_rejection = step.get("expect_rejection", False)
        try:
            result = self.engine.execute(COMMAND_TYPES[name](**args))
        except (CommandRejected, IllegalTransition) as exc:
            # Both are typed refusals: one from validation, one from a state
            # machine guard. Neither is ever a silent no-op, which is exactly
            # what `expect_rejection` steps exist to demonstrate.
            if not expect_rejection:
                raise
            self._emit(render.bullets([f"REJECTED (as the scenario expects): {exc}"], marker="!", indent=8))
            return
        if expect_rejection:
            raise ScenarioError(f"step {index} expected a rejection from {name} and got none")

        self._emit(render.bullets(result.notes, marker="-", indent=8))
        if result.events:
            self._emit(render.bullets(
                [f"logged: {', '.join(e.event_type for e in result.events)}"], marker="+", indent=8))
        if result.decisions:
            self._emit(render.bullets(result.decisions, marker=">", indent=8))

        if "as" in step:
            binding = step["as"]
            if name in ("ReserveItem",):
                self._bind_new(binding, rentals_before, self.engine.state.rentals)
            elif name in ("DetectPurchaseOpportunity",):
                self._bind_new(binding, offers_before, self.engine.state.purchase_offers)
            elif name in ("OpenDispute",):
                self._bind_new(binding, disputes_before, self.engine.state.disputes)
            else:
                raise ScenarioError(f"command {name} does not create a bindable entity")

    def _show(self, what: str, step: Mapping[str, Any]) -> None:
        state = self.engine.state
        if what == "plan":
            item_id = self._resolve(step["item"])
            item = state.items[item_id]
            tier = item["effective_tier"]
            self._emit(render.handover_plan(
                tier, classify.tier_name(tier, self.ruleset),
                classify.handover_steps(tier, self.ruleset), item["tier_citation"]))
        elif what == "item":
            item_id = self._resolve(step["item"])
            item = state.items[item_id]
            self._emit(render.section(f"ITEM - {item['model_name']}"))
            self._emit(render.kv([
                ("item_id", item["item_id"]),
                ("owner", self._user_names().get(item["owner_id"], item["owner_id"])),
                ("category", item["category_id"]),
                ("state", item["state"]),
                ("classified tier", f"{item['classified_tier']} (row {item['tier_row_id']})"),
                ("effective tier", f"{item['effective_tier']}" + (" [GRADUATED]" if item["graduated"] else "")),
                ("replacement value", render.cents(item["replacement_value_cents"])),
                ("purchase price", render.cents(item["purchase_price_cents"])),
                ("day rate", render.cents(item["day_rate_cents"])),
                ("attributes", ", ".join(f"{k}={v}" for k, v in sorted(item["attributes"].items()))),
                ("clean handovers", item["clean_handovers_consecutive"]),
                ("item trust", state.trust_of("item", item_id)),
                ("citation", item["tier_citation"]),
            ]))
        elif what == "chain":
            self._emit(render.condition_chain(
                state.chain_for(self._resolve(step["item"])), self._user_names()))
        elif what == "trust":
            handle = step["user"]
            user = next(u for u in state.users.values() if u["handle"] == handle)
            score = compute_trust("user", user["user_id"], self.engine.log.as_dicts(), self.ruleset)
            self._emit(render.trust_ledger(score, f"{user['display_name']} ({handle})"))
        elif what == "item_trust":
            item_id = self._resolve(step["item"])
            score = compute_trust("item", item_id, self.engine.log.as_dicts(), self.ruleset)
            self._emit(render.trust_ledger(score, state.items[item_id]["model_name"]))
        elif what == "rental":
            rental = state.rentals[self._resolve(step["rental"])]
            self._emit(render.section("RENTAL"))
            self._emit(render.kv([
                ("rental_id", rental["rental_id"]),
                ("state", rental["state"]),
                ("tier", rental["tier"]),
                ("window", f"{rental['window_start_utc']} -> {rental['window_end_utc']}"),
                ("rent", render.cents(rental["rent_cents"])),
                ("premium", render.cents(rental["quoted_premium_cents"])),
                ("deposit", render.cents(rental["deposit_cents"])),
                ("coverage", rental.get("coverage_tier")),
                ("insurance", rental["insurance_status"]),
                ("policy", rental.get("policy_ref")),
                ("settled", render.cents(rental["settled_cents"])),
            ]))
        elif what == "offers":
            self._emit(render.section("PURCHASE OPPORTUNITIES"))
            offers = sorted(state.purchase_offers.values(), key=lambda o: (o["signal_rank"], o["item_id"]))
            if not offers:
                self._emit("  (none)")
            for offer in offers:
                self._emit(render.kv([
                    ("offer", f"{offer['offer_id']} [{offer['state']}]"),
                    ("signal", f"{offer['signal_id']} (rank {offer['signal_rank']})"),
                    ("headline", offer["headline"]),
                    ("evidence", ", ".join(f"{k}={v}" for k, v in sorted(offer["evidence"].items()))),
                    ("price", render.cents(offer["purchase_price_cents"])),
                    ("rent paid so far", render.cents(offer["cumulative_rental_cents"])),
                    ("finance principal", render.cents(offer["financing_principal_cents"])),
                    ("instalments", ", ".join(
                        f"{k}x {render.cents(v)}" for k, v in sorted(
                            (offer["financing_terms"] or {}).items(), key=lambda p: int(p[0])))),
                    ("eligible", offer["purchase_conversion_eligible"]),
                    ("citation", offer["citation"]),
                ]))
                self._emit("")
        elif what == "inventory":
            handle = step["owner"]
            owner = next(u for u in state.users.values() if u["handle"] == handle)
            self._emit(render.section(f"INVENTORY - {owner['display_name']}"))
            self._emit(render.table(
                ["item", "category", "tier", "state", "value", "clean runs", "trust"],
                [[i["model_name"], i["category_id"],
                  f"T{i['effective_tier']}" + ("*" if i["graduated"] else ""),
                  i["state"], render.cents(i["replacement_value_cents"]),
                  i["clean_handovers_consecutive"], state.trust_of("item", i["item_id"])]
                 for i in state.inventory_of(owner["user_id"])]))
        elif what == "risk_flags":
            self._emit(render.section("RISK FLAGS"))
            self._emit(render.table(
                ["seq", "subject", "flag", "rule that fired", "severity"],
                [[f["event_seq"], self._user_names().get(f["subject_id"], f["subject_id"]),
                  f["flag_id"], f["rule"], f["severity"]]
                 for f in sorted(state.risk_flags, key=lambda f: (f["event_seq"], f["flag_id"]))]))
        elif what == "log":
            self._emit(render.section("EVENT LOG (tail)"))
            self._emit(render.event_tail(self.engine.log.as_dicts(), limit=step.get("limit", 20)))
        else:
            raise ScenarioError(f"unknown `show` target {what!r}")

    # -- entry point -------------------------------------------------------
    def run(self) -> ScenarioRun:
        scenario = self.scenario
        clock = FixedClock(scenario["clock_start_utc"])
        self.engine = Engine(ruleset=self.ruleset, clock=clock)

        self._emit(render.banner(scenario["title"], scenario.get("subtitle", "")))
        self._emit(render.kv([
            ("scenario", scenario["id"]),
            ("seed world", scenario["seed"]),
            ("clock start", scenario["clock_start_utc"]),
            ("ruleset hash", self.ruleset.ruleset_hash),
        ]))
        if scenario.get("premise"):
            self._emit([""] + render.bullets([" ".join(scenario["premise"].split())], marker=" ", indent=2))

        self._load_seed(self.engine)
        self._emit(render.section("SEED WORLD LOADED"))
        self._emit(render.kv([
            ("users", len(self.engine.state.users)),
            ("locations", len(self.engine.state.locations)),
            ("partner nodes", len(self.engine.state.partner_nodes)),
            ("items", len(self.engine.state.items)),
            ("events so far", len(self.engine.log)),
        ]))

        script = scenario["script"]
        command_steps = [s for s in script if "cmd" in s]
        total = len(command_steps)
        index = 0
        for step in script:
            if "note" in step:
                self._emit(["", "  " + " ".join(step["note"].split())])
            elif "advance_seconds" in step:
                self.engine.clock.advance(int(step["advance_seconds"]))
                self._emit(["", f"  ~ clock advanced to {self.engine.clock.now_utc()}"])
            elif "advance_to" in step:
                self.engine.clock.set_to(step["advance_to"])
                self._emit(["", f"  ~ clock advanced to {self.engine.clock.now_utc()}"])
            elif "show" in step:
                self._show(step["show"], step)
            elif "cmd" in step:
                index += 1
                self._run_command(step, index, total)
            else:
                raise ScenarioError(f"unrecognised script step: {sorted(step)}")

        self._emit(render.section("FINAL STATE"))
        state = self.engine.state
        self._emit(render.kv([
            ("events in log", len(self.engine.log)),
            ("log hash", self.engine.log.log_hash),
            ("rentals", f"{len(state.rentals)} " + ", ".join(
                f"{r['rental_id'][:10]}={r['state']}" for r in state.rentals_sorted())),
            ("items not available", ", ".join(
                f"{i['model_name']}={i['state']}" for i in state.items_sorted()
                if i["state"] != "available") or "(none)"),
            ("open disputes", sum(1 for d in state.disputes.values() if d["state"] == "open")),
            ("purchase offers", len(state.purchase_offers)),
        ]))

        # Prove the projection is disposable, in every single scenario run.
        replayed = fold(self.engine.log.as_dicts(), self.ruleset)
        live_store, replay_store = SqliteProjectionStore(), SqliteProjectionStore()
        live_store.rebuild(state, self.engine.log.as_dicts(), self.ruleset)
        replay_store.rebuild(replayed, self.engine.log.as_dicts(), self.ruleset)
        identical = live_store.fingerprint() == replay_store.fingerprint()
        self._emit(render.section("REPLAY CHECK"))
        self._emit(render.kv([
            ("projection fingerprint", live_store.fingerprint()),
            ("rebuilt-from-log fingerprint", replay_store.fingerprint()),
            ("identical", "YES" if identical else "NO -- THE REPLAY WINS, THE PROJECTION IS THE BUG"),
        ]))
        live_store.close(), replay_store.close()
        if not identical:
            raise ScenarioError(f"{scenario['id']}: projection diverged from a replay of its own log")

        run = ScenarioRun(scenario["id"], scenario["title"], self.out, self.engine)
        return run


def list_scenarios() -> list[pathlib.Path]:
    return sorted(SCENARIO_DIR.glob("*.yaml"))


def run_scenario(path: pathlib.Path, ruleset: Ruleset | None = None) -> ScenarioRun:
    return ScenarioRunner(path, ruleset).run()
