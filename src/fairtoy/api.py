from __future__ import annotations

from collections.abc import Generator
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from sqlalchemy.orm import Session, sessionmaker

from .api_schemas import (
    FinisherResponse,
    PartImpactResponse,
    SupplierResponse,
    ToyDetailResponse,
    ToySummaryResponse,
    ImpactPathResponse,
)
from .config import DEFAULT_DATABASE_PATH
from .db import create_engine_for_path, create_session_factory
from .impact import (
    ImpactPath,
    PartImpact,
    ToyImpact,
    calculate_toy_impact,
    calculate_toy_impacts,
)
from .repository import TraceabilityRepository


def create_app(
    database_path: str | Path = DEFAULT_DATABASE_PATH,
) -> FastAPI:
    """Create the FairToy API with a request-scoped SQLite session factory."""

    engine = create_engine_for_path(database_path)
    session_factory = create_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        engine.dispose()

    app = FastAPI(
        title="FairToy API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.engine = engine
    app.state.session_factory = session_factory

    @app.get("/api/finishers", response_model=list[FinisherResponse])
    def list_finishers(
        session: Session = Depends(get_session),
    ) -> list[FinisherResponse]:
        repository = TraceabilityRepository(session)
        return [
            FinisherResponse(
                finisher_id=finisher.finisher_id,
                finisher_name=finisher.finisher_name,
                hq_country=finisher.hq_country,
            )
            for finisher in repository.list_finishers()
        ]

    @app.get("/api/suppliers", response_model=list[SupplierResponse])
    def list_suppliers(
        session: Session = Depends(get_session),
    ) -> list[SupplierResponse]:
        repository = TraceabilityRepository(session)
        return [
            SupplierResponse(
                supplier_id=supplier.supplier_id,
                supplier_name=supplier.supplier_name,
                hq_country=supplier.hq_country,
                child_labor_flagged=supplier.child_labor_flagged,
                flagged_at=supplier.flagged_at,
            )
            for supplier in repository.list_suppliers()
        ]

    @app.get("/api/toys", response_model=list[ToySummaryResponse])
    def list_toys(
        finisher_id: str = Query(..., min_length=1),
        session: Session = Depends(get_session),
    ) -> list[ToySummaryResponse]:
        repository = TraceabilityRepository(session)
        _require_finisher(repository, finisher_id)
        impacts = calculate_toy_impacts(
            repository.list_toy_traceability(finisher_id=finisher_id)
        )
        return [
            _summary_response(finisher_id, impact)
            for impact in impacts
        ]

    @app.get(
        "/api/toys/{toy_id}",
        response_model=ToyDetailResponse,
    )
    def get_toy(
        toy_id: str,
        finisher_id: str = Query(..., min_length=1),
        session: Session = Depends(get_session),
    ) -> ToyDetailResponse:
        repository = TraceabilityRepository(session)
        _require_finisher(repository, finisher_id)
        _require_identifier(toy_id, "toy_id")
        traceability = repository.get_toy_traceability(
            finisher_id=finisher_id,
            toy_id=toy_id,
        )
        if traceability is None:
            raise HTTPException(
                status_code=404,
                detail="Toy is not in the selected Finisher catalog",
            )
        return _detail_response(
            finisher_id,
            calculate_toy_impact(traceability),
        )

    return app


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    with session_factory() as session:
        yield session


def _require_finisher(
    repository: TraceabilityRepository,
    finisher_id: str,
) -> None:
    _require_identifier(finisher_id, "finisher_id")
    if repository.get_finisher(finisher_id) is None:
        raise HTTPException(status_code=404, detail="Finisher not found")


def _require_identifier(value: str, field_name: str) -> None:
    if not value.strip():
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} is required",
        )


def _summary_response(
    finisher_id: str,
    impact: ToyImpact,
) -> ToySummaryResponse:
    return ToySummaryResponse(
        finisher_id=finisher_id,
        toy_id=impact.toy_id,
        toy_name=impact.toy_name,
        status=impact.status,
        reason_code=impact.reason_code,
        reason=impact.reason,
    )


def _detail_response(
    finisher_id: str,
    impact: ToyImpact,
) -> ToyDetailResponse:
    summary = _summary_response(finisher_id, impact)
    return ToyDetailResponse(
        **summary.model_dump(),
        parts=[_part_response(part) for part in impact.parts],
    )


def _part_response(part: PartImpact) -> PartImpactResponse:
    return PartImpactResponse(
        part_id=part.part_id,
        part_name=part.part_name,
        quantity=part.quantity,
        status=part.status,
        reason_code=part.reason_code,
        reason=part.reason,
        paths=[_path_response(path) for path in part.paths],
    )


def _path_response(path: ImpactPath) -> ImpactPathResponse:
    return ImpactPathResponse(
        supplier_id=path.supplier_id,
        supplier_name=path.supplier_name,
        supplier_flagged=path.supplier_flagged,
        factory_id=path.factory_id,
        factory_name=path.factory_name,
        unit_cost_usd=_serialize_unit_cost(path.unit_cost_usd),
    )


def _serialize_unit_cost(unit_cost_usd: Decimal | None) -> str | None:
    if unit_cost_usd is None:
        return None
    return format(unit_cost_usd, "f")


app = create_app()
