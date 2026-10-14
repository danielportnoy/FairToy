# FairToy decisions

This log records deliberate choices and important deferred extensions. It is
not a transcript of the planning conversation.

## D001 — Optimize for traceability, not generic CRUD

- **Status:** Accepted
- **Decision:** The required product is a Finisher-focused traceability and
  impact-analysis workflow. Source entities are initialized through an
  importer; generic CRUD is optional follow-up work.
- **Rationale:** Traceability is the core requirement and the assignment is
  time-limited. CRUD should not displace the core workflow.

## D002 — Use a canonical spec and phased implementation

- **Status:** Accepted
- **Decision:** Maintain one `SPEC.md`, this decision log, and a process log.
  Implement in bounded phases with human review between AI-assisted slices.
- **Rationale:** The company prefers spec-driven development, and the
  candidate must be able to explain the process and decisions.

## D003 — Treat CSVs as external fixtures

- **Status:** Accepted
- **Decision:** The six CSVs are customer-export-style input data. They will be
  transformed into a canonical model rather than exposed as the application's
  schema.
- **Rationale:** The assignment explicitly allows transformation,
  normalization, restructuring, and omission of irrelevant data.

## D004 — Model Toy independently from Finisher

- **Status:** Accepted
- **Decision:** A canonical `Toy` has `FinisherToy` relationships. Finisher
  specific price and annual volume belong on the relationship.
- **Rationale:** The source contains the same toy identifier in multiple
  Finisher rows with different commercial values.

## D005 — Model Part sources as relationships

- **Status:** Accepted
- **Decision:** A canonical `Part` has one or more `PartSource` relationships
  to Suppliers and Factories. `ToyPart` stores BOM quantities.
- **Rationale:** Source rows contain repeated part identifiers with different
  supplier and factory relationships.

## D006 — Treat PartSource as a possible source

- **Status:** Accepted
- **Decision:** A PartSource is a possible or approved sourcing option, not
  proof that a particular toy used that source.
- **Rationale:** The BOM identifies a Part but does not identify the Supplier
  that produced the instance.

## D007 — Use three impact states

- **Status:** Accepted
- **Decision:** Derive `unaffected`, `potentially affected`, or `affected`.
  A mixed flagged/unflagged source set is potentially affected; all known
  sources flagged is affected.
- **Rationale:** This represents the certainty available in the source data
  without hiding possible exposure or claiming unsupported certainty.

## D008 — Supplier flags are global

- **Status:** Accepted
- **Decision:** The current child-labor flag belongs to the Supplier and is
  reflected for every relevant Finisher. The UI filters the catalog by
  Finisher.
- **Rationale:** Authentication and multi-tenancy are explicitly out of scope,
  and the current business rule identifies the Supplier as the risk subject.

## D009 — Store current risk state on Supplier

- **Status:** Accepted
- **Decision:** Store the current child-labor state and timestamp on Supplier.
  Do not create a separate risk-history entity for the take-home.
- **Rationale:** The minimum workflow needs current flag/unflag behavior.
  Evidence, actors, approvals, and history are future extensions.

## D010 — Derive impact status on read

- **Status:** Accepted
- **Decision:** Store the Supplier flag as source state and calculate impact
  dynamically from current relationships and flags.
- **Rationale:** The dataset is small, this avoids stale duplicated status, and
  it gives immediate consistency after flagging or unflagging.
- **Future:** Use an incremental materialized projection or event-driven
  recalculation if high-fanout reads become a scale bottleneck.

## D011 — Keep Factory contextual for now

- **Status:** Accepted
- **Decision:** Factories appear in traceability paths but cannot be
  independently flagged in the current app.
- **Rationale:** The minimum behavior is Supplier flagging. Factory-specific
  findings require additional evidence and precedence rules.
- **Future:** Add factory-level risk observations and define how they combine
  with Supplier-level findings.

## D012 — Keep industry-context actors out of the bounded context

- **Status:** Accepted
- **Decision:** Retailers, Basic Materials companies, raw materials, orders,
  and recalls are documented as future extensions, not implemented entities.
- **Rationale:** They appear in the industry narrative but are not represented
  in the supplied data or required traceability workflow. Inventing their
  relationships would add unsupported behavior.

## D013 — Preserve nulls and validate imports

- **Status:** Accepted
- **Decision:** Preserve blank optional source fields as null, preserve
  distinct relationships, safely deduplicate exact duplicates, and fail
  clearly on invalid references.
- **Rationale:** This keeps source quality visible and makes setup
  deterministic and reproducible.

## D014 — Use a small relational stack

- **Status:** Accepted
- **Decision:** Use FastAPI, SQLite, React, TypeScript, and Vite with
  relational joins.
- **Rationale:** The stack meets the requirements, fits the dataset and time
  limit, and maps directly to the traceability relationships. Graph storage
  and external infrastructure are unnecessary for this slice.

## D015 — Defer low-level system design

- **Status:** Deferred
- **Decision:** Decide exact tables, indexes, API endpoints, response shapes,
  frontend routes, and flag-request semantics during the system-design phase.
- **Rationale:** The current phase establishes domain intent and boundaries;
  implementation details should follow the approved spec.
