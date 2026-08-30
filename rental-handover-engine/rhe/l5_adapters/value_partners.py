"""L5 — Insurance and financing partner seams.

Neither is built. Both are shaped so the real thing drops in behind them:

  InsurancePartner -> Tint.ai. Embedded protection built for P2P platforms
      (self-storage, equipment rental, carsharing) with real-time per-transaction
      risk pricing. Our local rate table is what we quote and what a partner
      response gets reconciled against -- a partner that disagrees with our table
      is a signal about our table, which is only possible because ours is
      auditable in the first place.

  FinancingPartner -> Mondu. German B2B BNPL that lets a marketplace split BNPL
      fees between vendor and buyer, charge a markup, and split a purchase into
      3/6/12 monthly instalments. Our upsell engine decides WHEN to offer;
      Mondu decides the terms.

The fakes never call out. They echo the local, table-derived decision back with
a partner-shaped envelope, so the simulator shows the full round trip without a
socket ever opening.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from rhe.canonical import sha256_hex
from rhe.l1_kernel.insurance import InsuranceQuote
from rhe.l1_kernel.upsell import FinancingOffer


@dataclass(frozen=True)
class BoundPolicy:
    policy_ref: str
    premium_cents: int
    coverage_tier: str
    deductible_cents: int
    partner: str
    status: str


@dataclass(frozen=True)
class FinancingApproval:
    approval_ref: str
    principal_cents: int
    term_months: int
    monthly_cents: int
    partner: str
    status: str


class InsurancePartner(Protocol):
    def bind(self, rental_id: str, quote: InsuranceQuote) -> BoundPolicy: ...


class FinancingPartner(Protocol):
    def request(self, offer_id: str, financing: FinancingOffer, term_months: int) -> FinancingApproval: ...


class FakeInsurancePartner:
    """Tint-shaped. Binds whatever the local rate table quoted -- deliberately no
    partner-side repricing, so the simulator's numbers stay explainable."""

    name = "fake_tint"

    def __init__(self) -> None:
        self._policies: dict[str, BoundPolicy] = {}

    def bind(self, rental_id: str, quote: InsuranceQuote) -> BoundPolicy:
        policy = BoundPolicy(
            policy_ref=f"pol_{sha256_hex({'rental_id': rental_id, 'key': quote.lookup_key})[:12]}",
            premium_cents=quote.premium_cents,
            coverage_tier=quote.coverage_tier,
            deductible_cents=quote.deductible_cents,
            partner=self.name,
            status="bound",
        )
        self._policies[rental_id] = policy
        return policy

    def policy_for(self, rental_id: str) -> BoundPolicy | None:
        return self._policies.get(rental_id)


class FakeFinancingPartner:
    """Mondu-shaped. Approves the instalment plan the upsell engine computed."""

    name = "fake_mondu"

    def request(self, offer_id: str, financing: FinancingOffer, term_months: int) -> FinancingApproval:
        if term_months not in financing.terms_months:
            raise ValueError(
                f"term {term_months} not offered; available: {list(financing.terms_months)}"
            )
        return FinancingApproval(
            approval_ref=f"fin_{sha256_hex({'offer_id': offer_id, 'term': term_months})[:12]}",
            principal_cents=financing.principal_cents,
            term_months=term_months,
            monthly_cents=financing.monthly_cents_by_term[term_months],
            partner=self.name,
            status="approved",
        )
