# Determinism

The nine charter rules, where each one is enforced in the codebase, and the test
that fails the build if it stops being true.

The general principle: **a rule that only lives in a document erodes.** So most of
these are checked by tests that read the source tree rather than by convention.

---

## 1. No randomness anywhere

No `random`, no `uuid4`, no shuffling, no sampling. Ids are content hashes over a
canonical field set, or monotonic counters seeded from the log itself.

| Where | What |
|---|---|
| `rhe/l1_kernel/ids.py` | `content_id(kind, fields)` → `sha256` over `ENTITY_ID_FIELDS[kind]`, rendered `usr_2b8e1d877f65`. Missing field → `IdError`. |
| `rhe/l1_kernel/access.py` | `derive_secret(rental_id, location_id, valid_from_epoch, length)` — PINs are derived, never generated. |
| `rhe/l2_log/events.py` | `event_seq` is a counter seeded from the log's own tail, so reload-and-continue reproduces the original sequence. |

**Tests:** `test_charter.py::test_no_banned_module_is_imported_anywhere` walks the
AST of every file under `rhe/` and fails on `random`, `secrets` or `uuid`.
`test_kernel.py::test_ids_are_content_hashes_not_counters`,
`::test_pins_are_derived_not_random`.

---

## 2. No hidden clock reads

Time enters through the injected `Clock` interface and nowhere else. `FixedClock`
is used in every test and every simulation; `SystemClock` exists only so the seam
is honest and is used by nothing.

| Where | What |
|---|---|
| `rhe/l5_adapters/clock.py` | The **only** file permitted to read a real clock. UTC, ISO 8601, second precision, `Z` suffix. Duration maths in integer seconds. |
| `rhe/l4_commands/engine.py` | Takes a clock by injection; stamps `clock_utc` on every event. |
| `sim/runner.py` | Each scenario declares `clock_start_utc`; the script advances it explicitly. |

`FixedClock.set_to` refuses to move backwards. Nothing in the system fires on a
timer — "overdue" is a command someone issues, gated on the injected clock, which
is why an eight-day overdue scenario runs in a millisecond.

**Test:** `test_charter.py::test_only_the_clock_adapter_reads_a_clock` — AST scan
for `datetime.now` / `utcnow` / `time.time` in every file except `clock.py`.

---

## 3. No floats in money, scores or thresholds

Money is integer minor units. Trust is an integer 0–1000. Percentages are integer
basis points. Zero float arithmetic in any decision path.

| Where | What |
|---|---|
| `rhe/l2_log/events.py` | `append()` rejects any float in a payload with a message naming the charter rule. |
| `rhe/l1_kernel/insurance.py` | `value_band()` rejects non-integer cents outright. |
| `rhe/l1_kernel/upsell.py` | `price * bp // 10000` — integer multiply, division last. Instalments use floor division. |
| `rhe/l1_kernel/ids.py` | `geo_cell()` takes integer microdegrees and refuses floats. |
| `tools/gen_insurance_rates.py` | Basis-of-100 integer multipliers, quantised to 25-cent steps. |

**Tests:** `test_charter.py::test_the_pure_kernel_contains_no_float_literals` and
`::test_the_pure_kernel_uses_no_true_division` (a bare `/` produces a float, so
every division in L1 must be `//`). `test_system.py::test_float_payloads_are_refused`.
`test_kernel.py::test_float_money_is_refused`, `::test_financing_is_integer_only`.

---

## 4. Ordered iteration everywhere

Every output-facing collection has an explicit, documented sort key. The keys are
declared in one place: `precedence.yaml:sort_keys`.

| Collection | Key |
|---|---|
| event log, access log | `event_seq` — **never** timestamp, which collides |
| inventory view | `owner_id, category_id, item_id` |
| condition report tags | `tag_id` (canonical, not insertion order) |
| damage findings | `component_id, tag_id` |
| handover steps | `step_index` (not file order) |
| purchase opportunities | `signal_rank, item_id` |
| search results | `distance_band, availability_rank, trust_score_desc, item_id` |

Also: `canonical_json` sorts keys before hashing; the classifier evaluates rows by
precedence rather than file order; `fold` sorts events by `event_seq`;
`compute_trust` sorts signals by `event_seq`; the SQLite fingerprint sorts every
table by all of its columns.

**Test:** `test_kernel.py::test_diff_is_independent_of_tag_order`,
`::test_trust_is_a_pure_fold_and_order_is_fixed_by_event_seq` (feeds the same
events in reverse and asserts the same score and the same contribution order),
`::test_signals_are_returned_in_the_declared_precedence_order`.

---

## 5. Rules live in versioned data, not code branches

Nine files in `rhe/l0_rules/rulesets/`, each with a `ruleset_version`, each hashed
on load. The composite hash is stamped on every event and every decision.

| File | v | What it owns |
|---|---|---|
| `tier_rules.yaml` | 3 | the 10-row decision table and the 8 attribute domains |
| `state_transitions.yaml` | 4 | both machines, guard names, grace periods |
| `damage_taxonomy.yaml` | 3 | 26 tags, severities, blocking set, report phases |
| `trust_weights.yaml` | 4 | every trust delta, bands, graduation thresholds, risk rules |
| `insurance_rates.yaml` | 2 | 320 premium cells, deposits, coverage tiers *(generated)* |
| `complementary_items.yaml` | 2 | 28 pairs and the three upsell thresholds |
| `category_tree.yaml` | 3 | 34 leaf categories and their default attributes |
| `handover_steps.yaml` | 2 | the ordered choreography and logged fields per tier |
| `precedence.yaml` | 1 | tie-breaking strategy and every sort key |

Hashing is over the **parsed document**, not the bytes: reformatting or adding a
comment must not change a decision's provenance, but any semantic edit must.
`make rulesets` prints the table. The loaded `Ruleset` is frozen — mutating it
raises.

**Tests:** `test_rulesets.py` — every file loads and declares a version, loading
twice gives the same hash, the ruleset is immutable at runtime, the generated rate
table regenerates byte for byte.

---

## 6. Total functions, no fallthrough

The tier classifier is total: every attribute combination maps to exactly one
tier. No default case, no silent `else`. Proven by enumeration, not asserted.

```
$ make prove
attribute space : accessory_count(3) x enclosable(2) x fragility(2) x has_fixed_location(2)
                  x partner_node_available(2) x requires_license(2) x value_band(4) x weight_class(3)
expected cells  : 1152
resolved cells  : 1152
gaps            : 0
catch-all rows  : none
unique precedence: True
cells matched by >1 row (resolved by precedence): 1122
dead rows       : none
PROOF HOLDS
```

The full table is committed as `artifacts/tier_decision_table.tsv` (1152 rows) and
byte-compared by the tests. The loader refuses a rule row with an empty `when`
(that is a catch-all, and `precedence.yaml` sets `allow_catch_all_row: false`).

Elsewhere: `fold` raises if an event type has no reducer — even a `_noop` must be
registered, because silence there means drift. The projection has 46 reducers for
46 event types, checked by a set-equality test.

**Tests:** `test_classifier.py::test_classifier_is_total_over_the_whole_input_space`,
`::test_no_rule_row_is_dead`, `::test_exhaustiveness_proof_script_passes`,
`::test_decision_table_artifact_is_current`,
`test_system.py::test_every_event_type_has_a_projection_reducer`.

---

## 7. Explicit tie-breaking

Where two rules could apply, a documented precedence decides — never code
evaluation order.

- **Tier rows:** unique integer `precedence`, lowest wins. The loader raises
  `RulesetError` on a duplicate, with a message naming this charter rule.
- **Upsell signals:** `precedence.yaml:upsell_signal_rank`.
- **Contradicting condition reports:** `precedence.yaml:condition_disagreement`
  decides only the order claims are *presented to a human*, never fault.
- **Transitions:** if two transitions matched the same `(state, trigger)` the
  machine raises `MachineError` rather than picking one.

**Tests:** `test_rulesets.py::test_tier_rule_precedence_is_unique`,
`::test_a_duplicate_precedence_is_rejected_at_load` (copies the rulesets, forces a
collision, asserts the load fails),
`test_classifier.py::test_every_overlap_is_resolved_by_unique_precedence`.

---

## 8. Append-only log as the single source of truth

No UPDATE, no DELETE. Corrections are compensating events. All state is derived.

| Where | What |
|---|---|
| `rhe/l2_log/events.py` | `append()` and `compensate()` are the only mutators. The event vocabulary is closed — an unknown type raises. |
| `rhe/l3_projections/state.py` | `fold(events, ruleset)` is pure; compensated events are skipped, never removed. |
| `rhe/l3_projections/sqlite_store.py` | `rebuild()` drops every table and re-inserts. There is deliberately **no** incremental update path. |
| `rhe/l4_commands/engine.py` | Refolds the entire log after every command. Quadratic and intentional: drift becomes structurally impossible rather than merely unlikely. |

**Replaying the full log from zero reproduces the exact current state.** This is
checked in four places: inside every scenario run, by the acceptance harness, and
by two dedicated tests — one of which deletes the SQLite file from disk before
rebuilding.

**Tests:** `test_system.py::test_deleting_the_projection_and_replaying_reproduces_it_exactly`,
`::test_folding_the_same_log_repeatedly_gives_the_same_state`,
`::test_corrections_are_compensating_events_not_deletions`,
`::test_a_log_round_trips_through_jsonl`.

---

## 9. No network, no LLM, no I/O in the decision path

L1 is pure: no file access, no database, no clock, no imports from above it. All
I/O lives at L5 behind interfaces with deterministic fakes.

| Adapter | Fake | Real target |
|---|---|---|
| `Clock` | `FixedClock` | system clock |
| `AccessProvider` | `FakeAccessProvider` | Lockii on igloohome hardware |
| `PhotoStore` | `FakePhotoStore` | content-addressed object storage with object lock |
| `InsurancePartner` | `FakeInsurancePartner` | Tint.ai |
| `FinancingPartner` | `FakeFinancingPartner` | Mondu |

The fakes return values from lookup tables and content hashes. Nothing is
generated, nothing is fetched, and no socket is ever opened by any code path in
this repository.

**Tests:** `test_charter.py::test_no_banned_module_is_imported_anywhere` (bans
`socket`, `http`, `urllib`, `requests`, `asyncio`),
`::test_the_pure_kernel_does_not_import_upward`,
`::test_the_kernel_does_not_open_files_or_databases`.

---

## The acceptance bar

> Run the full simulator suite twice, diff the two output directories: zero bytes
> of difference. Then delete the database, replay the event log from zero, and get
> identical state.

`make verify` runs both, literally, via `tools/verify_acceptance.py`:

```
1. THE SUITE, RUN TWICE, DIFFED BYTE FOR BYTE
   18/18 files identical; 0 differ, 0 unreadable
   event log hashes identical: YES

2. DELETE THE DATABASE, REPLAY THE LOG FROM ZERO
   9/9 scenarios: fingerprint IDENTICAL

VERDICT
  suite runs twice with zero byte difference  PASS
  state survives deleting and replaying       PASS

  ACCEPTANCE BAR MET
```

`make verify` also runs the exhaustiveness proof, re-renders the item bench,
byte-compares all nine golden files, runs every scenario twice in-process, and
finishes with the 112-test suite.

---

## Known determinism boundaries

Honest limits, so nobody discovers them the hard way:

- **Python version.** Output depends on `sha256` (stable) and dict insertion order
  for the *declared* order of YAML mappings (guaranteed since Python 3.7). Tested
  on 3.11.
- **PyYAML.** Documents are hashed after parsing, so a PyYAML change that altered
  parsing semantics would change every hash. Pinned by `requirements.txt`.
- **Locale.** `canonical_json` uses `ensure_ascii=True` and all rendering is
  ASCII-only box drawing, so locale cannot affect the bytes.
- **The rate table generator.** It contains a formula, deliberately, because it is
  build-time. Its output is committed and a test regenerates and byte-compares it,
  so the two cannot drift — but if you change a multiplier you must re-run
  `make` targets and review the diff.
