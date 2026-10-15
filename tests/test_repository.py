from __future__ import annotations

from pathlib import Path

import pytest

from fairtoy.db import create_engine_for_path, create_schema, create_session_factory
from fairtoy.importer import import_fixtures
from fairtoy.models import FinisherToy, Part, Toy, ToyPart
from fairtoy.repository import TraceabilityRepository

FIXTURE_DIR = Path(__file__).parents[1] / "data"


@pytest.fixture(scope="module")
def session_factory(tmp_path_factory: pytest.TempPathFactory):
    database_path = tmp_path_factory.mktemp("repository") / "fairtoy.sqlite3"
    engine = create_engine_for_path(database_path)
    create_schema(engine)
    factory = create_session_factory(engine)

    with factory() as session:
        import_fixtures(session, FIXTURE_DIR)
        session.add_all(
            [
                Toy(toy_id="TOY-EMPTY", toy_name="Empty Toy"),
                FinisherToy(
                    finisher_id="FIN-001",
                    toy_id="TOY-EMPTY",
                ),
                Toy(toy_id="TOY-NO-SOURCE", toy_name="No Source Toy"),
                FinisherToy(
                    finisher_id="FIN-001",
                    toy_id="TOY-NO-SOURCE",
                ),
                Part(part_id="PRT-NO-SOURCE", part_name="Unallocated Part"),
                ToyPart(
                    toy_id="TOY-NO-SOURCE",
                    part_id="PRT-NO-SOURCE",
                    quantity=3,
                ),
            ]
        )
        session.commit()

    yield factory
    engine.dispose()


def test_lists_only_the_selected_finishers_catalog(
    session_factory,
) -> None:
    with session_factory() as session:
        toys = TraceabilityRepository(session).list_toy_traceability(
            finisher_id="FIN-003"
        )

    assert toys
    assert [toy.toy_id for toy in toys] == sorted(toy.toy_id for toy in toys)
    assert all(toy.finisher_id == "FIN-003" for toy in toys)
    assert any(toy.toy_id == "TOY-0275" for toy in toys)


def test_detail_read_is_scoped_to_the_finisher_catalog(
    session_factory,
) -> None:
    with session_factory() as session:
        repository = TraceabilityRepository(session)
        detail = repository.get_toy_traceability(
            finisher_id="FIN-003",
            toy_id="TOY-0275",
        )
        outside_catalog = repository.get_toy_traceability(
            finisher_id="FIN-001",
            toy_id="TOY-0275",
        )

    assert detail is not None
    assert detail.finisher_id == "FIN-003"
    assert detail.toy_id == "TOY-0275"
    assert detail.facts
    assert outside_catalog is None


def test_source_facts_derive_supplier_through_factory(
    session_factory,
) -> None:
    with session_factory() as session:
        detail = TraceabilityRepository(session).get_toy_traceability(
            finisher_id="FIN-003",
            toy_id="TOY-0275",
        )

    assert detail is not None
    source_facts = [fact for fact in detail.facts if fact.factory_id is not None]
    assert source_facts
    assert all(fact.supplier_id is not None for fact in source_facts)
    assert all(fact.factory_name is not None for fact in source_facts)
    assert all(fact.unit_cost_usd is not None for fact in source_facts)


def test_same_toy_is_visible_with_the_same_global_facts_to_each_finisher(
    session_factory,
) -> None:
    with session_factory() as session:
        repository = TraceabilityRepository(session)
        first_catalog = repository.get_toy_traceability(
            finisher_id="FIN-001",
            toy_id="TOY-0092",
        )
        second_catalog = repository.get_toy_traceability(
            finisher_id="FIN-004",
            toy_id="TOY-0092",
        )

    assert first_catalog is not None
    assert second_catalog is not None
    assert first_catalog.toy_id == second_catalog.toy_id
    assert first_catalog.facts == second_catalog.facts


def test_no_source_part_is_preserved_by_the_left_join(
    session_factory,
) -> None:
    with session_factory() as session:
        detail = TraceabilityRepository(session).get_toy_traceability(
            finisher_id="FIN-001",
            toy_id="TOY-NO-SOURCE",
        )

    assert detail is not None
    assert len(detail.facts) == 1
    assert detail.facts[0].part_id == "PRT-NO-SOURCE"
    assert detail.facts[0].quantity == 3
    assert detail.facts[0].supplier_id is None
    assert detail.facts[0].factory_id is None


def test_toy_with_no_bom_rows_is_returned_with_empty_facts(
    session_factory,
) -> None:
    with session_factory() as session:
        detail = TraceabilityRepository(session).get_toy_traceability(
            finisher_id="FIN-001",
            toy_id="TOY-EMPTY",
        )

    assert detail is not None
    assert detail.toy_name == "Empty Toy"
    assert detail.facts == ()


def test_blank_scope_identifiers_are_rejected(session_factory) -> None:
    with session_factory() as session:
        repository = TraceabilityRepository(session)
        with pytest.raises(ValueError, match="finisher_id is required"):
            repository.list_toy_traceability(finisher_id=" ")
        with pytest.raises(ValueError, match="toy_id is required"):
            repository.get_toy_traceability(
                finisher_id="FIN-001",
                toy_id="",
            )
