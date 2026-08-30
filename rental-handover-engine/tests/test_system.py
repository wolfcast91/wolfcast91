"""L2-L4 — the log, the projection, and the command engine, end to end."""
from __future__ import annotations

import pytest

from rhe.l2_log.events import EventLog, LogError
from rhe.l3_projections.sqlite_store import SqliteProjectionStore
from rhe.l3_projections.state import fold
from rhe.l4_commands import commands as cmd
from rhe.l4_commands.engine import CommandRejected, Engine
from rhe.l5_adapters.clock import DAY, HOUR, FixedClock


# -- event log --------------------------------------------------------------

def test_the_event_vocabulary_is_closed():
    log = EventLog()
    with pytest.raises(LogError, match="unknown event type"):
        log.append("SomethingHappened", {}, "2026-03-01T08:00:00Z", "h")


def test_float_payloads_are_refused():
    log = EventLog()
    with pytest.raises(LogError, match="is a float"):
        log.append("ItemListed", {"price": 19.99}, "2026-03-01T08:00:00Z", "h")


def test_event_seq_is_monotonic_and_contiguous():
    log = EventLog()
    for i in range(5):
        assert log.append("UserRegistered", {"n": i}, "2026-03-01T08:00:00Z", "h").event_seq == i + 1


def test_corrections_are_compensating_events_not_deletions():
    log = EventLog()
    log.append("UserRegistered", {"user_id": "usr_1"}, "2026-03-01T08:00:00Z", "h")
    log.compensate(1, "registered in error", "2026-03-01T09:00:00Z", "h")
    assert len(log) == 2                      # nothing was removed
    assert log.compensated_seqs() == {1}


def test_a_log_round_trips_through_jsonl(tmp_path):
    log = EventLog()
    log.append("UserRegistered", {"user_id": "usr_1"}, "2026-03-01T08:00:00Z", "h")
    log.append("IdentityVerified", {"user_id": "usr_1"}, "2026-03-01T08:00:01Z", "h")
    path = tmp_path / "log.jsonl"
    log.write_jsonl(path)
    assert EventLog.read_jsonl(path).log_hash == log.log_hash


def test_every_event_type_has_a_projection_reducer():
    from rhe.l2_log.events import EVENT_TYPES
    from rhe.l3_projections.state import REDUCERS
    assert set(EVENT_TYPES) == set(REDUCERS)


# -- a full Tier 1 rental ---------------------------------------------------

def _tier1_engine(ruleset):
    engine = Engine(ruleset=ruleset, clock=FixedClock("2026-03-01T08:00:00Z"))
    engine.execute(cmd.RegisterUser("maja", "Maja K.", "private", True))
    engine.execute(cmd.RegisterUser("tobi", "Tobias R.", "sole_trader", True))
    engine.execute(cmd.RegisterLocation("maja", "Hof Nord", "pin", 52520000, 13405000))
    engine.execute(cmd.ListItem("maja", "drill_driver", "Bosch GSR", "SN-1",
                                18000, 21900, 900, "Hof Nord", ("charger",)))
    return engine, next(iter(engine.state.items))


def _run_clean_rental(engine, item_id, start, end, pickup, ret, renter="tobi"):
    engine.execute(cmd.ReserveItem(item_id, renter, start, end))
    rental_id = max(engine.state.rentals, key=lambda r: engine.state.rentals[r]["opened_event_seq"])
    engine.execute(cmd.GrantAccess(rental_id))
    engine.clock.set_to(pickup)
    engine.execute(cmd.SubmitConditionReport(rental_id, "pre", renter, (), {"front": "clean"}))
    engine.execute(cmd.OpenLockbox(rental_id))
    engine.clock.set_to(ret)
    engine.execute(cmd.ReturnItem(rental_id))
    engine.execute(cmd.SubmitConditionReport(rental_id, "post", renter, (), {"front": "clean"}))
    engine.execute(cmd.AcceptReturn(rental_id))
    return rental_id


def test_a_clean_tier1_rental_closes_and_returns_the_item_to_the_market(ruleset):
    engine, item_id = _tier1_engine(ruleset)
    rental_id = _run_clean_rental(engine, item_id, "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z",
                                  "2026-03-02T10:00:00Z", "2026-03-03T18:00:00Z")
    assert engine.state.rentals[rental_id]["state"] == "closed"
    assert engine.state.items[item_id]["state"] == "available"
    assert engine.state.items[item_id]["clean_handovers_consecutive"] == 1
    assert len(engine.state.chain_for(item_id)) == 2


def test_the_lockbox_will_not_open_without_a_pre_rental_report(ruleset):
    from rhe.l1_kernel.transitions import IllegalTransition
    engine, item_id = _tier1_engine(ruleset)
    engine.execute(cmd.ReserveItem(item_id, "tobi", "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z"))
    rental_id = next(iter(engine.state.rentals))
    engine.execute(cmd.GrantAccess(rental_id))
    engine.clock.set_to("2026-03-02T10:00:00Z")
    with pytest.raises(IllegalTransition, match="pre_rental_condition_report_missing"):
        engine.execute(cmd.OpenLockbox(rental_id))


def test_a_wrong_pin_is_refused_and_the_attempt_is_logged(ruleset):
    engine, item_id = _tier1_engine(ruleset)
    engine.execute(cmd.ReserveItem(item_id, "tobi", "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z"))
    rental_id = next(iter(engine.state.rentals))
    engine.execute(cmd.GrantAccess(rental_id))
    engine.clock.set_to("2026-03-02T10:00:00Z")
    engine.execute(cmd.SubmitConditionReport(rental_id, "pre", "tobi", (), {"front": "clean"}))
    with pytest.raises(CommandRejected, match="wrong_secret"):
        engine.execute(cmd.OpenLockbox(rental_id, presented_secret="000000"))
    rejected = [e for e in engine.log.of_type("AccessCodeValidated")
                if e.payload["validation_result"] == "wrong_secret"]
    assert len(rejected) == 1


def test_an_unverified_renter_is_blocked_by_a_named_rule(ruleset):
    engine, item_id = _tier1_engine(ruleset)
    engine.execute(cmd.RegisterUser("rico", "Rico B.", "private", verify_identity=False))
    with pytest.raises(CommandRejected, match="unverified_identity"):
        engine.execute(cmd.ReserveItem(item_id, "rico", "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z"))
    assert any(f["flag_id"] == "unverified_identity" for f in engine.state.risk_flags)


def test_overdue_and_lost_both_wait_for_their_grace_period(ruleset):
    from rhe.l1_kernel.transitions import IllegalTransition
    engine, item_id = _tier1_engine(ruleset)
    engine.execute(cmd.ReserveItem(item_id, "tobi", "2026-03-02T08:00:00Z", "2026-03-03T08:00:00Z"))
    rental_id = next(iter(engine.state.rentals))
    engine.execute(cmd.GrantAccess(rental_id))
    engine.clock.set_to("2026-03-02T09:00:00Z")
    engine.execute(cmd.SubmitConditionReport(rental_id, "pre", "tobi", (), {"front": "clean"}))
    engine.execute(cmd.OpenLockbox(rental_id))

    engine.clock.set_to("2026-03-03T08:30:00Z")
    with pytest.raises(IllegalTransition, match="window_not_yet_overdue"):
        engine.execute(cmd.MarkOverdue(rental_id))
    engine.clock.advance(HOUR)
    engine.execute(cmd.MarkOverdue(rental_id))

    with pytest.raises(IllegalTransition, match="lost_grace"):
        engine.execute(cmd.DeclareLost(rental_id))
    engine.clock.advance(8 * DAY)
    engine.execute(cmd.DeclareLost(rental_id))
    assert engine.state.items[item_id]["state"] == "lost"
    assert engine.state.rentals[rental_id]["state"] == "written_off"


def test_a_dispute_cannot_close_without_a_human(ruleset):
    from rhe.l1_kernel.transitions import IllegalTransition
    engine, item_id = _tier1_engine(ruleset)
    engine.execute(cmd.ReserveItem(item_id, "tobi", "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z"))
    rental_id = next(iter(engine.state.rentals))
    engine.execute(cmd.GrantAccess(rental_id))
    engine.clock.set_to("2026-03-02T10:00:00Z")
    engine.execute(cmd.SubmitConditionReport(rental_id, "pre", "tobi", (), {"front": "clean"}))
    engine.execute(cmd.OpenLockbox(rental_id))
    engine.clock.set_to("2026-03-03T18:00:00Z")
    engine.execute(cmd.ReturnItem(rental_id))
    engine.execute(cmd.SubmitConditionReport(rental_id, "post", "tobi", ("crack_housing",), {"front": "cracked"}))
    engine.execute(cmd.ReportDamage(rental_id, "maja", ("crack_housing",)))
    engine.execute(cmd.OpenDispute(rental_id, "tobi", ("crack_housing",)))
    dispute_id = next(iter(engine.state.disputes))

    # The guard is literally named human_resolution_recorded.
    from rhe.l1_kernel.transitions import evaluate_transition
    with pytest.raises(IllegalTransition, match="no_human_resolution_on_record"):
        evaluate_transition("rental", "disputed", "DisputeResolvedNoFault", ruleset, {})

    engine.execute(cmd.ResolveDispute(dispute_id, "maja", "no_fault"))
    assert engine.state.disputes[dispute_id]["resolved_by"]
    assert engine.state.rentals[rental_id]["state"] == "closed"


def test_tier_graduation_after_four_clean_handovers(ruleset):
    engine = Engine(ruleset=ruleset, clock=FixedClock("2026-03-01T08:00:00Z"))
    engine.execute(cmd.RegisterUser("ferdi", "Ferdi O.", "private", True))
    engine.execute(cmd.RegisterUser("tobi", "Tobias R.", "sole_trader", True))
    engine.execute(cmd.RegisterLocation("ferdi", "Ostkreuz", "meetup", 52502000, 13469000))
    engine.execute(cmd.ListItem("ferdi", "sewing_machine", "Bernina 570", "SN-9",
                                195000, 229000, 3200, "Ostkreuz"))
    item_id = next(iter(engine.state.items))
    assert engine.state.items[item_id]["effective_tier"] == 3

    day = 2
    for _ in range(4):
        _run_clean_rental(
            engine, item_id,
            f"2026-03-{day:02d}T08:00:00Z", f"2026-03-{day + 2:02d}T08:00:00Z",
            f"2026-03-{day:02d}T10:00:00Z", f"2026-03-{day + 1:02d}T18:00:00Z")
        day += 5

    item = engine.state.items[item_id]
    assert item["effective_tier"] == 1 and item["graduated"] is True
    assert engine.state.trust_of("item", item_id) == 700


# -- the projection is disposable -------------------------------------------

def test_deleting_the_projection_and_replaying_reproduces_it_exactly(ruleset, tmp_path):
    engine, item_id = _tier1_engine(ruleset)
    _run_clean_rental(engine, item_id, "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z",
                      "2026-03-02T10:00:00Z", "2026-03-03T18:00:00Z")

    database = tmp_path / "projection.sqlite3"
    live = SqliteProjectionStore(database)
    live.rebuild(engine.state, engine.log.as_dicts(), ruleset)
    fingerprint = live.fingerprint()
    live.close()

    database.unlink()                                   # delete the cache entirely
    assert not database.exists()

    rebuilt = SqliteProjectionStore(database)
    rebuilt.rebuild(fold(engine.log.as_dicts(), ruleset), engine.log.as_dicts(), ruleset)
    assert rebuilt.fingerprint() == fingerprint
    rebuilt.close()


def test_folding_the_same_log_repeatedly_gives_the_same_state(ruleset):
    engine, item_id = _tier1_engine(ruleset)
    _run_clean_rental(engine, item_id, "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z",
                      "2026-03-02T10:00:00Z", "2026-03-03T18:00:00Z")
    events = engine.log.as_dicts()
    fingerprints = set()
    for _ in range(10):
        store = SqliteProjectionStore()
        store.rebuild(fold(events, ruleset), events, ruleset)
        fingerprints.add(store.fingerprint())
        store.close()
    assert len(fingerprints) == 1


def test_two_identical_engines_produce_identical_logs(ruleset):
    hashes = set()
    for _ in range(3):
        engine, item_id = _tier1_engine(ruleset)
        _run_clean_rental(engine, item_id, "2026-03-02T08:00:00Z", "2026-03-04T08:00:00Z",
                          "2026-03-02T10:00:00Z", "2026-03-03T18:00:00Z")
        hashes.add(engine.log.log_hash)
    assert len(hashes) == 1
