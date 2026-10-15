from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fairtoy.api import create_app
from fairtoy.db import create_engine_for_path, create_schema, create_session_factory
from fairtoy.importer import import_fixtures


FIXTURE_DIR = Path(__file__).parents[1] / "data"


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory):
    database_path = tmp_path_factory.mktemp("api") / "fairtoy.sqlite3"
    setup_engine = create_engine_for_path(database_path)
    create_schema(setup_engine)
    with create_session_factory(setup_engine)() as session:
        import_fixtures(session, FIXTURE_DIR)
    setup_engine.dispose()

    app = create_app(database_path)
    with TestClient(app) as test_client:
        yield test_client


def test_lists_finishers_and_suppliers(client: TestClient) -> None:
    finishers_response = client.get("/api/finishers")
    suppliers_response = client.get("/api/suppliers")

    assert finishers_response.status_code == 200
    assert suppliers_response.status_code == 200
    finishers = finishers_response.json()
    suppliers = suppliers_response.json()
    assert [finisher["finisher_id"] for finisher in finishers] == sorted(
        finisher["finisher_id"] for finisher in finishers
    )
    assert finishers[0].keys() == {"finisher_id", "finisher_name", "hq_country"}
    assert suppliers
    assert suppliers[0]["child_labor_flagged"] is False
    assert suppliers[0]["flagged_at"] is None


def test_lists_finisher_toy_summaries_with_derived_impact(
    client: TestClient,
) -> None:
    response = client.get("/api/toys", params={"finisher_id": "FIN-003"})

    assert response.status_code == 200
    toys = response.json()
    assert toys
    assert [toy["toy_id"] for toy in toys] == sorted(
        toy["toy_id"] for toy in toys
    )
    toy = next(toy for toy in toys if toy["toy_id"] == "TOY-0275")
    assert set(toy) == {
        "finisher_id",
        "toy_id",
        "toy_name",
        "status",
        "reason_code",
        "reason",
    }
    assert toy["finisher_id"] == "FIN-003"
    assert toy["status"] == "unaffected"
    assert toy["reason_code"] == "toy_unaffected"
    assert toy["reason"] == "No required part is affected or potentially affected."


def test_toy_detail_contains_explainable_traceability_paths(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/toys/TOY-0275",
        params={"finisher_id": "FIN-003"},
    )

    assert response.status_code == 200
    toy = response.json()
    assert toy["finisher_id"] == "FIN-003"
    assert toy["toy_id"] == "TOY-0275"
    assert toy["reason_code"] == "toy_unaffected"
    assert toy["parts"]
    assert all(part["paths"] for part in toy["parts"])
    part = toy["parts"][0]
    assert part["reason_code"] == "part_no_flagged_sources"
    path = part["paths"][0]
    assert set(path) == {
        "supplier_id",
        "supplier_name",
        "supplier_flagged",
        "factory_id",
        "factory_name",
        "unit_cost_usd",
    }
    assert path["supplier_id"]
    assert path["factory_id"]
    assert path["supplier_flagged"] is False
    assert isinstance(path["unit_cost_usd"], str)
    assert path["unit_cost_usd"]


def test_toy_detail_is_scoped_to_selected_finisher(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/toys/TOY-0275",
        params={"finisher_id": "FIN-001"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Toy is not in the selected Finisher catalog"
    )


def test_unknown_finisher_is_rejected_for_toy_list(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/toys",
        params={"finisher_id": "FIN-UNKNOWN"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Finisher not found"


def test_blank_finisher_identifier_is_rejected(
    client: TestClient,
) -> None:
    response = client.get("/api/toys", params={"finisher_id": " "})

    assert response.status_code == 422
    assert response.json()["detail"] == "finisher_id is required"
