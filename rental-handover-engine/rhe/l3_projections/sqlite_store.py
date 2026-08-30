"""L3 — The SQLite projection cache.

This database is a CACHE. Delete the file, replay the log, get it back exactly.
Nothing here is a source of truth, which is why every table is dropped and
rebuilt wholesale rather than incrementally updated: an UPDATE path is a place
for the cache to silently diverge from the log, so there isn't one.

Every entity table carries `event_seq`, `created_at_utc` and `ruleset_version`,
so any row can be traced back to the event and the rules that produced it.
"""
from __future__ import annotations

import pathlib
import sqlite3
from typing import Any

from rhe.canonical import canonical_json
from rhe.l0_rules.loader import Ruleset
from rhe.l3_projections.state import ProjectionState

SCHEMA = """
PRAGMA foreign_keys = ON;

-- The log itself, mirrored for queryability. Still append-only: the projection
-- rebuild TRUNCATES and re-inserts rather than updating a single row.
CREATE TABLE event_log (
    event_seq      INTEGER PRIMARY KEY,   -- monotonic, the system's ordering key
    event_type     TEXT    NOT NULL,
    payload_json   TEXT    NOT NULL,      -- canonical JSON, sorted keys
    clock_utc      TEXT    NOT NULL,      -- ISO 8601, second precision, UTC
    ruleset_hash   TEXT    NOT NULL,
    event_id       TEXT    NOT NULL       -- content hash of the whole event
);

CREATE TABLE users (
    user_id                      TEXT PRIMARY KEY,   -- content hash of (kind, handle, account_type)
    handle                       TEXT NOT NULL UNIQUE,
    display_name                 TEXT NOT NULL,
    account_type                 TEXT NOT NULL,      -- private | sole_trader | business | partner_staff
    id_verified                  INTEGER NOT NULL,   -- 0/1, never NULL
    trust_score                  INTEGER NOT NULL,   -- 0..1000, recomputed from the log
    trust_band                   TEXT    NOT NULL,
    overdue_returns_lifetime     INTEGER NOT NULL,
    items_declared_lost_lifetime INTEGER NOT NULL,
    disputes_lifetime            INTEGER NOT NULL,
    created_at_utc               TEXT NOT NULL,
    event_seq                    INTEGER NOT NULL,
    ruleset_version              INTEGER NOT NULL
);

CREATE TABLE locations (
    location_id     TEXT PRIMARY KEY,
    owner_id        TEXT NOT NULL REFERENCES users(user_id),
    label           TEXT NOT NULL,
    access_type     TEXT NOT NULL,   -- pin | gate_code | meetup | staffed | depot
    geo_cell        TEXT NOT NULL,   -- integer grid cell, never float coordinates
    lat_micro       INTEGER NOT NULL,
    lon_micro       INTEGER NOT NULL,
    spatial_instruction_id TEXT,     -- Tier 2: "third pallet, blue tarp"
    spatial_instruction    TEXT,
    landmark_photo_slot    TEXT,
    partner_node_id TEXT,
    created_at_utc  TEXT NOT NULL,
    event_seq       INTEGER NOT NULL,
    ruleset_version INTEGER NOT NULL
);

CREATE TABLE partner_nodes (
    partner_node_id TEXT PRIMARY KEY,
    operator_name   TEXT NOT NULL,
    node_type       TEXT NOT NULL,   -- hardware_store | workshop | repair_cafe | locker_bank
    geo_cell        TEXT NOT NULL,
    intake_fee_cents INTEGER NOT NULL,
    created_at_utc  TEXT NOT NULL,
    event_seq       INTEGER NOT NULL,
    ruleset_version INTEGER NOT NULL
);

CREATE TABLE items (
    item_id                   TEXT PRIMARY KEY,
    owner_id                  TEXT NOT NULL REFERENCES users(user_id),
    category_id               TEXT NOT NULL,
    model_name                TEXT NOT NULL,
    serial_number             TEXT NOT NULL,
    replacement_value_cents   INTEGER NOT NULL,   -- integer minor units, always
    purchase_price_cents      INTEGER NOT NULL,
    day_rate_cents            INTEGER NOT NULL,
    location_id               TEXT REFERENCES locations(location_id),
    partner_node_id           TEXT,
    state                     TEXT NOT NULL,      -- item lifecycle state
    classified_tier           INTEGER NOT NULL,   -- what tier_rules.yaml says
    effective_tier            INTEGER NOT NULL,   -- after graduation/demotion
    graduated                 INTEGER NOT NULL,
    tier_row_id               TEXT NOT NULL,      -- e.g. R07 -- the citation
    tier_citation             TEXT NOT NULL,
    attributes_json           TEXT NOT NULL,
    attribute_sources_json    TEXT NOT NULL,
    accessory_manifest_json   TEXT NOT NULL,
    clean_handovers_consecutive INTEGER NOT NULL,
    completed_rentals         INTEGER NOT NULL,
    disputes_lifetime         INTEGER NOT NULL,
    trust_score               INTEGER NOT NULL,
    created_at_utc            TEXT NOT NULL,
    event_seq                 INTEGER NOT NULL,
    ruleset_version           INTEGER NOT NULL
);

CREATE TABLE rentals (
    rental_id             TEXT PRIMARY KEY,
    item_id               TEXT NOT NULL REFERENCES items(item_id),
    renter_id             TEXT NOT NULL REFERENCES users(user_id),
    owner_id              TEXT NOT NULL REFERENCES users(user_id),
    tier                  INTEGER NOT NULL,
    state                 TEXT NOT NULL,
    window_start_utc      TEXT NOT NULL,
    window_end_utc        TEXT NOT NULL,
    window_start_epoch    INTEGER NOT NULL,
    window_end_epoch      INTEGER NOT NULL,
    duration_seconds      INTEGER NOT NULL,
    rent_cents            INTEGER NOT NULL,
    quoted_premium_cents  INTEGER NOT NULL,
    deposit_cents         INTEGER NOT NULL,
    coverage_tier         TEXT,
    insurance_status      TEXT NOT NULL,
    policy_ref            TEXT,
    pre_report_id         TEXT,
    post_report_id        TEXT,
    returned_late         INTEGER NOT NULL,
    settled_cents         INTEGER,
    closed_at_utc         TEXT,
    closed_at_epoch       INTEGER,
    opened_event_seq      INTEGER NOT NULL,
    ruleset_version       INTEGER NOT NULL
);

-- The condition chain. `prev_report_id` is what makes it a chain rather than a
-- pile of reports: every link names the link it confirms or contradicts.
CREATE TABLE condition_reports (
    report_id               TEXT PRIMARY KEY,
    item_id                 TEXT NOT NULL REFERENCES items(item_id),
    rental_id               TEXT REFERENCES rentals(rental_id),
    prev_report_id          TEXT REFERENCES condition_reports(report_id),
    phase                   TEXT NOT NULL,   -- pre | post | partner_intake | inspection
    submitted_by            TEXT NOT NULL,
    submitted_at_utc        TEXT NOT NULL,
    chain_index             INTEGER NOT NULL,
    damage_tags_json        TEXT NOT NULL,   -- closed taxonomy, canonical sort order
    photo_slots_json        TEXT NOT NULL,
    photo_refs_json         TEXT NOT NULL,   -- content-addressed evidence, never read
    accessory_manifest_json TEXT NOT NULL,
    countersigned_by_json   TEXT NOT NULL,
    diff_appeared_json      TEXT,
    diff_blocking_json      TEXT,
    deposit_hold_cents      INTEGER,
    event_seq               INTEGER NOT NULL,
    ruleset_version         INTEGER NOT NULL
);

CREATE TABLE access_grants (
    rental_id        TEXT PRIMARY KEY REFERENCES rentals(rental_id),
    location_id      TEXT NOT NULL,
    access_type      TEXT NOT NULL,
    secret           TEXT NOT NULL,   -- derived, never random
    derivation       TEXT NOT NULL,   -- the exact inputs that produced it
    valid_from_utc   TEXT NOT NULL,
    valid_until_utc  TEXT NOT NULL,
    revoked          INTEGER NOT NULL,
    event_seq        INTEGER NOT NULL,
    ruleset_version  INTEGER NOT NULL
);

CREATE TABLE purchase_offers (
    offer_id                     TEXT PRIMARY KEY,
    renter_id                    TEXT NOT NULL REFERENCES users(user_id),
    item_id                      TEXT NOT NULL REFERENCES items(item_id),
    signal_id                    TEXT NOT NULL,
    signal_rank                  INTEGER NOT NULL,
    state                        TEXT NOT NULL,
    purchase_price_cents         INTEGER NOT NULL,
    cumulative_rental_cents      INTEGER NOT NULL,
    financing_principal_cents    INTEGER,
    financing_terms_json         TEXT,
    purchase_conversion_eligible INTEGER NOT NULL,
    evidence_json                TEXT NOT NULL,
    citation                     TEXT NOT NULL,
    event_seq                    INTEGER NOT NULL,
    ruleset_version              INTEGER NOT NULL
);

CREATE TABLE disputes (
    dispute_id      TEXT PRIMARY KEY,
    rental_id       TEXT NOT NULL REFERENCES rentals(rental_id),
    item_id         TEXT NOT NULL REFERENCES items(item_id),
    opened_by       TEXT NOT NULL,
    state           TEXT NOT NULL,
    contested_tags_json TEXT NOT NULL,
    resolution      TEXT,
    resolved_by     TEXT,   -- ALWAYS a human. The system never adjudicates.
    opened_event_seq INTEGER NOT NULL,
    ruleset_version INTEGER NOT NULL
);

CREATE TABLE risk_flags (
    flag_row_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_kind    TEXT NOT NULL,
    subject_id      TEXT NOT NULL,
    flag_id         TEXT NOT NULL,
    rule            TEXT NOT NULL,   -- the literal rule text that fired
    severity        TEXT NOT NULL,
    citation        TEXT NOT NULL,
    event_seq       INTEGER NOT NULL
);

-- Provenance of the projection itself: which log, which rules, how far.
CREATE TABLE projection_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX idx_items_owner        ON items(owner_id, category_id, item_id);
CREATE INDEX idx_items_state        ON items(state);
CREATE INDEX idx_rentals_item       ON rentals(item_id, opened_event_seq);
CREATE INDEX idx_rentals_renter     ON rentals(renter_id, opened_event_seq);
CREATE INDEX idx_reports_item_chain ON condition_reports(item_id, chain_index);
CREATE INDEX idx_events_type        ON event_log(event_type, event_seq);
"""


def _j(value: Any) -> str:
    return canonical_json(value)


class SqliteProjectionStore:
    """Writes a ProjectionState into SQLite. Rebuild-only, never incremental."""

    def __init__(self, path: pathlib.Path | str = ":memory:") -> None:
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row

    def rebuild(self, state: ProjectionState, log_events: list[dict[str, Any]], ruleset: Ruleset) -> None:
        """Drop everything and re-derive. This is the only write path."""
        cursor = self.connection.cursor()
        for (name,) in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall():
            cursor.execute(f"DROP TABLE IF EXISTS {name}")
        cursor.executescript(SCHEMA)

        from rhe.canonical import sha256_hex
        from rhe.l1_kernel.trust import band_for_score

        version = ruleset.versions["state_transitions"]

        for e in log_events:
            cursor.execute(
                "INSERT INTO event_log VALUES (?,?,?,?,?,?)",
                (e["event_seq"], e["event_type"], _j(e["payload"]), e["clock_utc"],
                 e["ruleset_hash"], f"evt_{sha256_hex(e)[:12]}"),
            )

        for user_id in sorted(state.users):
            u = state.users[user_id]
            score = state.trust_of("user", user_id)
            cursor.execute(
                "INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (u["user_id"], u["handle"], u["display_name"], u["account_type"],
                 int(u["id_verified"]), score, band_for_score(score, ruleset),
                 u["overdue_returns_lifetime"], u["items_declared_lost_lifetime"],
                 u["disputes_lifetime"], u["created_at_utc"], u["event_seq"], version),
            )

        for node_id in sorted(state.partner_nodes):
            n = state.partner_nodes[node_id]
            cursor.execute(
                "INSERT INTO partner_nodes VALUES (?,?,?,?,?,?,?,?)",
                (n["partner_node_id"], n["operator_name"], n["node_type"], n["geo_cell"],
                 n["intake_fee_cents"], n["created_at_utc"], n["event_seq"], version),
            )

        for location_id in sorted(state.locations):
            loc = state.locations[location_id]
            cursor.execute(
                "INSERT INTO locations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (loc["location_id"], loc["owner_id"], loc["label"], loc["access_type"],
                 loc["geo_cell"], loc["lat_micro"], loc["lon_micro"],
                 loc.get("spatial_instruction_id"), loc.get("spatial_instruction"),
                 loc.get("landmark_photo_slot"), loc.get("partner_node_id"),
                 loc["created_at_utc"], loc["event_seq"], version),
            )

        for item_id in sorted(state.items):
            i = state.items[item_id]
            cursor.execute(
                "INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (i["item_id"], i["owner_id"], i["category_id"], i["model_name"], i["serial_number"],
                 i["replacement_value_cents"], i["purchase_price_cents"], i["day_rate_cents"],
                 i["location_id"], i.get("partner_node_id"), i["state"],
                 i["classified_tier"], i["effective_tier"], int(i["graduated"]),
                 i["tier_row_id"], i["tier_citation"], _j(i["attributes"]),
                 _j(i["attribute_sources"]), _j(i["accessory_manifest"]),
                 i["clean_handovers_consecutive"], i["completed_rentals"], i["disputes_lifetime"],
                 state.trust_of("item", item_id), i["created_at_utc"], i["event_seq"], version),
            )

        for rental_id in sorted(state.rentals):
            r = state.rentals[rental_id]
            cursor.execute(
                "INSERT INTO rentals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["rental_id"], r["item_id"], r["renter_id"], r["owner_id"], r["tier"], r["state"],
                 r["window_start_utc"], r["window_end_utc"], r["window_start_epoch"],
                 r["window_end_epoch"], r["duration_seconds"], r["rent_cents"],
                 r["quoted_premium_cents"], r["deposit_cents"], r.get("coverage_tier"),
                 r["insurance_status"], r.get("policy_ref"), r["pre_report_id"], r["post_report_id"],
                 int(r["returned_late"]), r["settled_cents"], r["closed_at_utc"],
                 r["closed_at_epoch"], r["opened_event_seq"], version),
            )

        for item_id in sorted(state.condition_chains):
            for chain_index, report_id in enumerate(state.condition_chains[item_id]):
                c = state.condition_reports[report_id]
                cursor.execute(
                    "INSERT INTO condition_reports VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (c["report_id"], c["item_id"], c["rental_id"], c["prev_report_id"], c["phase"],
                     c["submitted_by"], c["submitted_at_utc"], chain_index, _j(c["damage_tags"]),
                     _j(c["photo_slots"]), _j(c["photo_refs"]), _j(c["accessory_manifest"]),
                     _j(c["countersigned_by"]), _j(c.get("diff_appeared")), _j(c.get("diff_blocking")),
                     c.get("deposit_hold_cents"), c["event_seq"], version),
                )

        for rental_id in sorted(state.access_grants):
            g = state.access_grants[rental_id]
            cursor.execute(
                "INSERT INTO access_grants VALUES (?,?,?,?,?,?,?,?,?,?)",
                (g["rental_id"], g["location_id"], g["access_type"], g["pin"], g["derivation"],
                 g["valid_from_utc"], g["valid_until_utc"], int(g["revoked"]), g["event_seq"], version),
            )

        for offer_id in sorted(state.purchase_offers):
            o = state.purchase_offers[offer_id]
            cursor.execute(
                "INSERT INTO purchase_offers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (o["offer_id"], o["renter_id"], o["item_id"], o["signal_id"], o["signal_rank"],
                 o["state"], o["purchase_price_cents"], o["cumulative_rental_cents"],
                 o.get("financing_principal_cents"), _j(o.get("financing_terms")),
                 int(o["purchase_conversion_eligible"]), _j(o["evidence"]), o["citation"],
                 o["event_seq"], version),
            )

        for dispute_id in sorted(state.disputes):
            d = state.disputes[dispute_id]
            cursor.execute(
                "INSERT INTO disputes VALUES (?,?,?,?,?,?,?,?,?,?)",
                (d["dispute_id"], d["rental_id"], d["item_id"], d["opened_by"], d["state"],
                 _j(d["contested_tags"]), d.get("resolution"), d.get("resolved_by"),
                 d["opened_event_seq"], version),
            )

        for f in sorted(state.risk_flags, key=lambda f: (f["event_seq"], f["flag_id"])):
            cursor.execute(
                "INSERT INTO risk_flags (subject_kind, subject_id, flag_id, rule, severity, citation, event_seq)"
                " VALUES (?,?,?,?,?,?,?)",
                (f["subject_kind"], f["subject_id"], f["flag_id"], f["rule"], f["severity"],
                 f["citation"], f["event_seq"]),
            )

        for key, value in sorted({
            "ruleset_hash": ruleset.ruleset_hash,
            "events_applied": str(state.events_applied),
            "log_length": str(len(log_events)),
            "ruleset_versions": _j(dict(ruleset.versions)),
        }.items()):
            cursor.execute("INSERT INTO projection_meta VALUES (?,?)", (key, value))

        self.connection.commit()

    def fingerprint(self) -> str:
        """Content hash of every projected row, for the replay-equality test."""
        from rhe.canonical import sha256_hex
        cursor = self.connection.cursor()
        tables = [r[0] for r in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()]
        snapshot = {}
        for table in tables:
            columns = [c[1] for c in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
            order = ", ".join(columns)
            rows = cursor.execute(f"SELECT * FROM {table} ORDER BY {order}").fetchall()
            snapshot[table] = [[r[c] for c in columns] for r in rows]
        return sha256_hex(snapshot)

    def close(self) -> None:
        self.connection.close()
