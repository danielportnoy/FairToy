# FairToy process log

This log records the working flow, checkpoints, AI boundaries, and review
outcomes. It intentionally summarizes the process rather than copying the
full conversation.

## 2026-10-14 — Domain framing

- **Phase:** Domain discovery and scope definition
- **Status:** Complete
- **Human decisions:**
  - prioritize Finisher-to-toy traceability over generic CRUD;
  - treat the CSVs as external customer-export fixtures;
  - define a canonical Toy/FinisherToy and Part/PartSource model;
  - distinguish unaffected, potentially affected, and affected;
  - keep Supplier risk global and Factory risk contextual for now;
  - defer retailers, basic materials, raw materials, orders, recalls, and
    risk-history workflows.
- **AI role:** challenge assumptions, expose ambiguity, propose alternatives,
  and keep the decision tree explicit.
- **Review outcome:** domain decisions were accepted by the candidate; API and
  physical implementation details remain intentionally deferred.

## 2026-10-14 — System design started

- **Phase:** System design
- **Status:** In progress
- **Artifact:** [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md)
- **Boundary:** technical choices may now be made, but only against the
  approved product specification.
- **First design focus:** canonical relational schema and reproducible
  database initialization.
- **Decision accepted:** use SQLAlchemy with file-backed SQLite; separate
  setup/import from normal application startup so Supplier flags persist.
- **Decision accepted:** use a normalized relational model with explicit
  Finisher/Toy and Part/source relationship tables instead of mirroring the
  flat CSVs.
- **Decision accepted:** use supplied source identifiers as canonical keys for
  this assignment, with composite keys for relationship tables.
- **Decision accepted:** require graph identity and relationship fields while
  preserving missing optional and enrichment values as null.
- **Decision accepted:** protect referenced traceability relationships with
  foreign keys and restricted deletes.
- **Decision accepted:** validate and import source data atomically, while
  keeping normal seeding separate from runtime Supplier state.
- **Decision accepted:** retrieve filtered traceability facts from the
  database and classify impact in a testable backend domain service.
- **Decision accepted:** shape the API around the Finisher traceability
  workflow rather than generic CRUD resources.
- **Decision accepted:** update Supplier child-labor state with an explicit
  desired value rather than a toggle operation.
- **Decision accepted:** separate compact dashboard summaries from
  on-demand full Toy traceability details.
- **Decision accepted:** use one focused Finisher dashboard rather than
  unrelated administration screens.
- **Decision accepted:** focus automated tests on the domain, importer, and
  API boundaries, with a frontend build and manual workflow check.
- **Decision accepted:** rely on automatic primary/unique-key indexes and add
  only supplemental reverse-relationship indexes.
- **Decision accepted:** use synchronous request-scoped SQLAlchemy sessions
  with explicit transactions for Supplier flag mutations.
- **Decision accepted:** avoid generic internal IDs and lifecycle timestamps
  until the product needs their semantics.
- **Decision accepted:** keep Factory as the PartSource site node and derive
  Supplier through Factory while retaining direct Supplier flag state.
- **Decision accepted:** scope Toy summary and detail reads under the
  selected Finisher while keeping Supplier updates global.
- **Decision accepted:** expose Toys as a reusable top-level resource and use
  the selected Finisher as the dashboard filter.
- **Decision accepted:** use a small typed frontend API client over native
  `fetch` and keep server data authoritative.

## 2026-10-15 — Foundation / Slice 1

- **Phase:** Foundation
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add the `src/fairtoy` package, SQLAlchemy models, file-backed
  SQLite setup, deterministic CSV importer, and setup/reset CLI commands.
- **Importer behavior:** validate the complete six-file source set before
  writing, preserve nulls, deduplicate exact rows, preserve distinct
  relationships, reject invalid references, import atomically, and preserve
  runtime Supplier flags on normal setup.
- **Repository boundary:** the importer is operational setup tooling, not a
  user-facing product workflow. API, impact analysis, and frontend work remain
  deferred to later slices.
- **Verification:** five automated tests passed; syntax, diff, and CLI reset
  plus idempotent setup checks passed against the supplied fixtures.
- **Review gate:** do not begin the next implementation slice until this
  foundation is reviewed and accepted.

## 2026-10-15 — Core behavior / Slice 2

- **Phase:** Core behavior
- **Status:** Implemented; pending human review and acceptance
- **Scope:** refactor the pure impact-analysis service into focused contracts,
  validation, classification, and calculation modules while preserving its
  public `fairtoy.impact` imports.
- **Domain behavior:** classify Parts as unaffected, potentially affected, or
  affected from current possible-source flags; classify Toys using affected
  over potentially affected precedence; preserve global Toy-level semantics
  independent of Finisher context.
- **Input handling:** deduplicate identical source facts, order results
  deterministically, and reject contradictory names, Supplier flags, source
  relationships, quantities, or mixed source/no-source facts.
- **Verification:** 14 automated tests passed, including the full Slice 1
  importer suite and Slice 2 status, precedence, unflagging, ordering, and
  invalid-input coverage.
- **Readability outcome:** the public facade remains small; input contracts,
  consistency validation, status rules, and orchestration are now separately
  reviewable. No API, repository, or frontend behavior was introduced.
- **Review gate:** do not begin repository/API integration until this service
  is reviewed and accepted.

## 2026-10-15 — Repository boundary / Slice 3

- **Phase:** Core behavior
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add a synchronous `TraceabilityRepository` that maps the
  canonical SQLAlchemy graph to Finisher-scoped `ToyTraceability` contracts.
- **Query behavior:** preserve Toys with no BOM rows, preserve Parts with no
  possible sources through left joins, derive Supplier through Factory, filter
  detail reads by Finisher/Toy membership, and order results deterministically.
- **Domain contract:** retain Finisher catalog context while keeping the
  impact facts and Supplier state global at the canonical Toy level.
- **Verification:** 21 automated tests passed, including the importer and
  impact suites plus repository filtering, source mapping, empty-Toy,
  no-source-Part, and cross-Finisher coverage.
- **Review gate:** do not begin API or frontend integration until this
  repository boundary is reviewed and accepted.

## 2026-10-15 — Read-only API / Slice 4

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add a small FastAPI application factory and workflow-oriented
  read endpoints for Finishers, Finisher-filtered Toy summaries and details,
  and Suppliers.
- **Boundary behavior:** create one synchronous SQLAlchemy session per
  request, map repository contracts to typed response schemas, calculate
  impact on read, and return a clear not-found response when a Toy is outside
  the selected Finisher catalog.
- **Verification:** API integration tests use a temporary imported SQLite
  database and cover list responses, derived impact summaries, explainable
  detail paths, and Finisher catalog scoping.
- **Explicit deferral:** Supplier flag/unflag mutation and the frontend remain
  separate slices; this change does not add generic CRUD or authentication.
- **Review gate:** review the read-only API contract before implementing
  Supplier mutation or the frontend.

## 2026-10-15 — Detail response contract review

- **Phase:** User workflow
- **Status:** Accepted refinement; implementation follow-up required
- **Observation:** The real Toy detail response is approximately 16.5 KB for
  a Toy with many Parts, which is acceptable for an on-demand detail read.
- **Decision:** Keep full paths on detail responses, keep summary responses
  compact, remove redundant parent identifiers from path objects where
  practical, and add stable reason codes alongside human-readable reasons.
- **Serialization:** Keep monetary values consistent; decimal strings are
  acceptable when preserving currency precision.

## 2026-10-15 — API response contract / D035

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add stable reason codes to Toy and Part impact responses, keep
  summary responses compact, and remove redundant Toy and Part fields from
  nested detail paths.
- **Serialization:** Detail path `unit_cost_usd` values are emitted as
  decimal strings or null, preserving the domain value without float
  conversion.
- **Compatibility:** Existing endpoints, Finisher validation, catalog
  scoping, deterministic ordering, and impact semantics are unchanged.
- **Verification:** focused API tests passed (`6 passed`); full suite passed
  (`27 passed`). The environment reports nine third-party Python 3.14
  deprecation warnings from FastAPI/Starlette.
- **Explicit deferral:** Supplier mutation, frontend work, and unrelated
  refactoring remain out of scope.

## 2026-10-15 — Supplier risk mutation / Slice 5

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add an explicit `PATCH /api/suppliers/{supplier_id}` operation
  accepting the desired `child_labor_flagged` state.
- **State transition:** flagging records a UTC `flagged_at` timestamp,
  repeated identical flag requests preserve that timestamp, and unflagging
  clears it. The database invariant remains enforced.
- **Transaction boundary:** the API commits the repository update explicitly,
  rolls back on SQLAlchemy errors, and returns `404` for an unknown Supplier.
- **Request contract:** Pydantic uses strict boolean validation and rejects
  unknown PATCH body fields before the repository is called.
- **Workflow behavior:** the next Toy detail read reflects the updated global
  Supplier flag through the existing impact calculation.
- **Verification:** focused API tests passed (`15 passed`) and the full suite
  passed (`36 passed`), covering explicit flagging, strict request validation,
  idempotent repeats, unflagging, recalculation, and not-found behavior.
- **Explicit deferral:** frontend work, generic CRUD, authentication, and
  unrelated persistence changes remain out of scope.

## 2026-10-15 — Quality gates / Slice 6

- **Phase:** Verification
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add focused Ruff lint/format checks, mypy type checking, and
  documented local commands alongside the existing pytest suite.
- **Boundary:** no deployment, CI service, runtime feature, or infrastructure
  was added.
- **Verification:** Ruff lint and format checks passed, mypy reported no
  issues in 14 source files, and the full test suite passed (`36 passed`).
  Compilation and diff-whitespace checks also passed. The test environment
  still reports 11 third-party Python 3.14 deprecation warnings.

## 2026-10-15 — Importer boundaries / Slice 7

- **Phase:** Foundation maintainability
- **Status:** Implemented; pending human review and acceptance
- **Scope:** split importer contracts, CSV parsing, source normalization and
  reference validation, and database persistence into focused modules.
- **Compatibility:** `fairtoy.importer.read_source_data` and
  `fairtoy.importer.import_fixtures` remain the public entry points, with
  existing record and summary imports re-exported through the façade.
- **Behavior:** preserve deterministic ordering, duplicate handling, actionable
  validation errors, atomic persistence, and Supplier-flag preservation.
- **Verification:** importer tests passed (`5 passed`); full suite passed
  (`36 passed`). Ruff, format, mypy, compilation, and diff checks passed.
- **Explicit deferral:** schema changes, API behavior, and new importer
  capabilities remain out of scope.

## 2026-10-15 — Setup transaction boundaries / Slice 8

- **Phase:** Foundation maintainability
- **Status:** Implemented; pending human review and acceptance
- **Scope:** clarify CLI configuration and setup/reset error boundaries without
  changing the canonical schema or importer semantics.
- **Behavior:** validate the complete fixture set before an explicit reset can
  drop an existing database; normal setup continues to preserve Supplier flags,
  while a valid reset recreates the database and clears runtime state.
- **Compatibility:** existing `fairtoy setup` and `fairtoy reset` commands,
  path flags, and importer entry points remain available.
- **Verification:** focused CLI/importer tests passed (`7 passed`); the full
  suite passed (`38 passed`), with Ruff, format, mypy, compilation, and diff
  checks also passing. The environment still reports 11 third-party Python
  3.14 deprecation warnings.
- **Explicit deferral:** migrations, deployment infrastructure, and unrelated
  database abstractions remain out of scope.

## Working method

1. Human defines or approves the product boundary and business semantics.
2. The current specification and decision log are updated.
3. AI receives one bounded implementation or design task at a time.
4. Human reviews the complete result and runs the relevant checks.
5. Decisions or rejected suggestions are recorded before the next phase.

AI is an implementation accelerator, not the product decision-maker.

## Planned phases

1. **System design:** choose the physical schema, importer boundary, query
   strategy, API contract, and frontend shape.
2. **Foundation:** scaffold the backend/frontend and reproducible data setup.
3. **Core behavior:** implement and test supplier flags and impact analysis.
4. **User workflow:** build the Finisher dashboard and traceability detail.
5. **Verification and handoff:** run checks, review the diff, complete the
   README, and document future work.

No rigid time allocation is being committed to. The requirements and
specification are the gates; optional features cannot displace the required
workflow.

## Deferred questions

- Exact relational tables and constraints.
- Import command and migration lifecycle.
- API endpoints and request/response contracts.
- Query/index design and repository boundaries.
- Frontend route and component structure.
- How optional CRUD would be introduced after the core workflow.
- How factory-level flags and risk history would work in a later version.
