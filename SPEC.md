# FairToy specification

## Document role

This document is the product and domain contract. It defines the user outcome,
scope, domain semantics, assumptions, and acceptance criteria.

- [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md) explains how the contract is
  implemented.
- [`DECISIONS.md`](DECISIONS.md) records alternatives and trade-offs.
- [`PROCESS_LOG.md`](PROCESS_LOG.md) records how the contract evolved and how
  implementation slices were verified.

## Product outcome

A Finisher should be able to understand which Toys may be exposed to a
Supplier child-labor issue, see why, and take the next risk-review action.

The core evidence path is:

> Toy → Part → Supplier → Factory

The primary user is a Finisher operations or compliance user reviewing a
product catalog, not an administrator managing every underlying record.

## Scope

### Included

- Import the six customer-export-style CSVs into a canonical model.
- Browse a selected Finisher's Toy catalog.
- Trace a Toy through Parts, possible Suppliers, and Factories.
- Review all Suppliers in a global Supplier workspace.
- Flag or unflag a Supplier for child labor.
- Derive and display each Toy's current impact status with explanations.
- Persist the current Supplier flag across application restarts.

### Excluded

- Retailers, Basic Materials companies, and raw-material relationships.
- Orders, order halts, recalls, or other downstream operational workflows.
- Factory-level risk flags.
- Evidence, approvals, actors, risk history, or audit workflows.
- Authentication, authorization, and multi-tenancy.
- Notifications, email, websockets, and real-time updates.
- Deployment infrastructure and production observability platforms.
- Generic CRUD screens for every imported entity.

These are deliberate boundaries, not unresolved requirements.

## Canonical domain model

The CSVs are external input fixtures, not the application's domain schema.
The importer transforms it into these canonical relationships:

- `Finisher → FinisherToy → Toy`
- `Toy → ToyPart → Part`
- `Part → PartSource → Factory → Supplier`

`FinisherToy` stores catalog-specific commercial values such as retail price
and annual volume. `ToyPart` stores BOM quantity. `PartSource` stores
source-specific values such as unit cost. Supplier risk state and
`flagged_at` live on `Supplier`; Factory is traceability context, not an
independently flaggable risk subject.

The supplied BOM identifies a Part, but not the source that produced a
particular instance. A `PartSource` is therefore possible evidence, not proof
that every Toy using the Part used that Supplier.

## Impact calculation

Impact status is derived from current relationships and Supplier flags. It is
not stored as a duplicated status column.

For each Part:

- no flagged possible sources → `unaffected`;
- some flagged and some unflagged possible sources →
  `potentially_affected`;
- all known possible sources flagged → `affected`.

For each Toy, the highest-severity Part result wins:

1. any affected Part → `affected`;
2. otherwise, any potentially affected Part → `potentially_affected`;
3. otherwise → `unaffected`.

The result is calculated at canonical Toy level and appears for every
Finisher–Toy relationship because Supplier flags and the current BOM/source
model are global. Every result includes the path and reason that produced it.

The MVP treats a Part with no known sources as unaffected because it has no
flagged path. This is a known evidence limitation, not proof that the Part is
safe; a future product could distinguish `needs_review` or incomplete
traceability.

## Source-data assumptions

- The CSVs are external, flat customer exports; repeated identifiers represent
  relationships rather than independent canonical entities.
- A Toy may appear in multiple Finisher catalogs with different commercial
  values. A Part may have multiple possible sources.
- Exact duplicate rows may be deduplicated, but conflicting or distinct
  relationships must not be silently overwritten.
- Optional blank values remain null and invalid references fail validation with
  an actionable error.
- Import is deterministic and idempotent; normal setup preserves runtime
  Supplier flags, while reset is an explicit database recreation.

These are modeling assumptions about a messy customer export, not claims about
the customer's upstream systems.

## Product behavior

### Finisher Traceability

- The first catalog visit requires explicit Finisher selection; the UI must
  not silently choose an arbitrary catalog.
- One Toys list uses `All statuses` by default and supports search, explicit
  status filters, and ten-row client-side pagination.
- Selecting a Toy opens an investigation with progressive disclosure of Parts
  and possible source paths.
- The backend owns classification; the frontend presents status, reason, and
  evidence paths.

### Supplier Review

- Suppliers is a global registry and can be opened without a selected
  Finisher.
- Users can search, filter flagged/unflagged state, open read-only Supplier
  detail, and inspect Factories and supplied Parts.
- A selected Finisher may provide relevance counts. An unrelated Supplier can
  still be flagged, with the UI explaining that it has no current Toy impact
  for that catalog.

### Supplier mutation

- Flagging and unflagging use explicit desired state and require confirmation
  because the state is global.
- After a successful mutation, the authoritative Toy summaries, Toy detail,
  Supplier list, and Supplier detail are refreshed.
- No real-time push behavior is required; users see current state on load or
  refresh.

### Explanation contract

Every impact result includes a stable machine-readable `reason_code` and a
human-readable reason. The current UI presents English reasons; a future
locale catalog can translate stable codes without changing domain logic.

## Acceptance criteria

- A fresh setup imports the selected fixture set reproducibly.
- A user explicitly selects a Finisher and browses its Toy catalog.
- A user can filter/search/paginate Toys and open any Toy investigation.
- A Toy investigation shows Parts, quantities, possible Suppliers, and
  Factories with status and explanation paths.
- A user can open Supplier Review without selecting a Finisher.
- A user can inspect Supplier detail and flag or unflag a Supplier.
- A mixed source set produces `potentially_affected`; an all-flagged known
  source set produces `affected`; no flagged source produces `unaffected`.
- Unflagging changes the next authoritative calculation, and a global flag is
  reflected for every relevant Finisher.
- Import, domain, API, and frontend boundaries have automated checks and the
  repository has runnable setup instructions.

## Deliberate future boundaries

- Source allocation per Finisher or production batch.
- Factory-level risk observations and precedence.
- Supplier risk history, evidence, actors, and approvals.
- A distinct incomplete-traceability/needs-review state.
- Exposure metrics based on annual units or affected production.
- Materialized impact projections and event-driven recalculation at scale.
- Server-side pagination or lazy loading for high-fanout detail reads.
- Optional CRUD and operational workflows.
