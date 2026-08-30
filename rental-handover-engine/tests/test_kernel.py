"""L1 — the rest of the kernel: transitions, condition diff, trust, rates, upsell, access."""
from __future__ import annotations

import pytest

from rhe.l1_kernel.access import (
    derive_secret, issue_credential, qr_payload, validate_credential,
)
from rhe.l1_kernel.condition import (
    ConditionError, ConditionReport, diff_condition, validate_tags,
)
from rhe.l1_kernel.ids import IdError, content_id, geo_cell
from rhe.l1_kernel.insurance import RateNotFound, quote_premium, trust_band, value_band
from rhe.l1_kernel.transitions import (
    IllegalTransition, evaluate_transition, legal_triggers,
)
from rhe.l1_kernel.trust import (
    ItemHistory, compute_trust, evaluate_graduation, evaluate_risk_flags,
)
from rhe.l1_kernel.upsell import CompletedRental, detect_upsell


# -- state machines ---------------------------------------------------------

def test_a_legal_transition_resolves_to_one_next_state(ruleset):
    decision = evaluate_transition(
        "item", "available", "ItemReserved", ruleset, {"renter_id_verified": True})
    assert decision.to_state == "reserved"


def test_an_illegal_transition_raises_rather_than_no_opping(ruleset):
    with pytest.raises(IllegalTransition) as exc:
        evaluate_transition("rental", "closed", "ItemPickedUp", ruleset, {})
    assert "no such transition" in str(exc.value)


def test_a_refused_guard_names_itself(ruleset):
    with pytest.raises(IllegalTransition, match="guard renter_id_verified refused"):
        evaluate_transition("item", "available", "ItemReserved", ruleset,
                            {"renter_id_verified": False})


def test_terminal_states_accept_nothing(ruleset):
    for machine, state in (("item", "retired"), ("item", "sold"), ("rental", "closed")):
        assert legal_triggers(machine, state, ruleset) == ()


def test_a_fixed_event_sequence_replays_identically_100_times(ruleset):
    """Charter: a fixed sequence produces an identical final state, every time."""
    sequence = [
        ("available", "ItemReserved"), ("reserved", "ItemPickedUp"),
        ("out", "ItemReturnInitiated"), ("in_return_check", "DamageReported"),
        ("damage_hold", "DisputeOpened"), ("disputed", "DisputeResolvedNoFault"),
    ]
    context = {
        "renter_id_verified": True, "access_granted": True,
        "pre_report_id": "cnd_x", "post_report_id": "cnd_y",
        "resolution_recorded_by": "usr_human",
    }
    finals = set()
    for _ in range(100):
        state = "available"
        for expected_from, trigger in sequence:
            assert state == expected_from
            state = evaluate_transition("item", state, trigger, ruleset, context).to_state
        finals.add(state)
    assert finals == {"available"}


# -- condition diff ---------------------------------------------------------

def _report(rid, tags, manifest=(), prev=None):
    return ConditionReport(
        report_id=rid, item_id="itm_1", rental_id="rnt_1", phase="post",
        submitted_by="usr_1", submitted_at_utc="2026-03-01T08:00:00Z", event_seq=1,
        damage_tags=tuple(tags), photo_slots=("front",),
        accessory_manifest=tuple(manifest), prev_report_id=prev)


def test_diff_is_independent_of_tag_order(ruleset):
    a = _report("a", ["scratch_minor", "dent_major", "battery_degraded"])
    b = _report("b", ["battery_degraded", "scratch_minor", "dent_major"])
    forward = diff_condition(a, b, ruleset)
    reverse = diff_condition(b, a, ruleset)
    assert forward.appeared == reverse.appeared == ()
    assert [f.tag_id for f in forward.confirmed] == [f.tag_id for f in reverse.confirmed]


def test_new_damage_is_detected_and_blocking_tags_are_flagged(ruleset):
    diff = diff_condition(_report("a", ["scratch_minor"]),
                          _report("b", ["scratch_minor", "crack_housing"]), ruleset)
    assert [f.tag_id for f in diff.appeared] == ["crack_housing"]
    assert diff.blocking == ("crack_housing",)
    assert diff.deposit_hold_cents == 12000
    assert not diff.is_clean


def test_a_vanishing_tag_is_a_recorded_disagreement_not_a_judgement(ruleset):
    diff = diff_condition(_report("a", ["crack_housing"]), _report("b", []), ruleset)
    assert [f.tag_id for f in diff.disappeared] == ["crack_housing"]
    assert diff.chain_disagreement is True


def test_missing_accessories_are_detected(ruleset):
    diff = diff_condition(_report("a", [], ["case", "charger"]),
                          _report("b", [], ["case"]), ruleset)
    assert diff.missing_accessories == ("charger",)


def test_tags_outside_the_closed_taxonomy_are_rejected(ruleset):
    with pytest.raises(ConditionError, match="outside the closed taxonomy"):
        validate_tags(["looks_a_bit_sad"], ruleset)


def test_the_first_report_has_no_predecessor_and_still_diffs(ruleset):
    diff = diff_condition(None, _report("a", ["scratch_minor"]), ruleset)
    assert [f.tag_id for f in diff.appeared] == ["scratch_minor"]
    assert diff.prev_report_id is None


# -- trust ------------------------------------------------------------------

def _signal(seq, signal, subject_id="usr_1", kind="user"):
    return {"event_seq": seq, "event_type": "TrustSignalRecorded",
            "payload": {"subject_kind": kind, "subject_id": subject_id,
                        "signal": signal, "caused_by_event": f"evt_{seq}"}}


def test_trust_is_a_pure_fold_and_order_is_fixed_by_event_seq(ruleset):
    events = [_signal(3, "ReturnedLate"), _signal(1, "IdentityVerified"),
              _signal(2, "RentalClosedClean")]
    first = compute_trust("user", "usr_1", events, ruleset)
    shuffled = compute_trust("user", "usr_1", list(reversed(events)), ruleset)
    assert first.score == shuffled.score == 605
    assert [c.event_seq for c in first.contributions] == [1, 2, 3]


def test_trust_is_clamped_after_each_signal_not_once_at_the_end(ruleset):
    """A big negative then a big positive must not restore a score that was
    clamped at the floor -- clamping per step is what makes the order matter."""
    events = [_signal(i, "ItemDeclaredLost") for i in range(1, 4)]
    events.append(_signal(4, "IdentityVerified"))
    assert compute_trust("user", "usr_1", events, ruleset).score == 120


def test_graduation_requires_every_threshold(ruleset):
    assert evaluate_graduation(3, ItemHistory(4, 0, 700, True), ruleset).granted
    assert not evaluate_graduation(3, ItemHistory(3, 0, 700, True), ruleset).granted
    assert not evaluate_graduation(3, ItemHistory(4, 0, 699, True), ruleset).granted
    assert not evaluate_graduation(3, ItemHistory(4, 1, 900, True), ruleset).granted


def test_graduation_cannot_violate_physics(ruleset):
    """A non-enclosable item can never take the Tier 3 -> Tier 1 path."""
    decision = evaluate_graduation(3, ItemHistory(99, 0, 1000, False), ruleset)
    assert decision.to_tier != 1


def test_every_risk_flag_cites_the_rule_that_fired(ruleset):
    flags = evaluate_risk_flags({"id_verified": False, "user_trust": 300}, ruleset)
    assert {f["flag_id"] for f in flags} == {"unverified_identity", "low_trust"}
    for flag in flags:
        assert flag["rule"] and flag["citation"]


# -- insurance --------------------------------------------------------------

def test_premium_is_a_lookup_with_full_provenance(ruleset):
    quote = quote_premium(45000, 1, 720, 259200, ruleset)
    assert quote.lookup_key == "mid|1|good|days_3"
    assert isinstance(quote.premium_cents, int)
    assert quote.coverage_tier == "standard"


def test_the_same_inputs_always_give_the_same_premium(ruleset):
    quotes = {quote_premium(45000, 3, 500, 86400, ruleset).premium_cents for _ in range(50)}
    assert len(quotes) == 1


def test_band_boundaries_are_exact_with_no_interpolation(ruleset):
    assert value_band(19999, ruleset) == "low"
    assert value_band(20000, ruleset) == "mid"
    assert trust_band(399, ruleset) == "new"
    assert trust_band(400, ruleset) == "fair"


def test_float_money_is_refused(ruleset):
    with pytest.raises(RateNotFound, match="integer cents"):
        quote_premium(450.0, 1, 700, 86400, ruleset)


def test_a_missing_cell_raises_rather_than_guessing(ruleset):
    with pytest.raises(RateNotFound):
        quote_premium(45000, 9, 700, 86400, ruleset)


# -- upsell -----------------------------------------------------------------

def _history(n, item="itm_x", category="tile_saw", cents=13300, base=1772352000):
    return [CompletedRental(f"rnt_{i}", item, category, "usr_1", base - 86400 * i, cents)
            for i in range(1, n + 1)]


def test_cumulative_spend_threshold_is_exact_integer_arithmetic(ruleset):
    # 60_00 bp of 100000 cents = 60000 cents. Two rentals of 30000 hit it exactly.
    history = _history(2, cents=30000)
    fired = detect_upsell("usr_1", "itm_x", "tile_saw", 100000, history, 1772352000, 700, ruleset)
    assert "cumulative_spend_threshold" in {o.signal_id for o in fired}

    just_under = _history(2, cents=29999)
    fired2 = detect_upsell("usr_1", "itm_x", "tile_saw", 100000, just_under, 1772352000, 700, ruleset)
    assert "cumulative_spend_threshold" not in {o.signal_id for o in fired2}


def test_signals_are_returned_in_the_declared_precedence_order(ruleset):
    history = _history(3) + [CompletedRental("rnt_9", "itm_y", "dust_extractor", "usr_1", 1772000000, 3000)]
    fired = detect_upsell("usr_1", "itm_x", "tile_saw", 20000, history, 1772352000, 700, ruleset)
    assert [o.signal_id for o in fired] == [
        "cumulative_spend_threshold", "repeat_rental_threshold", "complementary_pair"]
    assert [o.signal_rank for o in fired] == [1, 2, 3]


def test_rentals_outside_the_window_do_not_count(ruleset):
    old = [CompletedRental(f"rnt_{i}", "itm_x", "tile_saw", "usr_1", 1000, 30000) for i in range(3)]
    assert detect_upsell("usr_1", "itm_x", "tile_saw", 20000, old, 1772352000, 700, ruleset) == ()


def test_a_low_trust_renter_gets_no_financing_offer(ruleset):
    fired = detect_upsell("usr_1", "itm_x", "tile_saw", 20000, _history(3), 1772352000, 400, ruleset)
    assert all(o.financing is None and not o.purchase_conversion_eligible for o in fired)
    assert all("below" in o.blocked_reason for o in fired)


def test_financing_is_integer_only(ruleset):
    fired = detect_upsell("usr_1", "itm_x", "tile_saw", 100001, _history(3, cents=30000),
                          1772352000, 700, ruleset)
    for monthly in fired[0].financing.monthly_cents_by_term.values():
        assert isinstance(monthly, int)


# -- access -----------------------------------------------------------------

def test_pins_are_derived_not_random():
    assert derive_secret("rnt_1", "loc_1", 1772352000, 6) == derive_secret("rnt_1", "loc_1", 1772352000, 6)
    assert derive_secret("rnt_1", "loc_1", 1772352000, 6) != derive_secret("rnt_2", "loc_1", 1772352000, 6)


def test_a_pin_is_six_digits():
    pin = derive_secret("rnt_1", "loc_1", 1772352000, 6)
    assert len(pin) == 6 and pin.isdigit()


def test_a_credential_only_works_inside_its_window():
    credential = issue_credential("rnt_1", "loc_1", "pin", 1000, 2000, "a", "b")
    assert validate_credential(credential, credential.secret, 1500) == (True, "accepted")
    assert validate_credential(credential, credential.secret, 999)[1] == "too_early"
    assert validate_credential(credential, credential.secret, 2001)[1] == "expired"
    assert validate_credential(credential, "000000", 1500)[1] == "wrong_secret"
    assert validate_credential(credential, credential.secret, 1500, revoked=True)[1] == "revoked"


def test_a_meetup_needs_no_credential():
    credential = issue_credential("rnt_1", "loc_1", "meetup", 1000, 2000, "a", "b")
    assert credential.secret == ""
    assert validate_credential(credential, "", 1500)[0] is True


def test_a_zero_length_window_is_refused():
    with pytest.raises(Exception):
        issue_credential("rnt_1", "loc_1", "pin", 1000, 1000, "a", "b")


def test_qr_payload_is_content_derived():
    assert qr_payload("rnt_1", "loc_1") == qr_payload("rnt_1", "loc_1")


# -- ids --------------------------------------------------------------------

def test_ids_are_content_hashes_not_counters():
    fields = {"handle": "maja", "account_type": "private"}
    assert content_id("user", fields) == content_id("user", fields)
    assert content_id("user", fields) != content_id("user", {**fields, "handle": "tobi"})


def test_a_missing_canonical_field_is_an_error():
    with pytest.raises(IdError, match="requires field"):
        content_id("user", {"handle": "maja"})


def test_geo_cells_refuse_floats():
    assert geo_cell(52520000, 13405000) == "52520:13405"
    with pytest.raises(IdError, match="integer microdegrees"):
        geo_cell(52.52, 13.405)
