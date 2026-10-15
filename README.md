# FairToy

FairToy is a focused traceability application for Finishers. It shows how
finished toys relate to parts, suppliers, and factories, and identifies toys
that are affected or potentially affected when a supplier is flagged for child
labor.

## Status

Slice 1 foundation is implemented; the API and frontend remain deferred until
the foundation is reviewed and accepted. The implementation follows the
decisions in [`SPEC.md`](SPEC.md).

## Current scope

The core workflow will allow a Finisher to:

1. Browse its toys.
2. Trace a toy through its parts to possible suppliers and factories.
3. Flag or unflag a supplier for child labor.
4. See affected and potentially affected toys with an explainable path.

Retailers, basic-material companies, raw materials, orders, recalls,
authentication, multi-tenancy, notifications, real-time updates, and
production deployment are intentionally deferred.

## Planned technology

- Python and FastAPI
- SQLite
- React, TypeScript, and Vite
- A deterministic importer for the supplied CSV fixtures

## Project records

- [`SPEC.md`](SPEC.md) — product boundary, domain rules, assumptions, and
  acceptance criteria
- [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md) — technical architecture and
  implementation design
- [`DECISIONS.md`](DECISIONS.md) — decisions and deferred extensions
- [`PROCESS_LOG.md`](PROCESS_LOG.md) — implementation phases, AI usage, and
  review checkpoints

## Source data

The assignment data is currently available at
`../toy_data/` in the preparation workspace. The original six CSV files are
copied into this repository under `data/` so a fresh checkout can be seeded
reproducibly. macOS metadata under `__MACOSX/` is not part of the application
data.

Slice 1 local database setup is documented below. API and frontend run
instructions will be added with their respective implementation slices.

## Slice 1: local database setup

The foundation slice uses Python, SQLAlchemy, and a file-backed SQLite
database. The importer reads the six CSV fixtures from `data/` and writes
the canonical tables described in `SYSTEM_DESIGN.md`.

Create a virtual environment, install the project and development
dependencies, then run the tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Create or update the local database with the fixtures:

```bash
fairtoy setup
```

The default database is `data/generated/fairtoy.sqlite3`, which is ignored by
git. Re-running `fairtoy setup` is idempotent and preserves current Supplier
flags. To intentionally recreate the database from the fixtures:

```bash
fairtoy reset
```

The API and frontend are not implemented in this slice.
