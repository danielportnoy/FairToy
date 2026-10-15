from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from .config import DEFAULT_DATA_DIR, DEFAULT_DATABASE_PATH
from .db import (
    create_engine_for_path,
    create_schema,
    create_session_factory,
    drop_schema,
)
from .importer import ImportSummary, ImportValidationError, import_fixtures


def _add_location_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="directory containing the six CSV fixture files",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
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
    data_dir: Path,
    database_path: Path,
    reset: bool,
) -> ImportSummary:
    engine = create_engine_for_path(database_path)
    try:
        if reset:
            drop_schema(engine)
        create_schema(engine)
        session_factory = create_session_factory(engine)
        with session_factory() as session:
            return import_fixtures(session, data_dir)
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        summary = _run_import(
            data_dir=args.data_dir,
            database_path=args.database,
            reset=args.command == "reset",
        )
    except (ImportValidationError, SQLAlchemyError) as exc:
        print(f"FairToy setup failed: {exc}", file=sys.stderr)
        return 1

    action = "Reset and imported" if args.command == "reset" else "Imported"
    print(f"{action} FairToy fixtures ({_summary_text(summary)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
