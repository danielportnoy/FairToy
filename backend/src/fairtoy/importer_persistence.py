from __future__ import annotations

from typing import Any, TypeVar

from sqlalchemy.orm import Session

from .importer_contracts import ImportSummary, SourceData
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

_T = TypeVar("_T")


def _upsert(
    session: Session,
    model: type[_T],
    identity: Any,
    values: dict[str, Any],
) -> _T:
    instance = session.get(model, identity)
    if instance is None:
        instance = model(**values)
        session.add(instance)
    else:
        for field_name, value in values.items():
            setattr(instance, field_name, value)
    return instance


def persist_source_data(
    session: Session,
    source: SourceData,
) -> ImportSummary:
    """Atomically upsert normalized source data without resetting flags."""

    with session.begin():
        for finisher_record in source.finishers:
            _upsert(
                session,
                Finisher,
                finisher_record.finisher_id,
                {
                    "finisher_id": finisher_record.finisher_id,
                    "finisher_name": finisher_record.finisher_name,
                    "hq_country": finisher_record.hq_country,
                },
            )
        for supplier_record in source.suppliers:
            existing_supplier = session.get(
                Supplier,
                supplier_record.supplier_id,
            )
            if existing_supplier is None:
                session.add(
                    Supplier(
                        supplier_id=supplier_record.supplier_id,
                        supplier_name=supplier_record.supplier_name,
                        hq_country=supplier_record.hq_country,
                        child_labor_flagged=False,
                        flagged_at=None,
                    )
                )
            else:
                existing_supplier.supplier_name = supplier_record.supplier_name
                existing_supplier.hq_country = supplier_record.hq_country
        for factory_record in source.factories:
            _upsert(
                session,
                Factory,
                factory_record.factory_id,
                {
                    "factory_id": factory_record.factory_id,
                    "supplier_id": factory_record.supplier_id,
                    "factory_name": factory_record.factory_name,
                    "address_line": factory_record.address_line,
                    "city": factory_record.city,
                    "country": factory_record.country,
                },
            )
        for toy_record in source.toys:
            _upsert(
                session,
                Toy,
                toy_record.toy_id,
                {
                    "toy_id": toy_record.toy_id,
                    "toy_name": toy_record.toy_name,
                },
            )
        for part_record in source.parts:
            _upsert(
                session,
                Part,
                part_record.part_id,
                {
                    "part_id": part_record.part_id,
                    "part_name": part_record.part_name,
                },
            )

        session.flush()

        for finisher_toy_record in source.finisher_toys:
            _upsert(
                session,
                FinisherToy,
                (finisher_toy_record.finisher_id, finisher_toy_record.toy_id),
                {
                    "finisher_id": finisher_toy_record.finisher_id,
                    "toy_id": finisher_toy_record.toy_id,
                    "retail_price_usd": finisher_toy_record.retail_price_usd,
                    "units_per_year": finisher_toy_record.units_per_year,
                },
            )
        for toy_part_record in source.toy_parts:
            _upsert(
                session,
                ToyPart,
                (toy_part_record.toy_id, toy_part_record.part_id),
                {
                    "toy_id": toy_part_record.toy_id,
                    "part_id": toy_part_record.part_id,
                    "quantity": toy_part_record.quantity,
                },
            )
        for part_source_record in source.part_sources:
            _upsert(
                session,
                PartSource,
                (part_source_record.part_id, part_source_record.factory_id),
                {
                    "part_id": part_source_record.part_id,
                    "factory_id": part_source_record.factory_id,
                    "unit_cost_usd": part_source_record.unit_cost_usd,
                },
            )

    return ImportSummary(
        finishers=len(source.finishers),
        suppliers=len(source.suppliers),
        factories=len(source.factories),
        toys=len(source.toys),
        finisher_toys=len(source.finisher_toys),
        parts=len(source.parts),
        toy_parts=len(source.toy_parts),
        part_sources=len(source.part_sources),
    )


__all__ = ["persist_source_data"]
