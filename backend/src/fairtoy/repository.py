from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .impact import ToyTraceability, TraceabilityFact
from .models import (
    Factory,
    Finisher,
    FinisherToy,
    Part,
    PartSource,
    Supplier,
    Toy,
    ToyPart,
)


@dataclass(frozen=True)
class FinisherSummary:
    finisher_id: str
    finisher_name: str
    hq_country: str | None


@dataclass(frozen=True)
class SupplierSummary:
    supplier_id: str
    supplier_name: str
    hq_country: str | None
    child_labor_flagged: bool
    flagged_at: datetime | None
    related_toy_count: int | None = None


@dataclass(frozen=True)
class SupplierFactorySummary:
    factory_id: str
    factory_name: str
    address_line: str | None
    city: str | None
    country: str | None


@dataclass(frozen=True)
class SupplierPartSummary:
    part_id: str
    part_name: str


@dataclass(frozen=True)
class SupplierDetailSummary:
    supplier_id: str
    supplier_name: str
    hq_country: str | None
    child_labor_flagged: bool
    flagged_at: datetime | None
    factories: tuple[SupplierFactorySummary, ...]
    supplied_parts: tuple[SupplierPartSummary, ...]


@dataclass
class _ToyAccumulator:
    finisher_id: str
    toy_id: str
    toy_name: str
    facts: list[TraceabilityFact]


class TraceabilityRepository:
    """Read Finisher-scoped traceability facts from the canonical store."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_finishers(self) -> tuple[FinisherSummary, ...]:
        rows = self._session.execute(
            select(
                Finisher.finisher_id,
                Finisher.finisher_name,
                Finisher.hq_country,
            ).order_by(Finisher.finisher_id)
        ).all()
        return tuple(
            FinisherSummary(
                finisher_id=row.finisher_id,
                finisher_name=row.finisher_name,
                hq_country=row.hq_country,
            )
            for row in rows
        )

    def get_finisher(self, finisher_id: str) -> FinisherSummary | None:
        self._validate_identifier(finisher_id, "finisher_id")
        result = self._session.execute(
            select(
                Finisher.finisher_id,
                Finisher.finisher_name,
                Finisher.hq_country,
            ).where(Finisher.finisher_id == finisher_id)
        ).first()
        if result is None:
            return None
        return FinisherSummary(
            finisher_id=result.finisher_id,
            finisher_name=result.finisher_name,
            hq_country=result.hq_country,
        )

    def list_suppliers(
        self,
        *,
        finisher_id: str | None = None,
    ) -> tuple[SupplierSummary, ...]:
        rows: Sequence[Any]
        if finisher_id is None:
            rows = self._session.execute(
                select(
                    Supplier.supplier_id,
                    Supplier.supplier_name,
                    Supplier.hq_country,
                    Supplier.child_labor_flagged,
                    Supplier.flagged_at,
                ).order_by(Supplier.supplier_id)
            ).all()
        else:
            self._validate_identifier(finisher_id, "finisher_id")
            supplier_columns = (
                Supplier.supplier_id,
                Supplier.supplier_name,
                Supplier.hq_country,
                Supplier.child_labor_flagged,
                Supplier.flagged_at,
            )
            rows = self._session.execute(
                select(
                    *supplier_columns,
                    func.count(func.distinct(Toy.toy_id)).label("related_toy_count"),
                )
                .select_from(Supplier)
                .join(Factory, Factory.supplier_id == Supplier.supplier_id)
                .join(PartSource, PartSource.factory_id == Factory.factory_id)
                .join(ToyPart, ToyPart.part_id == PartSource.part_id)
                .join(Toy, Toy.toy_id == ToyPart.toy_id)
                .join(FinisherToy, FinisherToy.toy_id == Toy.toy_id)
                .where(FinisherToy.finisher_id == finisher_id)
                .group_by(*supplier_columns)
                .order_by(Supplier.supplier_id)
            ).all()

        return tuple(
            SupplierSummary(
                supplier_id=row.supplier_id,
                supplier_name=row.supplier_name,
                hq_country=row.hq_country,
                child_labor_flagged=row.child_labor_flagged,
                flagged_at=row.flagged_at,
                related_toy_count=getattr(row, "related_toy_count", None),
            )
            for row in rows
        )

    def get_supplier_detail(
        self,
        supplier_id: str,
    ) -> SupplierDetailSummary | None:
        self._validate_identifier(supplier_id, "supplier_id")
        supplier_row = self._session.execute(
            select(
                Supplier.supplier_id,
                Supplier.supplier_name,
                Supplier.hq_country,
                Supplier.child_labor_flagged,
                Supplier.flagged_at,
            ).where(Supplier.supplier_id == supplier_id)
        ).first()
        if supplier_row is None:
            return None

        factory_rows = self._session.execute(
            select(
                Factory.factory_id,
                Factory.factory_name,
                Factory.address_line,
                Factory.city,
                Factory.country,
            )
            .where(Factory.supplier_id == supplier_id)
            .order_by(Factory.factory_id)
        ).all()
        part_rows = self._session.execute(
            select(Part.part_id, Part.part_name)
            .join(PartSource, PartSource.part_id == Part.part_id)
            .join(Factory, Factory.factory_id == PartSource.factory_id)
            .where(Factory.supplier_id == supplier_id)
            .distinct()
            .order_by(Part.part_id)
        ).all()

        return SupplierDetailSummary(
            supplier_id=supplier_row.supplier_id,
            supplier_name=supplier_row.supplier_name,
            hq_country=supplier_row.hq_country,
            child_labor_flagged=supplier_row.child_labor_flagged,
            flagged_at=supplier_row.flagged_at,
            factories=tuple(
                SupplierFactorySummary(
                    factory_id=row.factory_id,
                    factory_name=row.factory_name,
                    address_line=row.address_line,
                    city=row.city,
                    country=row.country,
                )
                for row in factory_rows
            ),
            supplied_parts=tuple(
                SupplierPartSummary(
                    part_id=row.part_id,
                    part_name=row.part_name,
                )
                for row in part_rows
            ),
        )

    def update_supplier_flag(
        self,
        *,
        supplier_id: str,
        child_labor_flagged: bool,
        now: datetime | None = None,
    ) -> SupplierSummary | None:
        """Set a Supplier's desired flag state and preserve its transition time."""

        self._validate_identifier(supplier_id, "supplier_id")
        if not isinstance(child_labor_flagged, bool):
            raise ValueError("child_labor_flagged must be a boolean")

        supplier = self._session.get(Supplier, supplier_id)
        if supplier is None:
            return None

        if child_labor_flagged:
            if not supplier.child_labor_flagged or supplier.flagged_at is None:
                supplier.flagged_at = now or datetime.now(timezone.utc)
            supplier.child_labor_flagged = True
        else:
            supplier.child_labor_flagged = False
            supplier.flagged_at = None

        self._session.flush()
        return SupplierSummary(
            supplier_id=supplier.supplier_id,
            supplier_name=supplier.supplier_name,
            hq_country=supplier.hq_country,
            child_labor_flagged=supplier.child_labor_flagged,
            flagged_at=supplier.flagged_at,
        )

    def list_toy_traceability(
        self,
        *,
        finisher_id: str,
    ) -> tuple[ToyTraceability, ...]:
        """Return all catalog Toys for a Finisher in deterministic order."""

        self._validate_identifier(finisher_id, "finisher_id")
        rows = self._execute_traceability_query(finisher_id=finisher_id)
        return self._map_rows(rows)

    def get_toy_traceability(
        self,
        *,
        finisher_id: str,
        toy_id: str,
    ) -> ToyTraceability | None:
        """Return one catalog Toy, or ``None`` when it is not in the catalog."""

        self._validate_identifier(finisher_id, "finisher_id")
        self._validate_identifier(toy_id, "toy_id")
        rows = self._execute_traceability_query(
            finisher_id=finisher_id,
            toy_id=toy_id,
        )
        traceability = self._map_rows(rows)
        return traceability[0] if traceability else None

    def _execute_traceability_query(
        self,
        *,
        finisher_id: str,
        toy_id: str | None = None,
    ) -> list[dict[str, Any]]:
        statement = (
            select(
                FinisherToy.finisher_id.label("finisher_id"),
                Toy.toy_id.label("toy_id"),
                Toy.toy_name.label("toy_name"),
                Part.part_id.label("part_id"),
                Part.part_name.label("part_name"),
                ToyPart.quantity.label("quantity"),
                Supplier.supplier_id.label("supplier_id"),
                Supplier.supplier_name.label("supplier_name"),
                Supplier.child_labor_flagged.label("supplier_flagged"),
                Factory.factory_id.label("factory_id"),
                Factory.factory_name.label("factory_name"),
                PartSource.unit_cost_usd.label("unit_cost_usd"),
            )
            .select_from(FinisherToy)
            .join(Toy, FinisherToy.toy_id == Toy.toy_id)
            .outerjoin(ToyPart, ToyPart.toy_id == Toy.toy_id)
            .outerjoin(Part, ToyPart.part_id == Part.part_id)
            .outerjoin(PartSource, PartSource.part_id == Part.part_id)
            .outerjoin(Factory, PartSource.factory_id == Factory.factory_id)
            .outerjoin(Supplier, Factory.supplier_id == Supplier.supplier_id)
            .where(FinisherToy.finisher_id == finisher_id)
            .order_by(
                Toy.toy_id,
                Part.part_id,
                Factory.factory_id,
                Supplier.supplier_id,
            )
        )
        if toy_id is not None:
            statement = statement.where(Toy.toy_id == toy_id)

        return [dict(row) for row in self._session.execute(statement).mappings().all()]

    @staticmethod
    def _map_rows(
        rows: list[dict[str, Any]],
    ) -> tuple[ToyTraceability, ...]:
        grouped: dict[tuple[str, str], _ToyAccumulator] = {}
        for row in rows:
            key = (row["finisher_id"], row["toy_id"])
            accumulator = grouped.get(key)
            if accumulator is None:
                accumulator = _ToyAccumulator(
                    finisher_id=row["finisher_id"],
                    toy_id=row["toy_id"],
                    toy_name=row["toy_name"],
                    facts=[],
                )
                grouped[key] = accumulator
            elif accumulator.toy_name != row["toy_name"]:
                raise ValueError(f"toy_id {row['toy_id']!r} has conflicting names")

            fact = TraceabilityRepository._fact_from_row(row)
            if fact is not None:
                accumulator.facts.append(fact)

        return tuple(
            ToyTraceability(
                finisher_id=accumulator.finisher_id,
                toy_id=accumulator.toy_id,
                toy_name=accumulator.toy_name,
                facts=tuple(accumulator.facts),
            )
            for key, accumulator in sorted(grouped.items())
        )

    @staticmethod
    def _fact_from_row(
        row: dict[str, Any],
    ) -> TraceabilityFact | None:
        if row["part_id"] is None:
            return None
        return TraceabilityFact(
            toy_id=row["toy_id"],
            toy_name=row["toy_name"],
            part_id=row["part_id"],
            part_name=row["part_name"],
            quantity=row["quantity"],
            supplier_id=row["supplier_id"],
            supplier_name=row["supplier_name"],
            supplier_flagged=row["supplier_flagged"],
            factory_id=row["factory_id"],
            factory_name=row["factory_name"],
            unit_cost_usd=row["unit_cost_usd"],
        )

    @staticmethod
    def _validate_identifier(value: str, field_name: str) -> None:
        if not value.strip():
            raise ValueError(f"{field_name} is required")
