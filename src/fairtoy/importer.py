from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from .importer_contracts import (
    FactoryRecord,
    FinisherRecord,
    FinisherToyRecord,
    FixturePaths,
    ImportSummary,
    ImportValidationError,
    PartRecord,
    PartSourceRecord,
    SourceData,
    SupplierRecord,
    ToyPartRecord,
    ToyRecord,
)
from .importer_parsing import parse_source_data
from .importer_persistence import persist_source_data
from .importer_validation import validate_source_data


def read_source_data(data_dir: str | Path) -> SourceData:
    """Read, normalize, deduplicate, and validate all six fixture files."""

    return validate_source_data(parse_source_data(data_dir))


def import_fixtures(
    session: Session,
    data_dir: str | Path,
) -> ImportSummary:
    """Validate and atomically persist fixtures without resetting flags."""

    return persist_source_data(session, read_source_data(data_dir))


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
    "import_fixtures",
    "read_source_data",
]
