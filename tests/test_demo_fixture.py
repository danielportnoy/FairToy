from __future__ import annotations

from pathlib import Path

from fairtoy.db import create_engine_for_path, create_schema, create_session_factory
from fairtoy.importer import import_fixtures
from fairtoy.repository import TraceabilityRepository

DEMO_FIXTURE_DIR = Path(__file__).parents[1] / "data" / "demo"


def test_demo_fixture_is_small_and_keeps_supplier_scope_finisher_specific(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "fairtoy-demo.sqlite3"
    engine = create_engine_for_path(database_path)
    create_schema(engine)

    try:
        with create_session_factory(engine)() as session:
            summary = import_fixtures(session, DEMO_FIXTURE_DIR)
            repository = TraceabilityRepository(session)

            suppliers_by_finisher = {
                finisher_id: {
                    supplier.supplier_id
                    for supplier in repository.list_suppliers(finisher_id=finisher_id)
                }
                for finisher_id in ("FIN-001", "FIN-002", "FIN-003")
            }

        assert summary.finishers == 3
        assert summary.suppliers == 3
        assert summary.factories == 3
        assert summary.toys == 6
        assert summary.finisher_toys == 6
        assert summary.parts == 9
        assert summary.toy_parts == 18
        assert summary.part_sources == 12
        assert suppliers_by_finisher == {
            "FIN-001": {"SUP-001", "SUP-002"},
            "FIN-002": {"SUP-002", "SUP-003"},
            "FIN-003": {"SUP-001", "SUP-003"},
        }
        assert not set.intersection(*suppliers_by_finisher.values())
    finally:
        engine.dispose()
