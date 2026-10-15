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
