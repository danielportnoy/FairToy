from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from time import perf_counter

from sqlalchemy.exc import SQLAlchemyError

from .config import ImportSettings
from .db import (
    create_engine_for_path,
    create_schema,
    create_session_factory,
    drop_schema,
)
from .importer import (
    ImportSummary,
    ImportValidationError,
    import_source_data,
    read_source_data,
)
from .observability import configure_logging, get_logger, log_event

logger = get_logger(__name__)


def _add_location_arguments(parser: argparse.ArgumentParser) -> None:
    defaults = ImportSettings()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=defaults.data_dir,
        help="directory containing the six CSV fixture files",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=defaults.database_path,
        help="SQLite database path",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fairtoy",
        description="FairToy local database setup",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser(
        "setup",
        help="create the schema and import fixtures without resetting data",
    )
    _add_location_arguments(setup_parser)

    reset_parser = subparsers.add_parser(
        "reset",
        help="recreate the schema and import fixtures",
    )
    _add_location_arguments(reset_parser)

    return parser


def _summary_text(summary: ImportSummary) -> str:
    return ", ".join(
        f"{field}={getattr(summary, field)}"
        for field in (
            "finishers",
            "suppliers",
            "factories",
            "toys",
            "finisher_toys",
            "parts",
            "toy_parts",
            "part_sources",
        )
    )


def _run_import(
    *,
    settings: ImportSettings,
    reset: bool,
) -> ImportSummary:
    operation = "reset" if reset else "setup"
    started = perf_counter()
    log_event(
        logger,
        "import_started",
        operation=operation,
        data_dir=settings.data_dir,
        database_path=settings.database_path,
    )
    try:
        source_data = read_source_data(settings.data_dir)
        engine = create_engine_for_path(settings.database_path)
        try:
            if reset:
                drop_schema(engine)
            create_schema(engine)
            session_factory = create_session_factory(engine)
            with session_factory() as session:
                summary = import_source_data(session, source_data)
        finally:
            engine.dispose()
    except Exception as exc:
        log_event(
            logger,
            "import_failed",
            level=logging.ERROR,
            operation=operation,
            duration_ms=round((perf_counter() - started) * 1000, 2),
            error_type=type(exc).__name__,
        )
        raise

    log_event(
        logger,
        "import_completed",
        operation=operation,
        duration_ms=round((perf_counter() - started) * 1000, 2),
        **{
            field: getattr(summary, field)
            for field in (
                "finishers",
                "suppliers",
                "factories",
                "toys",
                "finisher_toys",
                "parts",
                "toy_parts",
                "part_sources",
            )
        },
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        settings = ImportSettings.from_values(
            data_dir=args.data_dir,
            database_path=args.database,
        )
        summary = _run_import(
            settings=settings,
            reset=args.command == "reset",
        )
    except (ImportValidationError, OSError, SQLAlchemyError) as exc:
        print(f"FairToy setup failed: {exc}", file=sys.stderr)
        return 1

    action = "Reset and imported" if args.command == "reset" else "Imported"
    print(f"{action} FairToy fixtures ({_summary_text(summary)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
