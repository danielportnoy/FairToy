from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


ImpactStatus = Literal[
    "unaffected",
    "potentially_affected",
    "affected",
]

ImpactReasonCode = Literal[
    "toy_unaffected",
    "toy_potentially_affected",
    "toy_affected",
    "part_no_known_sources",
    "part_no_flagged_sources",
    "part_all_sources_flagged",
    "part_mixed_source_flags",
]

UNAFFECTED: ImpactStatus = "unaffected"
POTENTIALLY_AFFECTED: ImpactStatus = "potentially_affected"
AFFECTED: ImpactStatus = "affected"

TOY_UNAFFECTED_REASON_CODE: ImpactReasonCode = "toy_unaffected"
TOY_POTENTIALLY_AFFECTED_REASON_CODE: ImpactReasonCode = (
    "toy_potentially_affected"
)
TOY_AFFECTED_REASON_CODE: ImpactReasonCode = "toy_affected"
PART_NO_KNOWN_SOURCES_REASON_CODE: ImpactReasonCode = "part_no_known_sources"
PART_NO_FLAGGED_SOURCES_REASON_CODE: ImpactReasonCode = (
    "part_no_flagged_sources"
)
PART_ALL_SOURCES_FLAGGED_REASON_CODE: ImpactReasonCode = (
    "part_all_sources_flagged"
)
PART_MIXED_SOURCE_FLAGS_REASON_CODE: ImpactReasonCode = (
    "part_mixed_source_flags"
)


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
class ToyTraceability:
    """Finisher-scoped Toy context plus its possible source facts.

    ``facts`` may be empty when the canonical Toy has no BOM rows. The
    Finisher context is retained here for catalog filtering, while impact
    classification remains global at the Toy level.
    """

    finisher_id: str
    toy_id: str
    toy_name: str
    facts: tuple[TraceabilityFact, ...]


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
    reason_code: ImpactReasonCode
    reason: str
    paths: tuple[ImpactPath, ...]


@dataclass(frozen=True)
class ToyImpact:
    toy_id: str
    toy_name: str
    status: ImpactStatus
    reason_code: ImpactReasonCode
    reason: str
    parts: tuple[PartImpact, ...]


__all__ = [
    "AFFECTED",
    "POTENTIALLY_AFFECTED",
    "UNAFFECTED",
    "ImpactReasonCode",
    "ImpactInputError",
    "ImpactPath",
    "ImpactStatus",
    "PartImpact",
    "ToyTraceability",
    "ToyImpact",
    "TraceabilityFact",
]
