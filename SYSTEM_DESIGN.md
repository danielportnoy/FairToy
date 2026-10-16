# FairToy system design

## Document role

**Status:** Implemented MVP

[`SPEC.md`](SPEC.md) is the product and domain source of truth. It defines
what FairToy must do and the semantics users can rely on. This document
explains how the implemented slice satisfies that contract.

The document follows a system-design discussion: requirements and constraints,
known scale, data model, API, architecture, flows, deep dives, and the
production boundary. [`DECISIONS.md`](DECISIONS.md) records alternatives and
trade-offs; [`PROCESS_LOG.md`](PROCESS_LOG.md) records how the work evolved.

## 1. Context and scope

FairToy helps a Finisher understand possible child-labor exposure across its
Toy catalog. The core evidence path is:

```text
Toy → Part → possible source → Factory → Supplier
```

The supplied CSVs identify possible sourcing paths, not the supplier that
produced a particular physical Toy. The system therefore explains possible
exposure and does not claim actual allocation without additional data.

### Functional requirements carried into the design

- Import the six customer-export-style CSVs into a canonical model.
- Let a user explicitly select a Finisher and browse its Toys.
- Show a Toy's Parts, quantities, possible Suppliers, and Factories.
- Let a user review all Suppliers independently of Finisher selection.
- Let a user flag or unflag a Supplier globally.
- Derive each Toy's current impact status with a stable reason and evidence
  path.
- Persist the current Supplier flag across application restarts.

The detailed behavior and acceptance criteria remain in [`SPEC.md`](SPEC.md).

### Non-functional and design goals

- **Correctness:** preserve relationships and reject invalid or conflicting
  source data instead of silently losing traceability.
- **Explainability:** return status, stable `reason_code`, human-readable
  reason, and the path that led to the result.
- **Consistency:** update Supplier state transactionally and calculate impact
  from current authoritative state.
- **Usability:** keep catalog responses compact and reveal high-fanout
  evidence progressively.
- **Maintainability:** keep ingestion, persistence, domain rules, HTTP, and UI
  responsibilities testable and separately understandable.
- **Operational safety:** provide bounded request/import/mutation logging
  without logging sensitive payloads.

### Explicitly out of scope

Authentication, authorization, multi-tenancy, notifications, real-time
updates, orders, recalls, generic CRUD for every entity, factory-level risk,
audit history, deployment infrastructure, and production monitoring platforms
are deliberately excluded. They are documented boundaries, not missing MVP
requirements.

## 2. Assumptions and known scale

The assignment does not provide production traffic, latency, concurrency,
retention, or availability targets. The full supplied fixture currently
contains:

- 8 Finishers;
- 50 Suppliers;
- 232 Factories;
- 300 Toys;
- 400 Parts;
- 305 Finisher–Toy relationships;
- 10,463 Toy–Part relationships; and
- 422 Part–Factory source relationships.

These numbers establish a useful fixture and test boundary, not a production
capacity target. The MVP consequently uses a local SQLite database,
synchronous request-scoped sessions, compact summary reads, on-demand detail
reads, and browser pagination.

The first production assumptions to validate would be catalog size, source
fan-out, concurrent users, flag mutation frequency, acceptable read latency,
and whether source allocation is known per Finisher or production batch.

## 3. Domain model and data design

### Relationship model

```text
Finisher ──< FinisherToy >── Toy ──< ToyPart >── Part
                                                  │
                                                  └──< PartSource >── Factory ── Supplier
```

The canonical tables are:

- `finishers` and `toys` — stable source entities;
- `finisher_toys` — catalog membership and Finisher-specific commercial
  values such as retail price and annual volume;
- `parts` — reusable component identity;
- `toy_parts` — BOM membership and quantity;
- `part_sources` — possible Part-to-Factory sourcing paths and source-specific
  values such as unit cost;
- `factories` — manufacturing sites belonging to Suppliers;
- `suppliers` — global risk subject, current flag, and `flagged_at`.

The importer treats the CSVs as external, flat exports and normalizes them
into this model. Exact duplicate rows may be deduplicated; conflicting
identities and invalid references fail validation before the database is
written.

### Integrity and indexing

Source identifiers are canonical primary keys for this single-source MVP.
`finisher_toys` and `toy_parts` use composite keys, and source relationships
remain distinct. Foreign keys and domain checks protect quantities,
relationships, and the Supplier/`flagged_at` invariant. Deletes are restricted
because cascading a referenced relationship could erase traceability evidence.

The relation tables are intentional rather than storing ID lists on `Toy` or
`Finisher`. They support many-to-many relationships, BOM quantity, foreign-key
validation, reverse lookups, and future relationship metadata. Primary and
unique-key indexes cover common forward reads; supplemental indexes cover
reverse lookups such as Part-to-Toy and Supplier-to-Factory.

Production would likely use internal IDs plus external-key mappings when
multiple source systems or tenants exist. PostgreSQL migrations would replace
the local SQLite setup.

## 4. API design

The API is organized around user workflows rather than generic CRUD for every
canonical table:

- `GET /api/finishers` — available Finisher catalog contexts;
- `GET /api/toys?finisher_id=...` — compact Toy summaries for one Finisher;
- `GET /api/toys/{toy_id}?finisher_id=...` — one Toy's Parts and source paths;
- `GET /api/suppliers` — the global Supplier registry;
- `GET /api/suppliers?finisher_id=...` — Supplier registry plus optional
  relevance to a selected Finisher;
- `GET /api/suppliers/{supplier_id}` — read-only Supplier detail with
  Factories and supplied Parts;
- `PATCH /api/suppliers/{supplier_id}` — explicit desired Supplier flag state.

The flag request is conceptually:

```json
{"child_labor_flagged": true}
```

Summary responses do not include the complete traceability graph. Detail
responses include Parts, quantities, statuses, explanations, and possible
source paths. The backend owns classification; the frontend does not
reimplement impact rules. A successful mutation returns authoritative Supplier
state, and the frontend refetches affected summaries and details.

`reason_code` is the stable machine-readable explanation contract. The current
English `reason` is a presentation fallback; a future locale catalog can
translate stable codes without changing domain logic.

## 5. High-level architecture

```text
CSV fixtures
    │
    ▼
Importer: parse, normalize, validate, persist atomically
    │
    ▼
Canonical SQLite model
    │
    ▼
Repository: retrieve filtered traceability facts
    │
    ▼
Impact service: group facts and derive statuses/reasons/paths
    │
    ▼
FastAPI: workflow-oriented JSON contracts
    │
    ▼
React + TypeScript: summaries, filters, and progressive investigation
```

The boundaries are deliberate:

- the importer owns source cleanup and validation;
- the relational model owns durable state and relationships;
- repositories retrieve facts but do not classify risk;
- the pure impact service applies domain rules without HTTP or React
  dependencies;
- FastAPI exposes stable workflow contracts;
- React presents summaries and requests evidence on demand;
- observability adds safe request, import, and mutation context.

## 6. Main flows

### Import and setup

1. The CLI selects `data/full` or `data/demo`.
2. The importer parses blank values and validates all six files.
3. Cross-file references, duplicate conflicts, and domain constraints are
   checked before persistence.
4. Canonical entities and relationships are written in one transaction.
5. Normal `setup` is idempotent and preserves runtime Supplier flags.
6. Explicit `reset` recreates the schema and clears runtime flags.

### Finisher traceability review

1. The user explicitly selects a Finisher; the application never silently
   chooses the first catalog.
2. The API returns compact Toy summaries scoped by `finisher_id`.
3. The UI filters, searches, and paginates that one Toy list.
4. Selecting a Toy loads its detail response on demand.
5. The impact service derives Part and Toy status and returns explanation
   paths through Supplier and Factory.

### Supplier flag mutation

1. The user opens the global Supplier workspace, with or without Finisher
   context.
2. The UI confirms the global effect of flagging or unflagging.
3. FastAPI applies the explicit desired state and `flagged_at` invariant in
   one transaction.
4. The response returns the authoritative Supplier state.
5. The frontend refetches Supplier, Toy summary, and open Toy detail data.

## 7. Deep dives and trade-offs

### Impact calculation

Impact is derived at read time rather than stored as a duplicated Toy status:

- no flagged possible source → `unaffected`;
- a mixture of flagged and unflagged possible sources →
  `potentially_affected`;
- all known possible sources flagged → `affected`.

For a Toy, the highest-severity Part result wins. A Part with no known source
is currently treated as unaffected because it has no flagged path; this is an
evidence limitation, not proof of safety. Source allocation data would be
needed before claiming actual exposure.

Keeping the calculation in a pure service avoids hiding business rules in SQL
or the frontend and makes the three statuses, invalid facts, duplicates, and
unflagging directly testable.

### Ingestion and persistence

SQLite and synchronous SQLAlchemy sessions are appropriate for the assignment's
local dataset and keep setup reproducible. Separating setup from API startup
prevents a restart from resetting Supplier flags. The repository boundary
contains the future storage migration, while the current source identifiers
remain simple and explainable.

### Frontend boundary

The React client has two focused client-side page states rather than a router:

- **Finisher Traceability:** explicit Finisher selection, one searchable and
  status-filtered Toy list, pagination, and Toy investigation;
- **Suppliers:** global search/filter, flag/unflag action, pagination, and
  read-only Supplier detail.

The typed `fetch` client and `useFairToyData` hook coordinate API calls,
loading/error state, mutation state, and authoritative refetches. Progressive
disclosure keeps high-fanout Parts and paths out of the initial catalog
response.

### Observability

The API and CLI emit structured key-value logs. Requests receive safe
`X-Request-ID` correlation, and import/mutation events include outcome,
duration, and record counts without logging credentials, request bodies, or
full traceability payloads. Metrics, distributed tracing, health checks,
alerting, and deployment monitoring remain production follow-up work.

## 8. Scale boundary and production evolution

The current design is intentionally sufficient for the supplied fixture and
the assignment's one-to-three-hour scope. It does not claim production
capacity.

The first changes at larger scale would be:

1. measure query plans, payload sizes, fan-out, and endpoint latency;
2. add server-side filtering, pagination, and lazy Part/source reads;
3. move to PostgreSQL with migrations and connection/concurrency controls;
4. add authentication, authorization, tenant isolation, and audit history;
5. introduce internal identity mappings for multiple source systems;
6. add an incremental materialized impact projection if high-fanout flag
   changes make read-time calculation too expensive;
7. model source allocation by Finisher or production batch before asserting
   actual exposure.

These are evolution points, not hidden requirements of the MVP.

## 9. Verification

The implementation is verified at the boundaries with the highest correctness
and regression risk:

- impact unit tests cover all statuses, mixed sources, unflagging, duplicates,
  and invalid facts;
- importer and database tests cover normalization, references, constraints,
  idempotent setup, and reset behavior;
- API tests cover summaries, detail paths, Supplier detail, mutations, and
  request correlation;
- frontend tests cover the API client, view models, and main workflows;
- Ruff, mypy, TypeScript type checking, a production build, and the complete
  test suites provide the quality gates.
