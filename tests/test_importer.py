from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from fairtoy.db import create_engine_for_path, create_schema, create_session_factory
from fairtoy.importer import ImportValidationError, import_fixtures, read_source_data
from fairtoy.models import (
    Factory,
    Finisher,
    FinisherToy,
    Part,
    PartSource,
    Supplier,
    Toy,
    ToyPart,
)


FIXTURE_DIR = Path(__file__).parents[1] / "data"


def _session_for(path: Path):
    engine = create_engine_for_path(path)
    create_schema(engine)
    return engine, create_session_factory(engine)


def _count(session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_imports_canonical_graph_and_preserves_nulls(tmp_path: Path) -> None:
    engine, session_factory = _session_for(tmp_path / "fairtoy.sqlite3")
    try:
        with session_factory() as session:
            summary = import_fixtures(session, FIXTURE_DIR)

        assert summary.finishers == 8
        assert summary.suppliers == 50
        assert summary.factories == 232
        assert summary.toys == 300
        assert summary.finisher_toys == 305
        assert summary.parts == 400
        assert summary.toy_parts == 10_463
        assert summary.part_sources == 422

        with session_factory() as session:
            assert _count(session, Finisher) == 8
            assert _count(session, Supplier) == 50
            assert _count(session, Factory) == 232
            assert _count(session, Toy) == 300
            assert _count(session, FinisherToy) == 305
            assert _count(session, Part) == 400
            assert _count(session, ToyPart) == 10_463
            assert _count(session, PartSource) == 422

            factory = session.get(Factory, "FAC-0032")
            assert factory is not None
            assert factory.address_line is None
            assert factory.city is None
            assert factory.country == "China"

            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            assert supplier.child_labor_flagged is False
            assert supplier.flagged_at is None
    finally:
        engine.dispose()


def test_reimport_is_idempotent_and_preserves_supplier_flag(
    tmp_path: Path,
) -> None:
    engine, session_factory = _session_for(tmp_path / "fairtoy.sqlite3")
    try:
        with session_factory() as session:
            first_summary = import_fixtures(session, FIXTURE_DIR)
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            supplier.child_labor_flagged = True
            supplier.flagged_at = datetime(2026, 10, 15, 9, 45)
            session.commit()

        with session_factory() as session:
            second_summary = import_fixtures(session, FIXTURE_DIR)
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            assert supplier.child_labor_flagged is True
            assert supplier.flagged_at == datetime(2026, 10, 15, 9, 45)

        assert second_summary == first_summary
        with session_factory() as session:
            assert _count(session, Supplier) == 50
            assert _count(session, PartSource) == 422
    finally:
        engine.dispose()


def test_exact_duplicate_fixture_rows_are_deduplicated(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "data"
    shutil.copytree(FIXTURE_DIR, fixture_dir)

    for filename, line in (
        ("toys.csv", "TOY-0275,Copper Camp,FIN-003,39.5,3173720"),
        ("parts.csv", "PRT-0121,injection-moulded body,SUP-027,FAC-0124,4.83"),
        ("bill_of_materials.csv", "TOY-0275,PRT-0176,4"),
    ):
        with (fixture_dir / filename).open("a", encoding="utf-8") as handle:
            handle.write(f"\n{line}\n")

    source = read_source_data(fixture_dir)
    assert len(source.toys) == 300
    assert len(source.finisher_toys) == 305
    assert len(source.parts) == 400
    assert len(source.part_sources) == 422
    assert len(source.toy_parts) == 10_463


def test_invalid_relationship_fails_before_writing_any_rows(
    tmp_path: Path,
) -> None:
    fixture_dir = tmp_path / "data"
    shutil.copytree(FIXTURE_DIR, fixture_dir)
    factories_path = fixture_dir / "factories.csv"
    factories = factories_path.read_text(encoding="utf-8")
    factories_path.write_text(
        factories.replace(
            "FAC-0001,SUP-001,",
            "FAC-0001,SUP-MISSING,",
            1,
        ),
        encoding="utf-8",
    )

    engine, session_factory = _session_for(tmp_path / "fairtoy.sqlite3")
    try:
        with session_factory() as session:
            with pytest.raises(ImportValidationError, match="missing supplier"):
                import_fixtures(session, fixture_dir)

        with session_factory() as session:
            assert _count(session, Finisher) == 0
            assert _count(session, Supplier) == 0
            assert _count(session, Factory) == 0
            assert _count(session, Toy) == 0
    finally:
        engine.dispose()


def test_sqlite_foreign_keys_and_domain_checks_are_enabled(
    tmp_path: Path,
) -> None:
    engine, session_factory = _session_for(tmp_path / "fairtoy.sqlite3")
    try:
        with session_factory() as session:
            import_fixtures(session, FIXTURE_DIR)
            pragma_value = session.connection().exec_driver_sql(
                "PRAGMA foreign_keys"
            ).scalar_one()
            assert pragma_value == 1

        with session_factory() as session:
            session.add(
                Supplier(
                    supplier_id="SUP-TEST",
                    supplier_name="Test Supplier",
                    child_labor_flagged=True,
                    flagged_at=None,
                )
            )
            with pytest.raises(IntegrityError):
                session.commit()

        with session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO toy_parts (toy_id, part_id, quantity) "
                        "VALUES (:toy_id, :part_id, :quantity)"
                    ),
                    {
                        "toy_id": "TOY-MISSING",
                        "part_id": "PRT-MISSING",
                        "quantity": 1,
                    },
                )
                session.commit()

        with session_factory() as session:
            with pytest.raises(IntegrityError):
                session.execute(
                    text(
                        "INSERT INTO finisher_toys "
                        "(finisher_id, toy_id, retail_price_usd, units_per_year) "
                        "VALUES (:finisher_id, :toy_id, :retail_price_usd, NULL)"
                    ),
                    {
                        "finisher_id": "FIN-001",
                        "toy_id": "TOY-0275",
                        "retail_price_usd": -1,
                    },
                )
                session.commit()
    finally:
        engine.dispose()
