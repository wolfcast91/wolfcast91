"""L4 — The command engine. The single write path.

Every command follows the same four steps, in the same order, with no
exceptions:

    1. VALIDATE  -- entities exist, the actor is who they claim, inputs are sane
    2. EVALUATE  -- ask L1 (classifier, state machines, diff, trust, rates)
    3. APPEND    -- write immutable events to L2
    4. PROJECT   -- rebuild L3 by folding the whole log from zero

Step 4 refolds the ENTIRE log after every command. That is quadratic and
deliberate: at prototype scale it costs nothing, and it makes projection drift
structurally impossible rather than merely unlikely. A production system would
fold incrementally and run this full refold as an audit -- the point is that the
two must agree, and here they cannot fail to.

No I/O happens in this module except through injected L5 adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from rhe.l0_rules.loader import Ruleset, load_ruleset
from rhe.l1_kernel import classify, condition, insurance, transitions, trust, upsell
from rhe.l1_kernel.ids import content_id, geo_cell
from rhe.l2_log.events import Event, EventLog
from rhe.l3_projections.state import ProjectionState, fold
from rhe.l4_commands import commands as cmd
from rhe.l5_adapters.clock import FixedClock, utc_to_epoch
from rhe.l5_adapters.lock_provider import FakeAccessProvider
from rhe.l5_adapters.photo_store import FakePhotoStore
from rhe.l5_adapters.value_partners import FakeFinancingPartner, FakeInsurancePartner


class CommandRejected(Exception):
    """A command failed validation or a guard. Typed, never a silent no-op."""


@dataclass
class CommandResult:
    """What one command did, in enough detail for the CLI to narrate it."""

    command: str
    events: tuple[Event, ...]
    notes: tuple[str, ...] = ()
    decisions: tuple[str, ...] = ()   # citation strings from L1

    @property
    def event_types(self) -> tuple[str, ...]:
        return tuple(e.event_type for e in self.events)


# Tier -> the access_type its handover uses. Derived from handover_steps.yaml
# semantics; kept here because it maps a tier to an ADAPTER, which is L4's job.
TIER_ACCESS_TYPE = {1: "pin", 2: "gate_code", 3: "meetup", 4: "staffed", 5: "depot"}


class Engine:
    """The whole system, wired together. One object, injected adapters, no globals."""

    def __init__(
        self,
        ruleset: Ruleset | None = None,
        clock: FixedClock | None = None,
        access_provider: FakeAccessProvider | None = None,
        photo_store: FakePhotoStore | None = None,
        insurance_partner: FakeInsurancePartner | None = None,
        financing_partner: FakeFinancingPartner | None = None,
    ) -> None:
        self.ruleset = ruleset or load_ruleset()
        self.clock = clock or FixedClock()
        self.access = access_provider or FakeAccessProvider()
        self.photos = photo_store or FakePhotoStore()
        self.insurer = insurance_partner or FakeInsurancePartner()
        self.financier = financing_partner or FakeFinancingPartner()
        self.log = EventLog()
        self.state = ProjectionState()

    # -- infrastructure ----------------------------------------------------
    def _emit(self, event_type: str, payload: Mapping[str, Any]) -> Event:
        return self.log.append(event_type, payload, self.clock.now_utc(), self.ruleset.ruleset_hash)

    def _reproject(self) -> None:
        """Step 4. Full refold, every time."""
        self.state = fold(self.log.as_dicts(), self.ruleset)

    def _user_by_handle(self, handle: str) -> dict[str, Any]:
        for user in self.state.users.values():
            if user["handle"] == handle:
                return user
        raise CommandRejected(f"no such user handle: {handle!r}")

    def _location_by_label(self, label: str) -> dict[str, Any]:
        for loc in self.state.locations.values():
            if loc["label"] == label:
                return loc
        raise CommandRejected(f"no such location label: {label!r}")

    def _item(self, item_id: str) -> dict[str, Any]:
        if item_id not in self.state.items:
            raise CommandRejected(f"no such item: {item_id!r}")
        return self.state.items[item_id]

    def _rental(self, rental_id: str) -> dict[str, Any]:
        if rental_id not in self.state.rentals:
            raise CommandRejected(f"no such rental: {rental_id!r}")
        return self.state.rentals[rental_id]

    def _context(self, rental: Mapping[str, Any]) -> dict[str, Any]:
        """Assemble the guard context. One place, so every guard sees the same world."""
        item = self.state.items[rental["item_id"]]
        renter = self.state.users[rental["renter_id"]]
        grant = self.state.access_grants.get(rental["rental_id"])
        dispute = next(
            (d for d in self.state.disputes.values()
             if d["rental_id"] == rental["rental_id"] and d["state"] == "resolved"),
            None,
        )
        return {
            "location_id": item["location_id"],
            "tier": rental["tier"],
            "renter_id_verified": renter["id_verified"],
            "has_overlapping_reservation": False,
            "access_granted": grant is not None and not grant["revoked"],
            "pre_report_id": rental["pre_report_id"],
            "post_report_id": rental["post_report_id"],
            "now_epoch": self.clock.now_epoch(),
            "window_end_epoch": rental["window_end_epoch"],
            "resolution_recorded_by": dispute["resolved_by"] if dispute else None,
            "deposit_hold_cents": rental.get("deposit_cents"),
            "claim_id": rental.get("policy_ref"),
            "accepted_purchase_offer_id": next(
                (o["offer_id"] for o in self.state.purchase_offers.values()
                 if o["item_id"] == item["item_id"] and o["state"] == "accepted"), None),
        }

    def _check(self, rental: Mapping[str, Any], trigger: str, actor: str | None = None) -> tuple[str, str]:
        """Evaluate BOTH machines before appending anything. Either refusal
        aborts the command, so the log never records a half-applied transition."""
        context = self._context(rental)
        item = self.state.items[rental["item_id"]]
        item_decision = transitions.evaluate_transition(
            "item", item["state"], trigger, self.ruleset, context, actor)
        rental_decision = transitions.evaluate_transition(
            "rental", rental["state"], trigger, self.ruleset, context, actor)
        return item_decision.to_state, rental_decision.to_state

    def _trust_signal(self, kind: str, subject_id: str, signal: str, caused_by: str) -> Event:
        return self._emit("TrustSignalRecorded", {
            "subject_kind": kind, "subject_id": subject_id,
            "signal": signal, "caused_by_event": caused_by,
        })

    # -- dispatch ----------------------------------------------------------
    def execute(self, command: cmd.Command) -> CommandResult:
        handler = self._HANDLERS.get(type(command).__name__)
        if handler is None:
            raise CommandRejected(f"no handler for command {type(command).__name__}")
        before = len(self.log)
        result = handler(self, command)
        self._reproject()
        result.events = self.log.events[before:]
        return result

    # -- handlers ----------------------------------------------------------
    def _register_user(self, c: cmd.RegisterUser) -> CommandResult:
        user_id = content_id("user", {"handle": c.handle, "account_type": c.account_type})
        if user_id in self.state.users:
            raise CommandRejected(f"user {c.handle!r} already registered")
        self._emit("UserRegistered", {
            "user_id": user_id, "handle": c.handle, "display_name": c.display_name,
            "account_type": c.account_type,
        })
        notes = [f"registered {c.handle} ({c.account_type}) as {user_id}"]
        if c.verify_identity:
            e = self._emit("IdentityVerified", {"user_id": user_id, "method": "eid_document_scan"})
            self._trust_signal("user", user_id, "IdentityVerified", e.event_id)
            notes.append("identity verified (+120 trust)")
        return CommandResult("RegisterUser", (), tuple(notes))

    def _register_location(self, c: cmd.RegisterLocation) -> CommandResult:
        owner = self._user_by_handle(c.owner_handle)
        cell = geo_cell(c.lat_micro, c.lon_micro)
        location_id = content_id("location", {
            "owner_id": owner["user_id"], "access_type": c.access_type,
            "geo_cell": cell, "label": c.label,
        })
        instruction_id = None
        if c.spatial_instruction:
            # Spatial instructions are content-addressed too, so "third pallet,
            # blue tarp" resolves to a stable id that a photo can be checked against.
            instruction_id = f"spi_{content_id('location', {'owner_id': owner['user_id'], 'access_type': c.access_type, 'geo_cell': cell, 'label': c.spatial_instruction})[4:16]}"
        self._emit("LocationRegistered", {
            "location_id": location_id, "owner_id": owner["user_id"], "label": c.label,
            "access_type": c.access_type, "geo_cell": cell,
            "lat_micro": c.lat_micro, "lon_micro": c.lon_micro,
            "spatial_instruction": c.spatial_instruction,
            "spatial_instruction_id": instruction_id,
            "landmark_photo_slot": c.landmark_photo_slot,
            "partner_node_id": c.partner_node_id,
        })
        return CommandResult("RegisterLocation", (), (f"location {c.label!r} ({c.access_type}) -> {location_id}",))

    def _register_partner_node(self, c: cmd.RegisterPartnerNode) -> CommandResult:
        cell = geo_cell(c.lat_micro, c.lon_micro)
        node_id = content_id("partner_node", {"operator_name": c.operator_name, "geo_cell": cell})
        self._emit("PartnerNodeRegistered", {
            "partner_node_id": node_id, "operator_name": c.operator_name,
            "node_type": c.node_type, "geo_cell": cell, "intake_fee_cents": c.intake_fee_cents,
        })
        return CommandResult("RegisterPartnerNode", (), (f"partner node {c.operator_name} -> {node_id}",))

    def _list_item(self, c: cmd.ListItem) -> CommandResult:
        owner = self._user_by_handle(c.owner_handle)
        location = self._location_by_label(c.location_label)
        decision, resolution = classify.classify_category(
            c.category_id, self.ruleset, c.attribute_overrides)
        item_id = content_id("item", {
            "owner_id": owner["user_id"], "category_id": c.category_id,
            "model_name": c.model_name, "serial_number": c.serial_number,
        })
        if item_id in self.state.items:
            raise CommandRejected(f"item {c.model_name!r} ({c.serial_number}) already listed")

        for attribute, value in sorted(c.attribute_overrides.items()):
            self._emit("AttributeOverridden", {
                "item_id": item_id, "attribute": attribute, "value": str(value),
                "overridden_by": owner["user_id"],
            })
        self._emit("ItemListed", {
            "item_id": item_id, "owner_id": owner["user_id"], "category_id": c.category_id,
            "model_name": c.model_name, "serial_number": c.serial_number,
            "replacement_value_cents": c.replacement_value_cents,
            "purchase_price_cents": c.purchase_price_cents, "day_rate_cents": c.day_rate_cents,
            "location_id": location["location_id"],
            "partner_node_id": location.get("partner_node_id"),
            "tier": decision.tier, "tier_row_id": decision.row_id,
            "tier_citation": decision.citation,
            "attributes": dict(decision.attributes),
            "attribute_sources": dict(resolution.sources),
            "accessory_manifest": list(c.accessory_manifest),
        })
        self._emit("TierAssigned", {
            "item_id": item_id, "tier": decision.tier, "row_id": decision.row_id,
            "precedence": decision.precedence, "rationale": decision.rationale,
            "citation": decision.citation,
            "all_matching_rows": list(decision.all_matching_rows),
        })
        return CommandResult(
            "ListItem", (),
            (f"{c.model_name} -> {item_id}", f"classified Tier {decision.tier}"),
            (decision.explain(),),
        )

    def _reserve_item(self, c: cmd.ReserveItem) -> CommandResult:
        item = self._item(c.item_id)
        renter = self._user_by_handle(c.renter_handle)
        start_epoch, end_epoch = utc_to_epoch(c.window_start_utc), utc_to_epoch(c.window_end_utc)
        if end_epoch <= start_epoch:
            raise CommandRejected("rental window must be strictly positive")

        renter_trust = self.state.trust_of("user", renter["user_id"])
        tier = item["effective_tier"]
        duration = end_epoch - start_epoch
        # Integer day-rate maths: partial days round UP, which is the honest
        # reading of "a day rate", and keeps everything in integers.
        days = (duration + 86399) // 86400
        rent_cents = item["day_rate_cents"] * days

        # Risk flags BEFORE the reservation. A blocking flag refuses the command.
        flags = trust.evaluate_risk_flags({
            "id_verified": renter["id_verified"],
            "user_trust": renter_trust,
            "n_disputes_90d": renter["disputes_lifetime"],
            "overdue_returns_lifetime": renter["overdue_returns_lifetime"],
            "items_declared_lost_lifetime": renter["items_declared_lost_lifetime"],
            "value_band": insurance.value_band(item["replacement_value_cents"], self.ruleset),
        }, self.ruleset)
        for flag in flags:
            self._emit("RiskFlagRaised", {
                "subject_kind": "user", "subject_id": renter["user_id"],
                "flag_id": flag["flag_id"], "rule": flag["rule"],
                "severity": flag["severity"], "citation": flag["citation"],
            })
        blocking = [f["flag_id"] for f in flags if f["severity"] == "block"]
        if blocking:
            self._reproject()
            raise CommandRejected(
                f"reservation blocked by risk flag(s) {blocking} "
                f"({self.ruleset.citation('trust_weights')})"
            )

        transitions.evaluate_transition(
            "item", item["state"], "ItemReserved", self.ruleset,
            {"renter_id_verified": renter["id_verified"], "has_overlapping_reservation": False},
        )
        quote = insurance.quote_premium(
            item["replacement_value_cents"], tier, renter_trust, duration, self.ruleset)
        rental_id = content_id("rental", {
            "item_id": c.item_id, "renter_id": renter["user_id"],
            "window_start_utc": c.window_start_utc, "window_end_utc": c.window_end_utc,
        })
        self._emit("ItemReserved", {
            "rental_id": rental_id, "item_id": c.item_id, "renter_id": renter["user_id"],
            "owner_id": item["owner_id"], "tier": tier,
            "window_start_utc": c.window_start_utc, "window_end_utc": c.window_end_utc,
            "window_start_epoch": start_epoch, "window_end_epoch": end_epoch,
            "duration_seconds": duration, "rent_cents": rent_cents,
            "quoted_premium_cents": quote.premium_cents, "deposit_cents": quote.deposit_cents,
        })
        self._emit("InsuranceQuoted", {
            "rental_id": rental_id, "premium_cents": quote.premium_cents,
            "deposit_cents": quote.deposit_cents, "coverage_tier": quote.coverage_tier,
            "deductible_cents": quote.deductible_cents, "lookup_key": quote.lookup_key,
            "covers": list(quote.covers), "citation": quote.citation,
        })
        policy = self.insurer.bind(rental_id, quote)
        self._emit("InsuranceBound", {
            "rental_id": rental_id, "policy_ref": policy.policy_ref,
            "partner": policy.partner, "premium_cents": policy.premium_cents,
        })
        return CommandResult(
            "ReserveItem", (),
            (f"rental {rental_id}", f"{days} day(s), rent {rent_cents} cents",
             f"premium {quote.premium_cents} cents, deposit {quote.deposit_cents} cents",
             *(f"risk flag: {f['flag_id']} ({f['rule']})" for f in flags)),
            (quote.explain(),),
        )

    def _grant_access(self, c: cmd.GrantAccess) -> CommandResult:
        rental = self._rental(c.rental_id)
        item = self.state.items[rental["item_id"]]
        access_type = TIER_ACCESS_TYPE[rental["tier"]]

        if access_type == "meetup":
            transitions.evaluate_transition(
                "rental", rental["state"], "MeetupConfirmed", self.ruleset, self._context(rental))
            self._emit("MeetupConfirmed", {
                "rental_id": c.rental_id, "location_id": item["location_id"],
                "access_type": access_type, "meetup_utc": rental["window_start_utc"],
            })
            return CommandResult("GrantAccess", (), ("meetup confirmed; no credential issued",))

        transitions.evaluate_transition(
            "rental", rental["state"], "AccessGranted", self.ruleset, self._context(rental))
        credential = self.access.issue(
            c.rental_id, item["location_id"], access_type,
            rental["window_start_epoch"], rental["window_end_epoch"],
            rental["window_start_utc"], rental["window_end_utc"],
        )
        location = self.state.locations[item["location_id"]]
        self._emit("AccessGranted", {
            "rental_id": c.rental_id, "location_id": item["location_id"],
            "access_type": access_type, "pin": credential.secret,
            "derivation": credential.derivation,
            "valid_from_utc": credential.valid_from_utc,
            "valid_until_utc": credential.valid_until_utc,
            "spatial_instruction_id": location.get("spatial_instruction_id"),
        })
        return CommandResult(
            "GrantAccess", (),
            (f"{access_type} credential {credential.secret} valid "
             f"{credential.valid_from_utc} -> {credential.valid_until_utc}",
             f"derived from {credential.derivation}"),
        )

    def _submit_condition_report(self, c: cmd.SubmitConditionReport) -> CommandResult:
        rental = self._rental(c.rental_id)
        item = self.state.items[rental["item_id"]]
        submitter = self._user_by_handle(c.submitted_by_handle)
        tags = condition.validate_tags(c.damage_tags, self.ruleset)

        chain = self.state.chain_for(item["item_id"])
        previous = chain[-1] if chain else None
        report_id = content_id("condition_report", {
            "rental_id": c.rental_id, "phase": c.phase,
            "submitted_by": submitter["user_id"], "event_seq": self.log.next_seq,
        })
        photo_refs = [
            {"slot": slot, "photo_ref": self.photos.put(c.rental_id, slot, descriptor, self.clock.now_utc()).photo_ref}
            for slot, descriptor in sorted(c.photo_descriptors.items())
        ]
        manifest = (
            list(c.accessory_manifest) if c.accessory_manifest is not None
            else list(item["accessory_manifest"])
        )
        self._emit("ConditionReportSubmitted", {
            "report_id": report_id, "item_id": item["item_id"], "rental_id": c.rental_id,
            "phase": c.phase, "submitted_by": submitter["user_id"],
            "damage_tags": list(tags), "photo_slots": sorted(c.photo_descriptors),
            "photo_refs": photo_refs, "accessory_manifest": manifest,
            "prev_report_id": previous["report_id"] if previous else None,
        })
        self._trust_signal("user", submitter["user_id"], "ConditionReportSubmitted", report_id)
        self._trust_signal("item", item["item_id"], "ConditionReportSubmitted", report_id)

        previous_report = (
            condition.ConditionReport(
                report_id=previous["report_id"], item_id=previous["item_id"],
                rental_id=previous["rental_id"], phase=previous["phase"],
                submitted_by=previous["submitted_by"], submitted_at_utc=previous["submitted_at_utc"],
                event_seq=previous["event_seq"], damage_tags=tuple(previous["damage_tags"]),
                photo_slots=tuple(previous["photo_slots"]),
                accessory_manifest=tuple(previous["accessory_manifest"]),
            ) if previous else None
        )
        current_report = condition.ConditionReport(
            report_id=report_id, item_id=item["item_id"], rental_id=c.rental_id, phase=c.phase,
            submitted_by=submitter["user_id"], submitted_at_utc=self.clock.now_utc(),
            event_seq=self.log.next_seq, damage_tags=tags,
            photo_slots=tuple(sorted(c.photo_descriptors)), accessory_manifest=tuple(manifest),
            prev_report_id=previous["report_id"] if previous else None,
        )
        diff = condition.diff_condition(previous_report, current_report, self.ruleset)
        self._emit("ConditionDiffComputed", {
            "report_id": report_id, "item_id": item["item_id"],
            "prev_report_id": diff.prev_report_id,
            "appeared": [f.tag_id for f in diff.appeared],
            "confirmed": [f.tag_id for f in diff.confirmed],
            "disappeared": [f.tag_id for f in diff.disappeared],
            "blocking": list(diff.blocking),
            "missing_accessories": list(diff.missing_accessories),
            "deposit_hold_cents": diff.deposit_hold_cents,
            "requires_human": diff.requires_human,
            "citation": diff.citation,
        })
        # Only a report with a PREDECESSOR can show newly appeared damage. The
        # first entry in a chain establishes the baseline; penalising the item
        # for what it looked like on day one would make every listing start in
        # the hole.
        if previous is not None and diff.appeared:
            self._trust_signal("item", item["item_id"], "NewDamageAppeared", report_id)

        if c.countersigned_by_handles:
            signers = [self._user_by_handle(h)["user_id"] for h in c.countersigned_by_handles]
            self._emit("ConditionReportCountersigned", {
                "report_id": report_id, "signed_by": sorted(signers),
            })
            for signer in sorted(signers):
                self._trust_signal("user", signer, "ConditionReportCountersigned", report_id)

        notes = [f"report {report_id} ({c.phase}), {len(tags)} tag(s), {len(photo_refs)} photo(s)"]
        if diff.appeared:
            notes.append("NEW: " + ", ".join(f"{f.tag_id} [{f.severity}]" for f in diff.appeared))
        if diff.confirmed:
            notes.append("confirmed from previous renter: " + ", ".join(f.tag_id for f in diff.confirmed))
        if diff.disappeared:
            notes.append("CHAIN DISAGREEMENT, previously logged and now absent: "
                         + ", ".join(f.tag_id for f in diff.disappeared))
        if diff.missing_accessories:
            notes.append("MISSING: " + ", ".join(diff.missing_accessories))
        return CommandResult("SubmitConditionReport", (), tuple(notes), (diff.citation,))

    def _open_lockbox(self, c: cmd.OpenLockbox) -> CommandResult:
        rental = self._rental(c.rental_id)
        item = self.state.items[rental["item_id"]]
        access_type = TIER_ACCESS_TYPE[rental["tier"]]
        notes: list[str] = []

        if access_type != "meetup":
            credential = self.access.credential_for(c.rental_id)
            if credential is None:
                raise CommandRejected(f"no credential issued for rental {c.rental_id}")
            presented = c.presented_secret if c.presented_secret is not None else credential.secret
            accepted, reason = self.access.validate(
                c.rental_id, presented, self.clock.now_epoch(), self.clock.now_utc())
            self._emit("AccessCodeValidated", {
                "rental_id": c.rental_id, "location_id": item["location_id"],
                "qr_payload": __import__("rhe.l1_kernel.access", fromlist=["qr_payload"]).qr_payload(
                    c.rental_id, item["location_id"]),
                "validation_result": reason,
            })
            if not accepted:
                self._reproject()
                raise CommandRejected(f"access denied at the lockbox: {reason}")
            notes.append(f"credential accepted ({reason})")

        self._check(rental, "ItemPickedUp", actor="renter")
        self._emit("ItemPickedUp", {
            "rental_id": c.rental_id, "item_id": item["item_id"],
            "location_id": item["location_id"], "pin_used": access_type != "meetup",
            "access_result": "accepted",
        })
        notes.append("item collected")
        return CommandResult("OpenLockbox", (), tuple(notes))

    def _mark_overdue(self, c: cmd.MarkOverdue) -> CommandResult:
        rental = self._rental(c.rental_id)
        self._check(rental, "RentalMarkedOverdue", actor="system")
        self._emit("RentalMarkedOverdue", {
            "rental_id": c.rental_id, "item_id": rental["item_id"],
            "overdue_by_seconds": self.clock.now_epoch() - rental["window_end_epoch"],
        })
        self._trust_signal("user", rental["renter_id"], "RentalMarkedOverdue", c.rental_id)
        return CommandResult(
            "MarkOverdue", (),
            (f"overdue by {self.clock.now_epoch() - rental['window_end_epoch']} seconds",))

    def _return_item(self, c: cmd.ReturnItem) -> CommandResult:
        rental = self._rental(c.rental_id)
        self._check(rental, "ItemReturnInitiated", actor="renter")
        self._emit("ItemReturnInitiated", {
            "rental_id": c.rental_id, "item_id": rental["item_id"],
            "location_id": self.state.items[rental["item_id"]]["location_id"],
            "gps_confirmed": c.gps_confirmed,
        })
        late = self.clock.now_epoch() > rental["window_end_epoch"]
        self._trust_signal(
            "user", rental["renter_id"], "ReturnedLate" if late else "ReturnedOnTime", c.rental_id)
        if late:
            self._trust_signal("item", rental["item_id"], "ReturnedLate", c.rental_id)
        return CommandResult("ReturnItem", (), ("returned late" if late else "returned on time",))

    def _accept_return(self, c: cmd.AcceptReturn) -> CommandResult:
        rental = self._rental(c.rental_id)
        item = self.state.items[rental["item_id"]]
        self._check(rental, "ReturnAccepted", actor="system")

        post_report = self.state.condition_reports[rental["post_report_id"]]
        clean = not post_report.get("diff_appeared") and not post_report.get("diff_missing_accessories")

        self._emit("ReturnAccepted", {
            "rental_id": c.rental_id, "item_id": item["item_id"], "clean": clean,
        })
        if TIER_ACCESS_TYPE[rental["tier"]] != "meetup":
            self.access.revoke(c.rental_id, self.clock.now_utc())
            self._emit("AccessRevoked", {"rental_id": c.rental_id, "reason": "rental_closed"})

        settled = rental["rent_cents"] + rental["quoted_premium_cents"]
        self._emit("RentalClosed", {
            "rental_id": c.rental_id, "item_id": item["item_id"],
            "settled_cents": settled, "rent_cents": rental["rent_cents"],
            "premium_cents": rental["quoted_premium_cents"],
            "closed_at_epoch": self.clock.now_epoch(),
        })
        signal = "RentalClosedClean" if clean else "RentalClosedWithDamageWaived"
        self._trust_signal("user", rental["renter_id"], signal, c.rental_id)
        if clean:
            self._trust_signal("item", item["item_id"], "RentalClosedClean", c.rental_id)

        notes = [f"return accepted ({'clean' if clean else 'with findings'})",
                 f"settled {settled} cents"]
        decisions: list[str] = []

        # Graduation is evaluated on every clean close, from the log, never cached.
        self._reproject()
        item = self.state.items[item["item_id"]]
        graduation = trust.evaluate_graduation(
            item["classified_tier"],
            trust.ItemHistory(
                clean_handovers_consecutive=item["clean_handovers_consecutive"],
                disputes_lifetime=item["disputes_lifetime"],
                item_trust=self.state.trust_of("item", item["item_id"]),
                enclosable=item["attributes"]["enclosable"] == "true",
            ),
            self.ruleset,
        )
        if graduation.granted and item["effective_tier"] != graduation.to_tier:
            self._emit("TierGraduated", {
                "item_id": item["item_id"], "from_tier": graduation.from_tier,
                "to_tier": graduation.to_tier, "reason": graduation.reason,
                "citation": graduation.citation,
            })
            notes.append(
                f"TIER GRADUATION: {graduation.from_tier} -> {graduation.to_tier} ({graduation.reason})")
            decisions.append(f"graduated, because {graduation.citation}")
        elif not graduation.granted and graduation.unmet:
            notes.append("graduation progress: " + ", ".join(graduation.unmet))
        return CommandResult("AcceptReturn", (), tuple(notes), tuple(decisions))

    def _report_damage(self, c: cmd.ReportDamage) -> CommandResult:
        rental = self._rental(c.rental_id)
        reporter = self._user_by_handle(c.reported_by_handle)
        tags = condition.validate_tags(c.tags, self.ruleset)
        self._check(rental, "DamageReported", actor="owner")
        self._emit("DamageReported", {
            "rental_id": c.rental_id, "item_id": rental["item_id"],
            "reported_by": reporter["user_id"], "tags": list(tags),
        })
        self._trust_signal("user", rental["renter_id"], "DamageReportedAgainstRenter", c.rental_id)
        return CommandResult("ReportDamage", (), (f"damage claimed: {', '.join(tags)}",))

    def _waive_damage(self, c: cmd.WaiveDamage) -> CommandResult:
        rental = self._rental(c.rental_id)
        self._check(rental, "DamageWaived", actor="owner")
        waiver = self._user_by_handle(c.waived_by_handle)
        self._emit("DamageWaived", {
            "rental_id": c.rental_id, "item_id": rental["item_id"], "waived_by": waiver["user_id"],
        })
        settled = rental["rent_cents"] + rental["quoted_premium_cents"]
        self._emit("RentalClosed", {
            "rental_id": c.rental_id, "item_id": rental["item_id"], "settled_cents": settled,
            "rent_cents": rental["rent_cents"], "premium_cents": rental["quoted_premium_cents"],
            "closed_at_epoch": self.clock.now_epoch(),
        })
        self._trust_signal("user", rental["renter_id"], "RentalClosedWithDamageWaived", c.rental_id)
        return CommandResult("WaiveDamage", (), ("owner waived the claim", f"settled {settled} cents"))

    def _open_dispute(self, c: cmd.OpenDispute) -> CommandResult:
        rental = self._rental(c.rental_id)
        opener = self._user_by_handle(c.opened_by_handle)
        tags = condition.validate_tags(c.contested_tags, self.ruleset)
        self._check(rental, "DisputeOpened", actor="renter")
        dispute_id = content_id("dispute", {
            "rental_id": c.rental_id, "opened_by": opener["user_id"], "event_seq": self.log.next_seq,
        })
        order = self.ruleset.doc("precedence")["condition_disagreement"]["order"]
        self._emit("DisputeOpened", {
            "dispute_id": dispute_id, "rental_id": c.rental_id, "item_id": rental["item_id"],
            "opened_by": opener["user_id"], "contested_tags": list(tags),
            "routing_order": list(order), "routed_to": "human_resolution_queue",
        })
        self._trust_signal("user", rental["renter_id"], "DisputeOpenedAgainstRenter", dispute_id)
        self._trust_signal("item", rental["item_id"], "DisputeOpenedOnItem", dispute_id)
        return CommandResult(
            "OpenDispute", (),
            (f"dispute {dispute_id} opened over {', '.join(tags)}",
             "routed to a human; the system records and orders the claims, it does not decide",
             "presentation order: " + " > ".join(order)),
            (self.ruleset.citation("precedence"),),
        )

    def _resolve_dispute(self, c: cmd.ResolveDispute) -> CommandResult:
        if c.dispute_id not in self.state.disputes:
            raise CommandRejected(f"no such dispute: {c.dispute_id!r}")
        dispute = self.state.disputes[c.dispute_id]
        rental = self._rental(dispute["rental_id"])
        resolver = self._user_by_handle(c.resolved_by_handle)
        trigger = {"repair": "DisputeResolvedRepair", "no_fault": "DisputeResolvedNoFault"}.get(c.outcome)
        if trigger is None:
            raise CommandRejected(f"unknown dispute outcome {c.outcome!r}; use 'repair' or 'no_fault'")

        payload = {
            "dispute_id": c.dispute_id, "rental_id": rental["rental_id"],
            "item_id": rental["item_id"], "resolution": c.outcome,
            "resolved_by": resolver["user_id"],
        }
        # The guard reads resolution_recorded_by from the context; the resolver
        # is supplied by the command, which is the only way a human enters.
        context = dict(self._context(rental), resolution_recorded_by=resolver["user_id"])
        transitions.evaluate_transition("item", self.state.items[rental["item_id"]]["state"], trigger, self.ruleset, context)
        transitions.evaluate_transition("rental", rental["state"], trigger, self.ruleset, context)
        self._emit(trigger, payload)
        self._trust_signal(
            "user", rental["renter_id"],
            "DisputeResolvedAgainstRenter" if c.outcome == "repair" else "DisputeResolvedForRenter",
            c.dispute_id,
        )
        if c.outcome == "repair":
            self._emit("RepairScheduled", {"rental_id": rental["rental_id"], "item_id": rental["item_id"]})
        settled = rental["rent_cents"] + rental["quoted_premium_cents"]
        self._emit("RentalClosed", {
            "rental_id": rental["rental_id"], "item_id": rental["item_id"], "settled_cents": settled,
            "rent_cents": rental["rent_cents"], "premium_cents": rental["quoted_premium_cents"],
            "closed_at_epoch": self.clock.now_epoch(),
        })
        return CommandResult(
            "ResolveDispute", (),
            (f"resolved by {resolver['handle']} (human): {c.outcome}", f"settled {settled} cents"))

    def _declare_lost(self, c: cmd.DeclareLost) -> CommandResult:
        rental = self._rental(c.rental_id)
        self._check(rental, "ItemDeclaredLost", actor="system")
        self._emit("ItemDeclaredLost", {
            "rental_id": c.rental_id, "item_id": rental["item_id"],
            "deposit_forfeited_cents": rental["deposit_cents"],
            "claim_against_policy": rental.get("policy_ref"),
        })
        self._trust_signal("user", rental["renter_id"], "ItemDeclaredLost", c.rental_id)
        return CommandResult(
            "DeclareLost", (),
            (f"item written off; deposit {rental['deposit_cents']} cents forfeited",
             f"claim filed against policy {rental.get('policy_ref')}"))

    def _detect_purchase_opportunity(self, c: cmd.DetectPurchaseOpportunity) -> CommandResult:
        renter = self._user_by_handle(c.renter_handle)
        item = self._item(c.item_id)
        history = [
            upsell.CompletedRental(
                rental_id=r["rental_id"], item_id=r["item_id"],
                category_id=self.state.items[r["item_id"]]["category_id"],
                renter_id=r["renter_id"], closed_at_epoch=r["closed_at_epoch"],
                rent_paid_cents=r["rent_cents"],
            )
            for r in self.state.rentals_sorted()
            if r["state"] == "closed" and r["closed_at_epoch"] is not None
        ]
        opportunities = upsell.detect_upsell(
            renter_id=renter["user_id"], item_id=c.item_id, category_id=item["category_id"],
            purchase_price_cents=item["purchase_price_cents"], history=history,
            now_epoch=self.clock.now_epoch(),
            renter_trust=self.state.trust_of("user", renter["user_id"]), ruleset=self.ruleset,
        )
        notes: list[str] = []
        for opportunity in opportunities:
            offer_id = content_id("purchase_offer", {
                "renter_id": renter["user_id"], "item_id": c.item_id,
                "signal_id": opportunity.signal_id, "event_seq": self.log.next_seq,
            })
            self._emit("PurchaseOpportunityDetected", {
                "offer_id": offer_id, "renter_id": renter["user_id"], "item_id": c.item_id,
                "signal_id": opportunity.signal_id, "signal_rank": opportunity.signal_rank,
                "headline": opportunity.headline, "evidence": dict(opportunity.evidence),
                "purchase_price_cents": opportunity.purchase_price_cents,
                "cumulative_rental_cents": opportunity.cumulative_rental_cents,
                "financing_principal_cents": (
                    opportunity.financing.principal_cents if opportunity.financing else None),
                "financing_terms": (
                    {str(k): v for k, v in sorted(opportunity.financing.monthly_cents_by_term.items())}
                    if opportunity.financing else None),
                "purchase_conversion_eligible": opportunity.purchase_conversion_eligible,
                "blocked_reason": opportunity.blocked_reason,
                "citation": opportunity.citation,
            })
            notes.append(f"{opportunity.signal_id} (rank {opportunity.signal_rank}) -> {offer_id}")
        if not opportunities:
            notes.append("no upsell signal fired")
        return CommandResult(
            "DetectPurchaseOpportunity", (), tuple(notes),
            tuple(o.explain() for o in opportunities))

    def _accept_purchase_offer(self, c: cmd.AcceptPurchaseOffer) -> CommandResult:
        if c.offer_id not in self.state.purchase_offers:
            raise CommandRejected(f"no such purchase offer: {c.offer_id!r}")
        offer = self.state.purchase_offers[c.offer_id]
        if not offer["purchase_conversion_eligible"]:
            raise CommandRejected(f"offer not eligible: {offer['blocked_reason']}")
        item = self._item(offer["item_id"])

        financing = upsell.FinancingOffer(
            principal_cents=offer["financing_principal_cents"],
            terms_months=tuple(int(k) for k in sorted(offer["financing_terms"], key=int)),
            monthly_cents_by_term={int(k): v for k, v in offer["financing_terms"].items()},
            rent_credited_cents=min(offer["cumulative_rental_cents"], offer["purchase_price_cents"]),
        )
        approval = self.financier.request(c.offer_id, financing, c.term_months)
        self._emit("PurchaseOfferAccepted", {
            "offer_id": c.offer_id, "item_id": offer["item_id"], "buyer_id": offer["renter_id"],
            "approval_ref": approval.approval_ref, "partner": approval.partner,
            "principal_cents": approval.principal_cents, "term_months": approval.term_months,
            "monthly_cents": approval.monthly_cents,
        })
        self._reproject()
        context = dict(accepted_purchase_offer_id=c.offer_id)
        transitions.evaluate_transition(
            "item", self.state.items[offer["item_id"]]["state"], "ItemSold", self.ruleset, context)
        self._emit("ItemSold", {
            "item_id": offer["item_id"], "seller_id": item["owner_id"],
            "buyer_id": offer["renter_id"], "price_cents": offer["purchase_price_cents"],
            "rent_credited_cents": financing.rent_credited_cents,
            "financed_principal_cents": approval.principal_cents,
        })
        self._trust_signal("user", offer["renter_id"], "PurchaseCompleted", c.offer_id)
        return CommandResult(
            "AcceptPurchaseOffer", (),
            (f"financed {approval.principal_cents} cents over {approval.term_months} months "
             f"at {approval.monthly_cents} cents/month via {approval.partner}",
             f"{financing.rent_credited_cents} cents of rent credited against the price",
             f"ownership transferred to {offer['renter_id']}"))

    _HANDLERS = {
        "RegisterUser": _register_user,
        "RegisterLocation": _register_location,
        "RegisterPartnerNode": _register_partner_node,
        "ListItem": _list_item,
        "ReserveItem": _reserve_item,
        "GrantAccess": _grant_access,
        "SubmitConditionReport": _submit_condition_report,
        "OpenLockbox": _open_lockbox,
        "MarkOverdue": _mark_overdue,
        "ReturnItem": _return_item,
        "AcceptReturn": _accept_return,
        "ReportDamage": _report_damage,
        "WaiveDamage": _waive_damage,
        "OpenDispute": _open_dispute,
        "ResolveDispute": _resolve_dispute,
        "DeclareLost": _declare_lost,
        "DetectPurchaseOpportunity": _detect_purchase_opportunity,
        "AcceptPurchaseOffer": _accept_purchase_offer,
    }
