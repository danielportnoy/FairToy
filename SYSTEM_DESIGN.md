# FairToy system design

## Document status

**Status:** Current design
**Phase:** Implemented MVP
**Source of truth:** [`SPEC.md`](SPEC.md) defines product behavior and
domain semantics. This document defines the technical design that implements
that behavior.

## Design objective

Build the smallest understandable full-stack system that lets a Finisher
trace its toys to possible suppliers and see how a current Supplier
child-labor flag changes the impact status.

The design should favor:

- explicit domain logic;
- reproducible data setup;
- explainable results;
- strong consistency for the current dataset;
- simple local development;
- a clear path to scale without implementing production infrastructure now.

## Proposed architecture

```text
CSV fixtures
    │
    ▼
Importer / normalizer
    │
    ▼
Canonical SQLite database
    │
    ├── relational repository queries
    │
    ▼
Impact-analysis domain service
    │
    ▼
FastAPI application
    │
    ▼
React + TypeScript UI
```

### Source fixtures and importer

The CSVs under the selected `data/demo/` or `data/full/` fixture directory
are treated as external customer-export-style input. An explicit importer
validates relationships and maps source rows into the canonical model
described in [`SPEC.md`](SPEC.md).

The importer should be deterministic and idempotent. It should preserve
distinct relationships, retain nulls for blank optional values, and fail with
actionable errors when required references are invalid.

Import processing should validate the complete source set before writing and
load the canonical data in one transaction. A failed import rolls back rather
than leaving a partial graph. Rerunning normal setup must not duplicate rows or
overwrite runtime Supplier flags; a separate reset operation is required to
recreate the database intentionally.

### Canonical relational store

SQLAlchemy models and constraints will define a file-backed SQLite database.
SQLite is the source of truth for the local application and stores canonical
entities plus the mutable current Supplier flag.

A dedicated setup/import command will create the schema and load the selected
fixture directory, defaulting to `data/full/` in the single local database
`data/generated/fairtoy.sqlite3`. Normal application startup will reuse the
existing database and will not reseed it, so runtime Supplier flags survive
restarts. A separate development reset operation may intentionally replace
that database with either fixture set. The small `data/demo/` fixture is not
loaded alongside `data/full/`: the two sets share identifiers and the
canonical schema has no dataset-isolation dimension.

Generated database files do not belong in version control. A migration system
is deferred for this disposable take-home database.

The accepted canonical table direction is:

- `finishers`
- `toys`
- `finisher_toys`
- `suppliers`
- `factories`
- `parts`
- `toy_parts`
- `part_sources`

Supplier flag state remains on `suppliers`; impact status remains derived.

### Alternatives considered

- **Mirror the CSVs:** simpler initially, but duplicate identifiers and
  relationships become ambiguous.
- **Graph database:** natural traversal semantics, but unnecessary
  infrastructure for this relational dataset.
- **In-memory or JSON:** quick to prototype, but weak persistence and
  relationship validation.

The normalized relational model is preferred because it makes the domain
relationships and impact rules explicit while remaining small enough for the
take-home.

### Identifier strategy

The supplied `toy_id`, `part_id`, `supplier_id`, `factory_id`, and
`finisher_id` values will be used as canonical primary keys for this
assignment. Relationship tables will use composite keys where the
relationship itself is the identity:

- `finisher_toys(finisher_id, toy_id)`
- `toy_parts(toy_id, part_id)`

`part_sources` will enforce uniqueness for each distinct Part/Factory
relationship. Supplier is derived through Factory rather than duplicated on
PartSource. A production multi-source platform may introduce internal
surrogate IDs and retain source identifiers as unique external keys.

Generic internal IDs and `created_at`/`updated_at` fields are intentionally
deferred. The current model has one source system and mostly immutable
imported entities; `flagged_at` is retained because it represents a meaningful
domain event.

### Canonical fields

- `finishers`: `finisher_id`, `finisher_name`, `hq_country`
- `toys`: `toy_id`, `toy_name`
- `finisher_toys`: `finisher_id`, `toy_id`, `retail_price_usd`,
  `units_per_year`
- `suppliers`: `supplier_id`, `supplier_name`, `hq_country`,
  `child_labor_flagged`, `flagged_at`
- `factories`: `factory_id`, `supplier_id`, `factory_name`, `address_line`,
  `city`, `country`
- `parts`: `part_id`, `part_name`
- `toy_parts`: `toy_id`, `part_id`, `quantity`
- `part_sources`: `part_id`, `factory_id`, `unit_cost_usd`

The Supplier for a PartSource is resolved through its Factory.

### Integrity and nullability

Foreign keys will be enabled and relationship identifiers will be required.
Names needed to explain a traceability path and BOM quantities will also be
required.

Optional source and enrichment values remain nullable. This includes factory
address and city, missing location values, optional commercial values, and
`flagged_at` while a Supplier is unflagged. Empty CSV values are normalized to
database `NULL`, not empty strings.

When present, numeric values such as quantities, prices, annual units, and
unit costs must be non-negative. The Supplier flag state must remain
consistent with `flagged_at`.

Deletes of referenced entities will be restricted rather than cascaded. A
development reset may intentionally recreate the complete database. If
destructive CRUD is added later, soft deletion or archival should protect
historical traceability.

### Indexing

Primary keys and unique constraints provide indexes for their key order.
Supplemental indexes will support reverse relationship lookups:

- `finisher_toys.toy_id`;
- `toy_parts.part_id`;
- `part_sources.factory_id`;
- `factories.supplier_id`.

We will not add duplicate indexes for primary-key-leading columns or an index
on the low-cardinality Supplier flag.

### Database access

Use synchronous SQLAlchemy sessions scoped to each FastAPI request. Read
queries use the request session; Supplier flag mutations commit explicitly and
roll back on failure. Async database access is deferred because this local
SQLite workload does not require it.

### Impact-analysis domain service

Repository/database code retrieves relationship facts. A small backend domain
service applies the impact rules from `SPEC.md` and returns status plus
explanation paths.

The repository query should be filtered by Finisher and, for detail views, by
Toy. Its result should contain the Toy, Part, quantity, possible Supplier
sources, Supplier flag state, and Factory details. The domain service groups
these facts by Toy and Part before classifying the result.

The service should not depend directly on HTTP or React. Its core
calculation should be straightforward to test with in-memory examples.

### API and UI

FastAPI exposes workflow-oriented capabilities:

- Finisher catalog listing;
- Finisher toy summaries with impact status;
- Toy traceability detail with explainable paths;
- Supplier state listing/detail;
- Supplier flag/unflag mutation.

The API returns explainable paths rather than only a boolean impact result.
Generic CRUD for every canonical table is deferred.

Toy reads are exposed as a reusable top-level resource with Finisher context
supplied as a filter, conceptually:

- `GET /api/finishers`
- `GET /api/toys?finisher_id={finisher_id}`
- `GET /api/toys/{toy_id}?finisher_id={finisher_id}`
- `GET /api/suppliers`
- `GET /api/suppliers?finisher_id={finisher_id}`
- `GET /api/suppliers/{supplier_id}`
- `PATCH /api/suppliers/{supplier_id}`

The current Supplier risk state is updated with an explicit desired value,
conceptually `PATCH /suppliers/{supplier_id}` with
`child_labor_flagged: true|false`. The backend owns the related
`flagged_at` update; the UI does not toggle based on stale local state.

The unfiltered Supplier collection is the primary Supplier Review read and
returns all Suppliers with current flag state and `flagged_at`. When
`finisher_id` is supplied, it returns one row per unique Supplier reachable
through that Finisher's Toy/Part/source graph, with a related-Toy count where
practical. The filtered form provides contextual relevance; it does not
restrict the global Supplier flag mutation.

Supplier detail is read-only and returns the Supplier, its Factories, and the
Parts for which it is a possible source. Generic editing of those relationships
is out of scope.

List reads should return compact Toy impact summaries. A detail read for one
Toy should return its complete parts, quantities, possible sources, Supplier
flags, Factories, and explanation paths. The frontend loads detail only when a
user opens a Toy.

The measured detail response for a Toy with many Parts is approximately
16.5 KB, which is acceptable for an on-demand read. Keep the detail response
explainable but avoid repeating Toy and Part fields inside every path when
those fields are already present on their parent objects. Include stable
reason codes alongside human-readable reasons. Serialize monetary values
consistently, with decimal strings acceptable when preserving currency
precision.

React presents two top-level pages:

- **Finisher Traceability:** one searchable Toy catalog for the selected
  Finisher with an `All statuses` filter by default, individual
  impact-status filters, ten-row client-side pagination, and Toy
  Investigation drill-down;
- **Suppliers:** a global Supplier registry with search/filter controls,
  flag/unflag actions, and Supplier detail for Factories and supplied Parts.

Toy Investigation shows the selected Toy's Parts and possible source paths,
with contextual Supplier flag actions. Supplier detail is read-only. Neither
page renders the entire relationship graph as one equally weighted page.

The first Finisher Traceability visit requires explicit Finisher selection
because authentication and user accounts are out of scope. Suppliers can be
opened without a selected Finisher. When present, the selected Finisher
remains visible on the traceability page and may provide relevance context on
the Supplier page. The UI uses progressive disclosure: summaries and risk
signals come first, while Parts, source paths, Factories, and supplied Parts
are opened on demand.

The current MVP reuses the existing compact Toy summary and on-demand detail
endpoints. It may derive simple status counts from the loaded summary list;
it does not add a separate Toy overview endpoint, exposure projection, or
server-side pagination for the take-home. The browser paginates the loaded
summary list in ten-row pages. Supplier Review uses the global Supplier
collection by default and may use the focused `finisher_id` query only for
relevance context, rather than fetching every Toy detail in the browser.
Supplier detail may use one focused read rather than reconstructing its
Factories and Parts from Toy details. The UI must still represent loading,
empty, error, and mutation states. Full administration navigation is deferred.

Frontend API calls will be centralized behind a small typed client using the
browser's native `fetch`. After a Supplier mutation, the dashboard will
refetch the relevant summaries and detail rather than maintain a second
client-side impact calculation.

Exact field names and frontend route mechanics remain implementation details;
the summary/detail and explainability contract above is accepted.

### Verification strategy

The impact-analysis service will have unit tests for the three statuses,
alternative sources, unflagging, and cross-Finisher visibility. Importer and
database integration tests will verify canonical row relationships, null
handling, foreign keys, and idempotent setup. API integration tests will cover
summary reads, detail paths, and Supplier flag persistence.

The frontend will be verified with a production build and a manual
end-to-end workflow. A full browser automation suite is deferred.

## Design constraints

- Python API and React frontend are required.
- Authentication, multi-tenancy, real-time updates, and deployment are out
  of scope.
- Supplier flags are global in the current bounded context.
- Impact status is derived from current flags and relationships.
- The current dataset is small enough for read-time calculation.
- A future materialized impact projection may be introduced if high-fanout
  reads become a bottleneck.

## Design status

The schema, importer, repository boundaries, API contract, impact service,
and frontend information architecture are resolved and implemented. Exact
client-side route mechanics remain an implementation detail. The MVP scale
boundary is documented in D038: add server-side pagination or an impact
projection only when observed fan-out, payload size, or latency justifies it.

## Deferred production extensions

- event-driven recalculation and a materialized impact read model;
- server-side pagination or lazy loading for high-fanout Parts and source
  paths;
- factory-level risk observations;
- risk history, evidence, actors, and approvals;
- source allocation per Finisher or production batch;
- authentication, tenant isolation, and permissions;
- full CRUD and operational workflows;
- data-quality states for incomplete traceability;
- annual-unit exposure metrics and locale-specific explanation catalogs.
