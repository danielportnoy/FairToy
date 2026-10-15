from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path


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
    def from_directory(cls, data_dir: str | Path) -> FixturePaths:
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


__all__ = [
    "FactoryRecord",
    "FinisherRecord",
    "FinisherToyRecord",
    "FixturePaths",
    "ImportSummary",
    "ImportValidationError",
    "PartRecord",
    "PartSourceRecord",
    "SourceData",
    "SupplierRecord",
    "ToyPartRecord",
    "ToyRecord",
]
