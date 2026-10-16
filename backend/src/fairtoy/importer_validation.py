from __future__ import annotations

from typing import Any, Callable, Iterable, TypeVar

from .importer_contracts import (
    ImportValidationError,
    SourceData,
)

_T = TypeVar("_T")


def _unique_records(
    records: Iterable[_T],
    *,
    key: Callable[[_T], Any],
    label: str,
) -> tuple[_T, ...]:
    records_by_key: dict[Any, _T] = {}
    for record in records:
        record_key = key(record)
        existing_record = records_by_key.get(record_key)
        if existing_record is None:
            records_by_key[record_key] = record
        elif existing_record != record:
            raise ImportValidationError(
                f"{getattr(record, 'location', label)}: {label} "
                f"{record_key!r} conflicts with "
                f"{getattr(existing_record, 'location', 'another row')}"
            )
    return tuple(records_by_key.values())


def normalize_source_data(source: SourceData) -> SourceData:
    """Deduplicate canonical entities and order every source collection."""

    finishers = _unique_records(
        source.finishers,
        key=lambda record: record.finisher_id,
        label="Finisher",
    )
    suppliers = _unique_records(
        source.suppliers,
        key=lambda record: record.supplier_id,
        label="Supplier",
    )
    factories = _unique_records(
        source.factories,
        key=lambda record: record.factory_id,
        label="Factory",
    )
    return SourceData(
        finishers=tuple(sorted(finishers, key=lambda record: record.finisher_id)),
        suppliers=tuple(sorted(suppliers, key=lambda record: record.supplier_id)),
        factories=tuple(sorted(factories, key=lambda record: record.factory_id)),
        toys=tuple(sorted(source.toys, key=lambda record: record.toy_id)),
        finisher_toys=tuple(
            sorted(
                source.finisher_toys,
                key=lambda record: (record.finisher_id, record.toy_id),
            )
        ),
        parts=tuple(sorted(source.parts, key=lambda record: record.part_id)),
        toy_parts=tuple(
            sorted(
                source.toy_parts,
                key=lambda record: (record.toy_id, record.part_id),
            )
        ),
        part_sources=tuple(
            sorted(
                source.part_sources,
                key=lambda record: (record.part_id, record.factory_id),
            )
        ),
    )


def _validate_references(source: SourceData) -> None:
    finisher_ids = {record.finisher_id for record in source.finishers}
    supplier_ids = {record.supplier_id for record in source.suppliers}
    factory_by_id = {record.factory_id: record for record in source.factories}
    toy_ids = {record.toy_id for record in source.toys}
    part_ids = {record.part_id for record in source.parts}

    for factory_record in source.factories:
        if factory_record.supplier_id not in supplier_ids:
            raise ImportValidationError(
                f"{factory_record.location}: factory {factory_record.factory_id!r} "
                f"references missing supplier {factory_record.supplier_id!r}"
            )

    for finisher_toy_record in source.finisher_toys:
        if finisher_toy_record.finisher_id not in finisher_ids:
            raise ImportValidationError(
                f"{finisher_toy_record.location}: FinisherToy "
                f"{finisher_toy_record.finisher_id, finisher_toy_record.toy_id!r} "
                f"references missing finisher {finisher_toy_record.finisher_id!r}"
            )
        if finisher_toy_record.toy_id not in toy_ids:
            raise ImportValidationError(
                f"{finisher_toy_record.location}: FinisherToy "
                f"{finisher_toy_record.finisher_id, finisher_toy_record.toy_id!r} "
                f"references missing toy {finisher_toy_record.toy_id!r}"
            )

    for part_source_record in source.part_sources:
        if part_source_record.part_id not in part_ids:
            raise ImportValidationError(
                f"{part_source_record.location}: PartSource "
                f"{part_source_record.part_id, part_source_record.factory_id!r} "
                f"references missing part {part_source_record.part_id!r}"
            )
        if part_source_record.supplier_id not in supplier_ids:
            raise ImportValidationError(
                f"{part_source_record.location}: PartSource "
                f"{part_source_record.part_id, part_source_record.factory_id!r} "
                f"references missing supplier {part_source_record.supplier_id!r}"
            )
        factory = factory_by_id.get(part_source_record.factory_id)
        if factory is None:
            raise ImportValidationError(
                f"{part_source_record.location}: PartSource "
                f"{part_source_record.part_id, part_source_record.factory_id!r} "
                f"references missing factory {part_source_record.factory_id!r}"
            )
        if factory.supplier_id != part_source_record.supplier_id:
            raise ImportValidationError(
                f"{part_source_record.location}: PartSource "
                f"{part_source_record.part_id, part_source_record.factory_id!r} "
                f"lists supplier {part_source_record.supplier_id!r}, but factory "
                f"{part_source_record.factory_id!r} belongs to "
                f"{factory.supplier_id!r}"
            )

    for toy_part_record in source.toy_parts:
        if toy_part_record.toy_id not in toy_ids:
            raise ImportValidationError(
                f"{toy_part_record.location}: ToyPart "
                f"{toy_part_record.toy_id, toy_part_record.part_id!r} "
                f"references missing toy {toy_part_record.toy_id!r}"
            )
        if toy_part_record.part_id not in part_ids:
            raise ImportValidationError(
                f"{toy_part_record.location}: ToyPart "
                f"{toy_part_record.toy_id, toy_part_record.part_id!r} "
                f"references missing part {toy_part_record.part_id!r}"
            )


def validate_source_data(source: SourceData) -> SourceData:
    """Normalize source records and validate all cross-file references."""

    normalized = normalize_source_data(source)
    _validate_references(normalized)
    return normalized


__all__ = ["normalize_source_data", "validate_source_data"]
