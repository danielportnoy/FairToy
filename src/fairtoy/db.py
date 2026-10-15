from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for the canonical FairToy SQLAlchemy models."""


def create_engine_for_path(
    database_path: str | Path,
    *,
    echo: bool = False,
) -> Engine:
    """Create a SQLite engine and enable foreign-key enforcement."""

    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{path.resolve()}",
        connect_args={"check_same_thread": False},
        echo=echo,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(
        dbapi_connection: Any,
        _connection_record: Any,
    ) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=True,
        expire_on_commit=False,
    )


def create_schema(engine: Engine) -> None:
    """Create all canonical tables without importing or reseeding data."""

    from . import models  # noqa: F401

    Base.metadata.create_all(engine)


def drop_schema(engine: Engine) -> None:
    """Drop canonical tables for an explicit development reset."""

    from . import models  # noqa: F401

    Base.metadata.drop_all(engine)
