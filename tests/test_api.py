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


def test_supplier_flag_update_is_explicit_idempotent_and_recalculates(
    client: TestClient,
) -> None:
    detail_response = client.get(
        "/api/toys/TOY-0275",
        params={"finisher_id": "FIN-003"},
    )
    path = detail_response.json()["parts"][0]["paths"][0]
    supplier_id = path["supplier_id"]

    flagged_response = client.patch(
        f"/api/suppliers/{supplier_id}",
        json={"child_labor_flagged": True},
    )
    assert flagged_response.status_code == 200
    flagged_supplier = flagged_response.json()
    assert flagged_supplier["child_labor_flagged"] is True
    assert flagged_supplier["flagged_at"]
    first_flagged_at = flagged_supplier["flagged_at"]

    repeated_response = client.patch(
        f"/api/suppliers/{supplier_id}",
        json={"child_labor_flagged": True},
    )
    assert repeated_response.status_code == 200
    assert repeated_response.json()["flagged_at"] == first_flagged_at

    flagged_detail = client.get(
        "/api/toys/TOY-0275",
        params={"finisher_id": "FIN-003"},
    ).json()
    flagged_paths = [
        candidate_path
        for part in flagged_detail["parts"]
        for candidate_path in part["paths"]
        if candidate_path["supplier_id"] == supplier_id
    ]
    assert flagged_paths
    assert all(candidate_path["supplier_flagged"] for candidate_path in flagged_paths)

    unflagged_response = client.patch(
        f"/api/suppliers/{supplier_id}",
        json={"child_labor_flagged": False},
    )
    assert unflagged_response.status_code == 200
    assert unflagged_response.json()["child_labor_flagged"] is False
    assert unflagged_response.json()["flagged_at"] is None

    unflagged_detail = client.get(
        "/api/toys/TOY-0275",
        params={"finisher_id": "FIN-003"},
    ).json()
    unflagged_paths = [
        candidate_path
        for part in unflagged_detail["parts"]
        for candidate_path in part["paths"]
        if candidate_path["supplier_id"] == supplier_id
    ]
    assert unflagged_paths
    assert all(not candidate_path["supplier_flagged"] for candidate_path in unflagged_paths)


def test_unknown_supplier_flag_update_returns_not_found(
    client: TestClient,
) -> None:
    response = client.patch(
        "/api/suppliers/SUP-UNKNOWN",
        json={"child_labor_flagged": True},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Supplier not found"


@pytest.mark.parametrize("value", [1, 0, "true", "false", "yes", None])
def test_supplier_flag_update_rejects_non_boolean_values(
    client: TestClient,
    value: object,
) -> None:
    response = client.patch(
        "/api/suppliers/SUP-001",
        json={"child_labor_flagged": value},
    )

    assert response.status_code == 422


def test_supplier_flag_update_rejects_unknown_fields(
    client: TestClient,
) -> None:
    response = client.patch(
        "/api/suppliers/SUP-001",
        json={
            "child_labor_flagged": True,
            "unexpected": "rejected",
        },
    )

    assert response.status_code == 422
