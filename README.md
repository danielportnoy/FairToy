# FairToy

FairToy is a focused traceability application for Finishers. It shows how
finished toys relate to parts, suppliers, and factories, and identifies toys
that are affected or potentially affected when a supplier is flagged for child
labor.

## Status

The foundation, impact-analysis service, repository boundary, and API are
implemented. The frontend remains deferred to a later slice. The
implementation follows the decisions in
[`SPEC.md`](SPEC.md).

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

Local database setup and API run instructions are documented below. The
frontend remains deferred.

## Local database setup

The foundation slice uses Python, SQLAlchemy, and a file-backed SQLite
database. The importer reads the six CSV fixtures from `data/` and writes
the canonical tables described in `SYSTEM_DESIGN.md`.

Create a virtual environment, install the project and development
dependencies, then run the tests:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest -q
ruff check src tests
ruff format --check src tests
mypy src/fairtoy
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

Both commands validate the complete fixture set before writing. A failed
validation does not replace an existing database; `reset` is destructive only
after the fixture data has passed validation.

## API

Start the API after setting up the local database:

```bash
fairtoy setup
uvicorn fairtoy.api:app --reload
```

FastAPI's interactive documentation is available at
<http://127.0.0.1:8000/docs>. The current workflow endpoints are:

```text
GET /api/finishers
GET /api/toys?finisher_id=FIN-001
GET /api/toys/{toy_id}?finisher_id=FIN-001
GET /api/suppliers
PATCH /api/suppliers/{supplier_id}
```

For example:

```bash
curl 'http://127.0.0.1:8000/api/toys?finisher_id=FIN-001'
```

The PATCH body is an explicit desired state:

```json
{"child_labor_flagged": true}
```

The frontend remains a separate follow-up slice.
