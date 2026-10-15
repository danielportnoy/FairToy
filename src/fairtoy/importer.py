from __future__ import annotations

import csv
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Iterable, TypeVar

from sqlalchemy.orm import Session

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


class ImportValidationError(ValueError):
    """Raised when fixture data cannot be mapped to the canonical model."""


@dataclass(frozen=True)
class FixturePaths:
    finishers: Path
    suppliers: Path
    factories: Path
    parts: Path
    toys: Path
    bill_of_materials: Path

    @classmethod
    def from_directory(cls, data_dir: str | Path) -> "FixturePaths":
        directory = Path(data_dir)
        return cls(
            finishers=directory / "finishers.csv",
            suppliers=directory / "suppliers.csv",
            factories=directory / "factories.csv",
            parts=directory / "parts.csv",
            toys=directory / "toys.csv",
            bill_of_materials=directory / "bill_of_materials.csv",
        )


@dataclass(frozen=True)
class FinisherRecord:
    finisher_id: str
    finisher_name: str
    hq_country: str | None
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class SupplierRecord:
    supplier_id: str
    supplier_name: str
    hq_country: str | None
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class FactoryRecord:
    factory_id: str
    supplier_id: str
    factory_name: str
    address_line: str | None
    city: str | None
    country: str | None
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class ToyRecord:
    toy_id: str
    toy_name: str
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class FinisherToyRecord:
    finisher_id: str
    toy_id: str
    retail_price_usd: Decimal | None
    units_per_year: int | None
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class PartRecord:
    part_id: str
    part_name: str
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class PartSourceRecord:
    part_id: str
    supplier_id: str
    factory_id: str
    unit_cost_usd: Decimal | None
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class ToyPartRecord:
    toy_id: str
    part_id: str
    quantity: int
    location: str = field(compare=False, repr=False)


@dataclass(frozen=True)
class SourceData:
    finishers: tuple[FinisherRecord, ...]
    suppliers: tuple[SupplierRecord, ...]
    factories: tuple[FactoryRecord, ...]
    toys: tuple[ToyRecord, ...]
    finisher_toys: tuple[FinisherToyRecord, ...]
    parts: tuple[PartRecord, ...]
    toy_parts: tuple[ToyPartRecord, ...]
    part_sources: tuple[PartSourceRecord, ...]


@dataclass(frozen=True)
class ImportSummary:
    finishers: int
    suppliers: int
    factories: int
    toys: int
    finisher_toys: int
    parts: int
    toy_parts: int
    part_sources: int


_T = TypeVar("_T")

_EXPECTED_HEADERS: dict[str, tuple[str, ...]] = {
    "finishers.csv": ("finisher_id", "finisher_name", "hq_country"),
    "suppliers.csv": ("supplier_id", "supplier_name", "hq_country"),
    "factories.csv": (
        "factory_id",
        "supplier_id",
        "factory_name",
        "address_line",
        "city",
        "country",
    ),
    "parts.csv": (
        "part_id",
        "part_name",
        "supplier_id",
        "factory_id",
        "unit_cost_usd",
    ),
    "toys.csv": (
        "toy_id",
        "toy_name",
        "finisher_id",
        "retail_price_usd",
        "units_per_year",
    ),
    "bill_of_materials.csv": ("toy_id", "part_id", "quantity"),
}


def _read_rows(
    path: Path,
    expected_headers: tuple[str, ...],
) -> Iterable[tuple[int, dict[str, str]]]:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except FileNotFoundError as exc:
        raise ImportValidationError(
            f"Missing required fixture file: {path}"
        ) from exc

    with handle:
        reader = csv.DictReader(handle)
        actual_headers = tuple(reader.fieldnames or ())
        if actual_headers != expected_headers:
            raise ImportValidationError(
                f"{path}: expected CSV headers {expected_headers}, "
                f"found {actual_headers}"
            )

        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if None in row:
                raise ImportValidationError(
                    f"{path}:{line_number}: too many CSV values"
                )
            if any(value is None for value in row.values()):
                raise ImportValidationError(
                    f"{path}:{line_number}: too few CSV values"
                )
            if all(not value.strip() for value in row.values()):
                continue
            yield line_number, row


def _location(path: Path, line_number: int) -> str:
    return f"{path}:{line_number}"


def _required(
    row: dict[str, str],
    field_name: str,
    *,
    path: Path,
    line_number: int,
) -> str:
    value = row[field_name].strip()
    if not value:
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} is required"
        )
    return value


def _optional(row: dict[str, str], field_name: str) -> str | None:
    value = row[field_name].strip()
    return value or None


def _parse_decimal(
    row: dict[str, str],
    field_name: str,
    *,
    path: Path,
    line_number: int,
    required: bool = False,
) -> Decimal | None:
    raw_value = (
        _required(row, field_name, path=path, line_number=line_number)
        if required
        else _optional(row, field_name)
    )
    if raw_value is None:
        return None
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} must be a number, "
            f"found {raw_value!r}"
        ) from exc
    if not value.is_finite():
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} must be finite"
        )
    if value < 0:
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} must be non-negative"
        )
    return value


def _parse_integer(
    row: dict[str, str],
    field_name: str,
    *,
    path: Path,
    line_number: int,
    required: bool = False,
) -> int | None:
    raw_value = (
        _required(row, field_name, path=path, line_number=line_number)
        if required
        else _optional(row, field_name)
    )
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} must be an integer, "
            f"found {raw_value!r}"
        ) from exc
    if value < 0:
        raise ImportValidationError(
            f"{path}:{line_number}: {field_name} must be non-negative"
        )
    return value


def _parse_finishers(path: Path) -> tuple[FinisherRecord, ...]:
    records = []
    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["finishers.csv"],
    ):
        records.append(
            FinisherRecord(
                finisher_id=_required(
                    row,
                    "finisher_id",
                    path=path,
                    line_number=line_number,
                ),
                finisher_name=_required(
                    row,
                    "finisher_name",
                    path=path,
                    line_number=line_number,
                ),
                hq_country=_optional(row, "hq_country"),
                location=_location(path, line_number),
            )
        )
    return tuple(records)


def _parse_suppliers(path: Path) -> tuple[SupplierRecord, ...]:
    records = []
    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["suppliers.csv"],
    ):
        records.append(
            SupplierRecord(
                supplier_id=_required(
                    row,
                    "supplier_id",
                    path=path,
                    line_number=line_number,
                ),
                supplier_name=_required(
                    row,
                    "supplier_name",
                    path=path,
                    line_number=line_number,
                ),
                hq_country=_optional(row, "hq_country"),
                location=_location(path, line_number),
            )
        )
    return tuple(records)


def _parse_factories(path: Path) -> tuple[FactoryRecord, ...]:
    records = []
    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["factories.csv"],
    ):
        records.append(
            FactoryRecord(
                factory_id=_required(
                    row,
                    "factory_id",
                    path=path,
                    line_number=line_number,
                ),
                supplier_id=_required(
                    row,
                    "supplier_id",
                    path=path,
                    line_number=line_number,
                ),
                factory_name=_required(
                    row,
                    "factory_name",
                    path=path,
                    line_number=line_number,
                ),
                address_line=_optional(row, "address_line"),
                city=_optional(row, "city"),
                country=_optional(row, "country"),
                location=_location(path, line_number),
            )
        )
    return tuple(records)


def _parse_toys(
    path: Path,
) -> tuple[tuple[ToyRecord, ...], tuple[FinisherToyRecord, ...]]:
    toys_by_id: dict[str, ToyRecord] = {}
    finisher_toys_by_key: dict[tuple[str, str], FinisherToyRecord] = {}

    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["toys.csv"],
    ):
        location = _location(path, line_number)
        toy = ToyRecord(
            toy_id=_required(
                row,
                "toy_id",
                path=path,
                line_number=line_number,
            ),
            toy_name=_required(
                row,
                "toy_name",
                path=path,
                line_number=line_number,
            ),
            location=location,
        )
        existing_toy = toys_by_id.get(toy.toy_id)
        if existing_toy is None:
            toys_by_id[toy.toy_id] = toy
        elif existing_toy != toy:
            raise ImportValidationError(
                f"{location}: toy_id {toy.toy_id!r} conflicts with "
                f"{existing_toy.location}"
            )

        finisher_toy = FinisherToyRecord(
            finisher_id=_required(
                row,
                "finisher_id",
                path=path,
                line_number=line_number,
            ),
            toy_id=toy.toy_id,
            retail_price_usd=_parse_decimal(
                row,
                "retail_price_usd",
                path=path,
                line_number=line_number,
            ),
            units_per_year=_parse_integer(
                row,
                "units_per_year",
                path=path,
                line_number=line_number,
            ),
            location=location,
        )
        key = (finisher_toy.finisher_id, finisher_toy.toy_id)
        existing_relationship = finisher_toys_by_key.get(key)
        if existing_relationship is None:
            finisher_toys_by_key[key] = finisher_toy
        elif existing_relationship != finisher_toy:
            raise ImportValidationError(
                f"{location}: FinisherToy {key!r} conflicts with "
                f"{existing_relationship.location}"
            )

    return (
        tuple(sorted(toys_by_id.values(), key=lambda record: record.toy_id)),
        tuple(
            sorted(
                finisher_toys_by_key.values(),
                key=lambda record: (record.finisher_id, record.toy_id),
            )
        ),
    )


def _parse_parts(
    path: Path,
) -> tuple[tuple[PartRecord, ...], tuple[PartSourceRecord, ...]]:
    parts_by_id: dict[str, PartRecord] = {}
    part_sources_by_key: dict[tuple[str, str], PartSourceRecord] = {}

    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["parts.csv"],
    ):
        location = _location(path, line_number)
        part = PartRecord(
            part_id=_required(
                row,
                "part_id",
                path=path,
                line_number=line_number,
            ),
            part_name=_required(
                row,
                "part_name",
                path=path,
                line_number=line_number,
            ),
            location=location,
        )
        existing_part = parts_by_id.get(part.part_id)
        if existing_part is None:
            parts_by_id[part.part_id] = part
        elif existing_part != part:
            raise ImportValidationError(
                f"{location}: part_id {part.part_id!r} conflicts with "
                f"{existing_part.location}"
            )

        part_source = PartSourceRecord(
            part_id=part.part_id,
            supplier_id=_required(
                row,
                "supplier_id",
                path=path,
                line_number=line_number,
            ),
            factory_id=_required(
                row,
                "factory_id",
                path=path,
                line_number=line_number,
            ),
            unit_cost_usd=_parse_decimal(
                row,
                "unit_cost_usd",
                path=path,
                line_number=line_number,
            ),
            location=location,
        )
        key = (part_source.part_id, part_source.factory_id)
        existing_source = part_sources_by_key.get(key)
        if existing_source is None:
            part_sources_by_key[key] = part_source
        elif existing_source != part_source:
            raise ImportValidationError(
                f"{location}: PartSource {key!r} conflicts with "
                f"{existing_source.location}"
            )

    return (
        tuple(sorted(parts_by_id.values(), key=lambda record: record.part_id)),
        tuple(
            sorted(
                part_sources_by_key.values(),
                key=lambda record: (record.part_id, record.factory_id),
            )
        ),
    )


def _parse_bill_of_materials(path: Path) -> tuple[ToyPartRecord, ...]:
    records_by_key: dict[tuple[str, str], ToyPartRecord] = {}
    for line_number, row in _read_rows(
        path,
        _EXPECTED_HEADERS["bill_of_materials.csv"],
    ):
        location = _location(path, line_number)
        record = ToyPartRecord(
            toy_id=_required(
                row,
                "toy_id",
                path=path,
                line_number=line_number,
            ),
            part_id=_required(
                row,
                "part_id",
                path=path,
                line_number=line_number,
            ),
            quantity=_parse_integer(
                row,
                "quantity",
                path=path,
                line_number=line_number,
                required=True,
            )
            or 0,
            location=location,
        )
        key = (record.toy_id, record.part_id)
        existing_record = records_by_key.get(key)
        if existing_record is None:
            records_by_key[key] = record
        elif existing_record != record:
            raise ImportValidationError(
                f"{location}: ToyPart {key!r} conflicts with "
                f"{existing_record.location}"
            )
    return tuple(
        sorted(
            records_by_key.values(),
            key=lambda record: (record.toy_id, record.part_id),
        )
    )


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


def _validate_references(source: SourceData) -> None:
    finisher_ids = {record.finisher_id for record in source.finishers}
    supplier_ids = {record.supplier_id for record in source.suppliers}
    factory_by_id = {
        record.factory_id: record for record in source.factories
    }
    toy_ids = {record.toy_id for record in source.toys}
    part_ids = {record.part_id for record in source.parts}

    for record in source.factories:
        if record.supplier_id not in supplier_ids:
            raise ImportValidationError(
                f"{record.location}: factory {record.factory_id!r} "
                f"references missing supplier {record.supplier_id!r}"
            )

    for record in source.finisher_toys:
        if record.finisher_id not in finisher_ids:
            raise ImportValidationError(
                f"{record.location}: FinisherToy {record.finisher_id, record.toy_id!r} "
                f"references missing finisher {record.finisher_id!r}"
            )
        if record.toy_id not in toy_ids:
            raise ImportValidationError(
                f"{record.location}: FinisherToy {record.finisher_id, record.toy_id!r} "
                f"references missing toy {record.toy_id!r}"
            )

    for record in source.part_sources:
        if record.part_id not in part_ids:
            raise ImportValidationError(
                f"{record.location}: PartSource {record.part_id, record.factory_id!r} "
                f"references missing part {record.part_id!r}"
            )
        if record.supplier_id not in supplier_ids:
            raise ImportValidationError(
                f"{record.location}: PartSource {record.part_id, record.factory_id!r} "
                f"references missing supplier {record.supplier_id!r}"
            )
        factory = factory_by_id.get(record.factory_id)
        if factory is None:
            raise ImportValidationError(
                f"{record.location}: PartSource {record.part_id, record.factory_id!r} "
                f"references missing factory {record.factory_id!r}"
            )
        if factory.supplier_id != record.supplier_id:
            raise ImportValidationError(
                f"{record.location}: PartSource {record.part_id, record.factory_id!r} "
                f"lists supplier {record.supplier_id!r}, but factory "
                f"{record.factory_id!r} belongs to {factory.supplier_id!r}"
            )

    for record in source.toy_parts:
        if record.toy_id not in toy_ids:
            raise ImportValidationError(
                f"{record.location}: ToyPart {record.toy_id, record.part_id!r} "
                f"references missing toy {record.toy_id!r}"
            )
        if record.part_id not in part_ids:
            raise ImportValidationError(
                f"{record.location}: ToyPart {record.toy_id, record.part_id!r} "
                f"references missing part {record.part_id!r}"
            )


def read_source_data(data_dir: str | Path) -> SourceData:
    """Read, normalize, deduplicate, and validate all six fixture files."""

    paths = FixturePaths.from_directory(data_dir)
    finishers = _unique_records(
        _parse_finishers(paths.finishers),
        key=lambda record: record.finisher_id,
        label="Finisher",
    )
    suppliers = _unique_records(
        _parse_suppliers(paths.suppliers),
        key=lambda record: record.supplier_id,
        label="Supplier",
    )
    factories = _unique_records(
        _parse_factories(paths.factories),
        key=lambda record: record.factory_id,
        label="Factory",
    )
    toys, finisher_toys = _parse_toys(paths.toys)
    parts, part_sources = _parse_parts(paths.parts)
    toy_parts = _parse_bill_of_materials(paths.bill_of_materials)

    source = SourceData(
        finishers=tuple(
            sorted(finishers, key=lambda record: record.finisher_id)
        ),
        suppliers=tuple(
            sorted(suppliers, key=lambda record: record.supplier_id)
        ),
        factories=tuple(
            sorted(factories, key=lambda record: record.factory_id)
        ),
        toys=toys,
        finisher_toys=finisher_toys,
        parts=parts,
        toy_parts=toy_parts,
        part_sources=part_sources,
    )
    _validate_references(source)
    return source


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


def import_fixtures(
    session: Session,
    data_dir: str | Path,
) -> ImportSummary:
    """Atomically upsert validated fixtures without resetting Supplier flags."""

    source = read_source_data(data_dir)

    with session.begin():
        for record in source.finishers:
            _upsert(
                session,
                Finisher,
                record.finisher_id,
                {
                    "finisher_id": record.finisher_id,
                    "finisher_name": record.finisher_name,
                    "hq_country": record.hq_country,
                },
            )
        for record in source.suppliers:
            existing_supplier = session.get(Supplier, record.supplier_id)
            if existing_supplier is None:
                session.add(
                    Supplier(
                        supplier_id=record.supplier_id,
                        supplier_name=record.supplier_name,
                        hq_country=record.hq_country,
                        child_labor_flagged=False,
                        flagged_at=None,
                    )
                )
            else:
                existing_supplier.supplier_name = record.supplier_name
                existing_supplier.hq_country = record.hq_country
        for record in source.factories:
            _upsert(
                session,
                Factory,
                record.factory_id,
                {
                    "factory_id": record.factory_id,
                    "supplier_id": record.supplier_id,
                    "factory_name": record.factory_name,
                    "address_line": record.address_line,
                    "city": record.city,
                    "country": record.country,
                },
            )
        for record in source.toys:
            _upsert(
                session,
                Toy,
                record.toy_id,
                {
                    "toy_id": record.toy_id,
                    "toy_name": record.toy_name,
                },
            )
        for record in source.parts:
            _upsert(
                session,
                Part,
                record.part_id,
                {
                    "part_id": record.part_id,
                    "part_name": record.part_name,
                },
            )

        session.flush()

        for record in source.finisher_toys:
            _upsert(
                session,
                FinisherToy,
                (record.finisher_id, record.toy_id),
                {
                    "finisher_id": record.finisher_id,
                    "toy_id": record.toy_id,
                    "retail_price_usd": record.retail_price_usd,
                    "units_per_year": record.units_per_year,
                },
            )
        for record in source.toy_parts:
            _upsert(
                session,
                ToyPart,
                (record.toy_id, record.part_id),
                {
                    "toy_id": record.toy_id,
                    "part_id": record.part_id,
                    "quantity": record.quantity,
                },
            )
        for record in source.part_sources:
            _upsert(
                session,
                PartSource,
                (record.part_id, record.factory_id),
                {
                    "part_id": record.part_id,
                    "factory_id": record.factory_id,
                    "unit_cost_usd": record.unit_cost_usd,
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
