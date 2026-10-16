# FairToy

FairToy is a traceability application for toy Finishers. It imports customer
CSV exports, maps Toys to Parts and possible Suppliers/Factories, and shows
which Toys may be exposed when a Supplier is flagged for child labor.

The MVP provides two workflows:

- **Finisher Traceability:** select a Finisher, search and filter its Toys,
  then inspect Toy → Part → Supplier → Factory paths.
- **Suppliers:** review all Suppliers, flag or unflag their current risk state,
  and inspect each Supplier's Factories and supplied Parts.

## Technology

- Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, and Pydantic
- SQLite for the local canonical database
- React 19, TypeScript, Vite, and native browser `fetch`
- Pytest, HTTPX, Ruff, and mypy for backend development
- Vitest and Testing Library for frontend tests

Authentication, multi-tenancy, generic CRUD, order/recall workflows,
notifications, deployment, and production infrastructure are not included in
this version.

## Prerequisites

- [Python 3.11 or newer](https://www.python.org/downloads/)
- [Node.js and npm](https://nodejs.org/en/download)

The commands below use a Unix-like shell. On Windows PowerShell, activate the
virtual environment with `.venv\Scripts\Activate.ps1`.

## Quick start

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
fairtoy setup
```

`fairtoy setup` creates the SQLite schema, validates the selected CSV
fixtures, and imports them into the default database. The default fixture set
is `data/full/`, and the default database is
`data/generated/fairtoy.sqlite3`.

Start the API in one terminal:

```bash
source .venv/bin/activate
uvicorn fairtoy.api:app --reload
```

Start the frontend in a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open:

- Frontend: <http://127.0.0.1:5173>
- API documentation: <http://127.0.0.1:8000/docs>

The Vite development server proxies `/api` requests to the FastAPI server.

## Data and database setup

The importer reads six customer-export-style CSV files:

- `finishers.csv`
- `suppliers.csv`
- `factories.csv`
- `parts.csv`
- `toys.csv`
- `bill_of_materials.csv`

The source data is normalized into the canonical relational tables described
in [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md).

Two fixture sets are included:

- `data/full/` — the complete source dataset: 8 Finishers, 50 Suppliers,
  232 Factories, 300 Toys, 400 Parts, and 10,463 Toy-Part relationships.
- `data/demo/` — a smaller fixture with 3 Finishers, 3 Suppliers, 3 Toys per
  Finisher, uneven Supplier coverage, and clear
  affected/potentially-affected/unaffected examples.

The default database is `data/generated/fairtoy.sqlite3`, which is ignored by
Git.

See the [CLI reference](#cli) for setup and reset commands.

`setup` preserves current Supplier flags. `reset` is destructive only after
the selected fixture set has passed validation. Do not run `setup` with both
fixture sets against the same database: they share identifiers and are not
isolated datasets.

## CLI

The `fairtoy` command manages the local canonical database. It is installed
by `python -m pip install -e ".[dev]"`.

```text
fairtoy [-h] {setup,reset} ...
```

### `fairtoy setup`

Create the schema if needed and import fixtures without dropping existing
tables. It validates all six files before writing, then upserts canonical
entities and relationships in a transaction. Re-running setup is safe for
normal data refreshes and preserves the current Supplier flag state. Use
`reset` when switching fixture sets or requiring a clean database.

```bash
fairtoy setup
fairtoy setup --database /tmp/fairtoy.sqlite3
```

### `fairtoy reset`

Drop and recreate the canonical schema, then import the selected fixtures.
Use this when switching between the full and demo datasets or when you need a
clean local state. This command clears persisted Supplier flags.

```bash
fairtoy reset
fairtoy reset --data-dir data/demo
fairtoy reset \
  --data-dir data/full \
  --database /tmp/fairtoy-full.sqlite3
```

Both commands accept:

- `--data-dir PATH` — directory containing the six CSV fixture files.
- `--database PATH` — SQLite file to create or update.

Successful commands print an import summary such as
`finishers=8, suppliers=50, factories=232, toys=300`.

## API

The API serves JSON over HTTP. The interactive OpenAPI reference is available
at <http://127.0.0.1:8000/docs> while the API is running. The main workflow
endpoints are:

```text
GET   /api/finishers
GET   /api/toys?finisher_id=FIN-001
GET   /api/toys/{toy_id}?finisher_id=FIN-001
GET   /api/suppliers
GET   /api/suppliers?finisher_id=FIN-001
GET   /api/suppliers/{supplier_id}
PATCH /api/suppliers/{supplier_id}
```

Supplier flag updates use an explicit desired state:

```json
{"child_labor_flagged": true}
```

Example:

```bash
curl 'http://127.0.0.1:8000/api/toys?finisher_id=FIN-001'
```

The API and setup CLI emit structured application logs. API responses include
an `X-Request-ID` correlation header. Metrics, distributed tracing,
health/readiness endpoints, dashboards, and alerting are intentionally
deferred.

## Tests

Run the backend test suite and quality checks from the repository root:

```bash
pytest -q
ruff check src tests
ruff format --check src tests
mypy src/fairtoy
```

Run the frontend tests, type check, and production build:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

## Repository structure

```text
src/fairtoy/              FastAPI application and domain code
  impact/                 Pure impact classification service
tests/                    Backend, importer, API, and observability tests
frontend/src/             React UI, typed API client, and view models
data/full/                Complete source CSV fixtures
data/demo/                Small review/demo CSV fixtures
data/generated/           Ignored local SQLite databases
pyproject.toml            Backend package, dependencies, and CLI definition
frontend/package.json     Frontend dependencies and scripts
SPEC.md                   Product and domain contract
SYSTEM_DESIGN.md          Technical architecture and scale boundary
DECISIONS.md              Decision rationale and trade-offs
PROCESS_LOG.md            Spec-driven implementation history
```

## Further documentation

`SPEC.md` defines product behavior and domain semantics. `SYSTEM_DESIGN.md`
explains the implementation. `DECISIONS.md` records alternatives and
trade-offs, while `PROCESS_LOG.md` records the spec-driven workflow and
verification history.
