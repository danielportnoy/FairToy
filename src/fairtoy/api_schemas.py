from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, StrictBool

from .impact import ImpactReasonCode


ImpactStatusValue = Literal[
    "unaffected",
    "potentially_affected",
    "affected",
]


class FinisherResponse(BaseModel):
    finisher_id: str
    finisher_name: str
    hq_country: str | None


class SupplierResponse(BaseModel):
    supplier_id: str
    supplier_name: str
    hq_country: str | None
    child_labor_flagged: bool
    flagged_at: datetime | None


class SupplierFlagUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    child_labor_flagged: StrictBool


class ImpactPathResponse(BaseModel):
    supplier_id: str
    supplier_name: str
    supplier_flagged: bool
    factory_id: str
    factory_name: str
    unit_cost_usd: str | None


class PartImpactResponse(BaseModel):
    part_id: str
    part_name: str
    quantity: int
    status: ImpactStatusValue
    reason_code: ImpactReasonCode
    reason: str
    paths: list[ImpactPathResponse]


class ToySummaryResponse(BaseModel):
    finisher_id: str
    toy_id: str
    toy_name: str
    status: ImpactStatusValue
    reason_code: ImpactReasonCode
    reason: str


class ToyDetailResponse(ToySummaryResponse):
    parts: list[PartImpactResponse]
