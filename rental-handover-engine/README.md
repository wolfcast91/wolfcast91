# Rental Handover Engine

A deterministic engine for a rental marketplace where **most handovers involve no
humans at all** — and where every decision the system makes can be cited like a
legal reference rather than explained like a model output.

```
Tier 2, because tier_rules.yaml v3 row R07 (ruleset fce31abe)
1450 cents, because insurance_rates.yaml v2 cell 'mid|1|good|days_3'
Rejected, because id_verified == false (trust_weights.yaml v4, severity: block)
```

Local-first, CLI-first, SQLite. **Zero AI calls, zero network calls, zero
randomness in the runtime path.** Everything a system like this would normally
reach for a model to do is replaced by an explicit, hand-editable rule table.

---

## Quick start

```bash
make setup     # installs PyYAML and pytest. That is the entire dependency list.
make demo      # watch a complete Tier 1 rental: reserve -> PIN -> photos -> return
make run       # all nine scenarios
make verify    # the proof: exhaustiveness, golden files, replay, the acceptance bar
```

Then poke at it:

```bash
make tiers                                       # the five tiers and their choreography
make classify                                    # every category, with the rule row that decided it
python3 -m rhe.l6_cli.main classify sewing_machine   # one item, fully explained
python3 -m rhe.l6_cli.main run 06_upsell_conversion  # the business model firing
make rulesets                                    # every rule file, its version and its hash
```

---

## The concept

A rental marketplace spanning C2C, B2C and B2B — private individuals, homeowners,
small businesses and professional fleets renting tools, equipment and machines to
verified users. Three things make it distinct:

**1. Hands-free handover by design.** Most rentals require zero coordination.
Smart lockboxes, gate codes, guided self-service pickup with in-app instructions
on where the thing is and how to open it.

**2. Insurance and financing are the business model, not features.** The platform
is free to use. Revenue comes from embedded insurance on each rental, and from
financing when a renter converts into a buyer.

**3. Community-based quality inspection.** Each renter documents the item before
use, confirming or extending what the previous renter logged. This produces a
timestamped **condition chain** per item — the risk data that makes automated
insurance pricing possible in the first place.

### Why this niche

The existing landscape is two silos that do not talk to each other. Heavy
professional rental (Boels, Loxam, Hornbach's Boels partnership) runs enormous
fleets with zero peer network and zero community layer. Small local tool-sharing
has ID verification and rental protocols, but handover is a manual meetup with no
smart lock, no insurance-by-design and no path to ownership.

Nobody bridges them. The actual niche is the middle tier: tradespeople and small
businesses with idle mid-value inventory — compressors, scaffolding, event gear,
small hoists, specialty power tools — who want passive income without handover
hassle, renting to prosumers who would rather rent-to-try-then-buy than commit
capital upfront.

---

## The tier system

Handover tiers are grouped by **mechanism, not by item type**. That is the whole
trick: a carpet cleaner is Tier 1 in a lockbox and Tier 5 at a partner counter,
because the tier describes how custody moves, not what the thing is.

| Tier | Mechanism | Human contact | Typical |
|---|---|---|---|
| **1** | Fully Autonomous — smart lockbox, time-boxed PIN, photo gate before unlock | none | drills, sanders, projectors, small generators |
| **2** | Semi-Autonomous — yard gate code plus spatial instructions, self-service load-out | none | scaffolding, ladders, mixers, party tents |
| **3** | Assisted Meetup — both parties present, shared checklist, both signatures | both parties | cameras, instruments, e-bikes, trailers |
| **4** | Certified / Licensed — contract, certification check, logged operator at a depot | depot staff | cranes, forklifts, excavators |
| **5** | Depot / Partner Node — consignment at a hardware store or repair café | partner staff | anything an owner hands custody of |

Tier 4 is not a gap in the automation story, it is a **category split stated out
loud**. A 30-tonne Liebherr is never going behind a PIN, and `requires_license`
sits at the highest precedence in the decision table for exactly that reason. The
platform's value there is inventory visibility, contracts and financing.

**Items graduate.** A Tier 3 item that survives four consecutive clean handovers,
reaches item trust 700, has zero lifetime disputes, and physically fits in a
lockbox becomes Tier 1. Watch it happen: `make run` → `02_tier3_graduation`.

---

## Architecture in one screen

Strict downward dependency. No layer calls upward. Enforced by a test that parses
the source.

```
L6  Interface       CLI. Reads projections, writes only by issuing commands. No logic.
L5  Adapters        The ONLY place I/O exists. Clock, locks, photos, insurer, financier.
L4  Commands        The only write path: validate -> evaluate -> append -> project.
L3  Projections     Derived state. A cache. Delete it and replay; the replay wins.
L2  Event Log       Append-only. No UPDATE, no DELETE, ever. The single source of truth.
L1  Pure Kernel     Pure functions. No I/O, no clock, no mutable state. All the logic.
L0  Rulesets        Versioned, hashed YAML. Every threshold in the system lives here.
```

### Where AI would normally sneak in — and what replaced it

| Would-be AI feature | What this system does instead |
|---|---|
| Damage detection from photos | A closed 26-tag taxonomy. Photos are evidence attached to a structured claim, **never a decision input**. Nothing here reads a pixel. |
| Item categorisation | A fixed category tree. Each node carries default attributes; owner overrides are logged; the tier follows deterministically. |
| Matching / search | Deterministic filter plus an explicit sort key, down to `item_id` as the final tiebreak. |
| Upsell detection | Three integer comparisons against thresholds in a YAML file. |
| Pricing | A 320-cell lookup table keyed by four bands. No formula, no interpolation, no fallback — a key miss raises rather than guesses. |
| Trust scoring | A pure integer fold over the log, recomputed from zero every time it is read. |
| Fraud flags | Six boolean rules. Every flag that fires carries the literal rule text. |

The payoff: **every decision is a citation.** That is the thing a model-driven
competitor structurally cannot offer, and it is precisely what an insurance
partner needs before they will underwrite anything.

---

## What is in here

```
rhe/
  l0_rules/rulesets/   nine versioned YAML files — every rule in the system
  l1_kernel/           classifier, state machines, condition diff, trust, rates, upsell, access
  l2_log/              the append-only event log
  l3_projections/      the fold, and the disposable SQLite cache it fills
  l4_commands/         22 typed commands and the engine that runs them
  l5_adapters/         clock, smart lock, photo store, insurer, financier — all deterministic fakes
  l6_cli/              the CLI and the terminal renderer
sim/
  seed/world.yaml      8 users, 6 locations, 2 partner nodes, 28 items
  seed/item_bench.yaml 34 classification cases, obvious and deliberately ambiguous
  scenarios/           nine committed scenario scripts
  golden/              their byte-compared expected output
tools/                 the exhaustiveness prover, the rate-table generator, the acceptance harness
artifacts/             the full 1152-cell decision table, and the rendered item bench
tests/                 112 tests, including a charter test that parses the source
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for every design decision and the open
questions each one left behind, and **[DETERMINISM.md](DETERMINISM.md)** for each
charter rule and exactly where in the codebase it is enforced and tested.

---

## Real integrations this is shaped for

None of these are built. Each fake at L5 is shaped so the real thing drops in
behind it without touching L0–L4:

- **Handover automation → Lockii**, running on igloohome hardware with
  offline-capable time-limited PINs. Our `FakeAccessProvider` derives PINs from
  `sha256(rental_id, location_id, window_start)` — same shape, same offline
  validation, and deterministic so a rental replays bit for bit.
- **Embedded insurance → Tint.ai**, protection built for P2P platforms with
  real-time per-transaction risk pricing. Our local rate table is what we quote
  and what a partner response is reconciled against. A partner that disagrees
  with our table is information about our table, which is only possible because
  ours is auditable.
- **Embedded financing → Mondu**, German B2B BNPL with 3/6/12-month instalments
  and fee splitting. Our upsell engine decides *when* to offer; Mondu decides the
  terms.

---

## The acceptance bar

```
make verify
```

Runs the classifier exhaustiveness proof over all 1152 cells, re-renders the item
bench, byte-compares every scenario against its golden file, runs every scenario
twice in-process, then the bar itself: the full suite run twice into two
directories and diffed (zero bytes of difference), and the projection database
deleted and rebuilt from the event log (identical state). Then 112 tests.

The build is not done until both hold. They hold.
