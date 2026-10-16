# FairToy system design

## Document role

**Status:** Implemented MVP

[`SPEC.md`](SPEC.md) is the product and domain source of truth. This document
explains the technical design that implements it. Detailed alternatives and
iteration history are in [`DECISIONS.md`](DECISIONS.md) and
[`PROCESS_LOG.md`](PROCESS_LOG.md).

## Architecture

```text
CSV fixtures → importer/normalizer → canonical SQLite database
                                      │
                                      ▼
                              repository queries
                                      │
                                      ▼
                          pure impact-analysis service
                                      │
                                      ▼
                               FastAPI API
                                      │
                                      ▼
                             React + TypeScript UI
```

The boundaries are intentional:

- ingestion owns source cleanup and validation;
- the relational model owns durable state and relationships;
- the repository retrieves facts but does not classify risk;
- the domain service classifies facts without HTTP or React dependencies;
- FastAPI exposes workflow-oriented contracts;
- React presents summaries and loads evidence on demand;
- observability provides safe request/import/mutation context without a
  monitoring platform.

## Key design choices

- **Relational model over a graph database:** the source is tabular, the
  relationships are explicit, and constraints/transactions matter more than
  generic graph traversal for this workflow.
- **SQLite now, PostgreSQL later:** the local dataset needs persistence but
  not production concurrency or infrastructure; the repository boundary keeps
  the storage change contained.
- **Read-time impact calculation:** Supplier flags are mutable source state,
  while impact is derived to avoid stale duplicated status.
- **Workflow APIs over generic CRUD:** each endpoint supports a user action
  and keeps the traceability contract explainable.
- **Summary/detail reads and progressive disclosure:** list screens stay
  compact, while high-fanout Parts and paths load only when requested.

### Source fixtures and importer

The CSVs are external customer-export-style inputs. The importer:

1. parses and normalizes blank values;
2. deduplicates exact canonical duplicates and rejects conflicts;
3. validates all cross-file references before writing;
4. persists the canonical graph in one transaction.

Normal `setup` is an idempotent upsert that preserves runtime Supplier flags.
`reset` explicitly drops and recreates the schema. Both use the same default
database path; the fixture set can be selected with `--data-dir`.

### Canonical relational store

SQLAlchemy models define a file-backed SQLite database with these tables:

`finishers`, `toys`, `finisher_toys`, `suppliers`, `factories`, `parts`,
`toy_parts`, and `part_sources`.

The source identifiers are primary keys for this single-source MVP.
`finisher_toys(finisher_id, toy_id)` and `toy_parts(toy_id, part_id)` use
composite keys; `part_sources(part_id, factory_id)` preserves distinct source
paths. Supplier is derived through Factory, preventing duplicated Supplier
ownership data.

Foreign keys, non-negative numeric constraints, nullable enrichment fields,
and the Supplier/`flagged_at` invariant protect the graph. Reverse lookup
indexes support catalog and Supplier queries. Deletes are restricted because
removing a referenced relationship would erase traceability evidence.

SQLite and synchronous request-scoped SQLAlchemy sessions are appropriate for
the local dataset. Production would use PostgreSQL, migrations, and a
multi-source identity strategy with internal IDs plus external-key mappings.

### Impact-analysis service

The repository returns flat traceability facts filtered by Finisher and,
optionally, Toy. The pure domain service groups those facts by Toy and Part,
validates consistency, and applies the rules from `SPEC.md`. It returns status,
reason code, human-readable reason, and explainable paths.

This separation keeps SQL focused on retrieval and keeps business rules
testable without FastAPI, SQLAlchemy, or React.

### API contract

FastAPI exposes workflow-oriented resources:

- `GET /api/finishers` — catalog contexts;
- `GET /api/toys?finisher_id=...` — compact Toy impact summaries;
- `GET /api/toys/{toy_id}?finisher_id=...` — one Toy's evidence paths;
- `GET /api/suppliers` — global Supplier Review;
- `GET /api/suppliers?finisher_id=...` — optional catalog relevance;
- `GET /api/suppliers/{supplier_id}` — read-only Supplier detail;
- `PATCH /api/suppliers/{supplier_id}` — explicit flag state.

The Toy list is compact; Parts and source paths are loaded on demand. Supplier
mutations update `flagged_at` in the same transaction and return the
authoritative Supplier state. The frontend refetches affected summaries and
details instead of calculating impact independently.

### Frontend workflow

React is a single-page application with two client-side page states rather
than a router:

- **Finisher Traceability:** explicit Finisher selection, one searchable
  status-filtered Toy list, ten-row client-side pagination, and Toy
  Investigation.
- **Suppliers:** global search/filter, explicit flag/unflag action, ten-row
  pagination, and read-only Supplier detail.

The typed `fetch` client and `useFairToyData` hook own API calls, loading/error
states, mutation state, and authoritative refetches. Progressive disclosure
keeps high-fanout Parts and paths out of the initial catalog response.

### Observability

The API and CLI use standard-library structured logs. Requests receive safe
`X-Request-ID` correlation, and import/mutation events include outcome,
duration, and record counts without logging credentials, request bodies, or
full traceability payloads. Metrics, tracing backends, health endpoints,
alerting, and deployment monitoring are intentionally deferred.

## Scale boundary

The MVP is deliberately sized for a local dataset and read-time
classification:

- compact Toy summaries are loaded for the selected Finisher;
- Toy detail is loaded only on demand;
- browser pagination is sufficient for the current catalog;
- SQLite and synchronous sessions keep local setup simple.

The first production changes would be server-side pagination/lazy source
reads, query-plan and latency measurement, PostgreSQL with migrations, and an
incremental materialized impact projection if flag fan-out makes read-time
calculation expensive. Source allocation by Finisher or production batch is
also needed before claiming actual exposure rather than possible exposure.

## Verification

The implementation is verified at the boundaries that carry the most risk:

- impact unit tests cover all statuses, mixed sources, unflagging, duplicates,
  and invalid facts;
- importer/database tests cover normalization, references, constraints,
  idempotent setup, and reset behavior;
- API tests cover summaries, detail paths, Supplier detail, mutations, and
  request correlation;
- frontend tests cover API/view-model boundaries and the main workflow;
- Ruff, mypy, TypeScript type checking, and a production build complete the
  quality gates.
