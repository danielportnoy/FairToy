from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


ImpactStatus = Literal[
    "unaffected",
    "potentially_affected",
    "affected",
]

UNAFFECTED: ImpactStatus = "unaffected"
POTENTIALLY_AFFECTED: ImpactStatus = "potentially_affected"
AFFECTED: ImpactStatus = "affected"


class ImpactInputError(ValueError):
    """Raised when traceability facts are inconsistent or incomplete."""


@dataclass(frozen=True)
class TraceabilityFact:
    """One row from a flat Toy/Part/Source repository query.

    A Part with no known possible sources is represented by a fact whose
    source fields are all ``None``. Source fields are otherwise required,
    except for the optional source unit cost.
    """

    toy_id: str
    toy_name: str
    part_id: str
    part_name: str
    quantity: int
    supplier_id: str | None = None
    supplier_name: str | None = None
    supplier_flagged: bool | None = None
    factory_id: str | None = None
    factory_name: str | None = None
    unit_cost_usd: Decimal | None = None


@dataclass(frozen=True)
class ImpactPath:
    """An explainable Toy → Part → Supplier → Factory path."""

    toy_id: str
    toy_name: str
    part_id: str
    part_name: str
    quantity: int
    supplier_id: str
    supplier_name: str
    supplier_flagged: bool
    factory_id: str
    factory_name: str
    unit_cost_usd: Decimal | None


@dataclass(frozen=True)
class PartImpact:
    part_id: str
    part_name: str
    quantity: int
    status: ImpactStatus
    reason: str
    paths: tuple[ImpactPath, ...]


@dataclass(frozen=True)
class ToyImpact:
    toy_id: str
    toy_name: str
    status: ImpactStatus
    reason: str
    parts: tuple[PartImpact, ...]


__all__ = [
    "AFFECTED",
    "POTENTIALLY_AFFECTED",
    "UNAFFECTED",
    "ImpactInputError",
    "ImpactPath",
    "ImpactStatus",
    "PartImpact",
    "ToyImpact",
    "TraceabilityFact",
]
