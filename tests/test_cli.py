import shutil
from datetime import datetime, timezone
from pathlib import Path

from fairtoy.cli import main
from fairtoy.config import DEFAULT_DATA_DIR, ImportSettings
from fairtoy.db import create_engine_for_path, create_session_factory
from fairtoy.models import Supplier

FIXTURE_DIR = Path(__file__).parents[1] / "data" / "full"


def test_default_import_settings_use_full_fixture_set() -> None:
    assert ImportSettings().data_dir == DEFAULT_DATA_DIR
    assert DEFAULT_DATA_DIR == FIXTURE_DIR


def _run_setup(database_path: Path) -> None:
    assert (
        main(
            [
                "setup",
                "--data-dir",
                str(FIXTURE_DIR),
                "--database",
                str(database_path),
            ]
        )
        == 0
    )


def _set_supplier_flag(database_path: Path) -> None:
    engine = create_engine_for_path(database_path)
    try:
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            supplier.child_labor_flagged = True
            supplier.flagged_at = datetime.now(timezone.utc)
            session.commit()
    finally:
        engine.dispose()


def test_setup_preserves_supplier_flags_and_reset_recreates_data(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fairtoy.sqlite3"
    _run_setup(database_path)
    _set_supplier_flag(database_path)

    _run_setup(database_path)

    engine = create_engine_for_path(database_path)
    try:
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            assert supplier.child_labor_flagged is True
            assert supplier.flagged_at is not None
    finally:
        engine.dispose()

    assert (
        main(
            [
                "reset",
                "--data-dir",
                str(FIXTURE_DIR),
                "--database",
                str(database_path),
            ]
        )
        == 0
    )

    engine = create_engine_for_path(database_path)
    try:
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            assert supplier.child_labor_flagged is False
            assert supplier.flagged_at is None
    finally:
        engine.dispose()


def test_invalid_reset_does_not_destroy_existing_database(tmp_path: Path) -> None:
    database_path = tmp_path / "fairtoy.sqlite3"
    _run_setup(database_path)
    _set_supplier_flag(database_path)

    fixture_dir = tmp_path / "invalid-data"
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

    assert (
        main(
            [
                "reset",
                "--data-dir",
                str(fixture_dir),
                "--database",
                str(database_path),
            ]
        )
        == 1
    )

    engine = create_engine_for_path(database_path)
    try:
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            supplier = session.get(Supplier, "SUP-001")
            assert supplier is not None
            assert supplier.child_labor_flagged is True
            assert supplier.flagged_at is not None
    finally:
        engine.dispose()
