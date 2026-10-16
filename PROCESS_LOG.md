# FairToy process log

This log records the working flow, checkpoints, AI boundaries, and review
outcomes. It intentionally summarizes the process rather than copying the
full conversation.

## Current handoff state

- `SPEC.md` is the product and domain contract.
- `SYSTEM_DESIGN.md` is the current technical design.
- `DECISIONS.md` contains accepted decisions; superseded iterations are
  marked rather than treated as current requirements.
- The current workflow is two top-level pages: Finisher Traceability and
  Suppliers. Toy and Supplier details are drill-downs within those pages.
- `data/full/` is the default fixture set for the single local SQLite
  database; `data/demo/` remains available for focused UI work and tests.
- The implemented operational boundary includes structured application logs,
  safe request correlation, and import/mutation lifecycle events. Metrics,
  tracing platforms, health endpoints, and deployment monitoring remain
  deferred.
- The latest verified Python suite has 55 passing tests; frontend checks are
  recorded in the implementation entries below.

The dated entries that follow are historical checkpoints, not an additional
source of requirements.

## Process summary

The work followed five deliberate phases:

1. **Frame the domain:** identify the Finisher outcome, separate required
   traceability from industry context, and write the first product contract.
2. **Resolve ambiguity:** record assumptions about repeated CSV identifiers,
   possible versus actual sources, global Supplier risk, impact certainty, and
   missing evidence.
3. **Design the system:** choose the normalized relational model, importer
   boundary, pure impact service, workflow APIs, and progressive-disclosure
   UI.
4. **Implement in slices:** build and review ingestion, impact rules,
   repository/API boundaries, Supplier mutation, and the two frontend
   workspaces; revise the spec when product decisions changed.
5. **Verify and refine:** test each boundary, run type/build/lint checks,
   exercise the demo workflow, and add a bounded observability foundation
   without expanding into production infrastructure.

The human-owned decisions are captured in `SPEC.md` and `DECISIONS.md`.
AI was used as an implementation and review accelerator; it did not replace
the product choices, scope decisions, or responsibility to understand the
resulting code.

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

## 2026-10-15 — Edge-case coverage / Slice 9

- **Phase:** Verification
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add focused tests for empty Toys, invalid impact facts, malformed
  numeric fixture values, and missing fixture files while retaining the
  supplied real-fixture integration coverage.
- **Behavior:** no production behavior or API contract changes.
- **Verification:** focused domain/importer tests passed (`19 passed`); the
  full suite passed (`43 passed`), with Ruff, format, mypy, compilation, and
  diff checks also passing. The environment still reports 11 third-party
  Python 3.14 deprecation warnings.
- **Explicit deferral:** browser automation, deployment infrastructure, and
  unrelated feature work remain out of scope.

## 2026-10-15 — Finisher dashboard / Slice 10

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add the focused React/TypeScript Finisher dashboard against the
  existing API, including a typed native-fetch client, compact Toy summaries,
  on-demand Toy detail paths, and contextual Supplier flag controls.
- **UI behavior:** represent loading, empty, error, and mutation states; keep
  server impact results authoritative; refetch summaries and detail after a
  Supplier update.
- **Boundary:** the Vite development server proxies `/api` to the local
  FastAPI server. No new backend endpoints, authentication, generic CRUD, or
  deployment infrastructure were added.
- **Verification:** `npm install`, `npm run typecheck`, and `npm run build`
  passed. The Python suite passed (`43 passed`), Ruff, format, mypy,
  compilation, and diff checks passed. A local smoke check confirmed the
  FastAPI endpoint, Vite app, and Vite `/api` proxy are reachable. The
  environment still reports 11 third-party Python 3.14 deprecation warnings.
- **Explicit deferral:** browser automation, advanced client-side caching, and
  unrelated screens remain out of scope.

## 2026-10-15 — Frontend API boundary tests / Slice 11

- **Phase:** Verification
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add a focused Vitest suite for the typed frontend API client.
- **Coverage:** verify Finisher query encoding, explicit Supplier PATCH
  payloads, response handling, and conversion of API error details to a typed
  `ApiError`.
- **Behavior:** no UI, backend, or API contract changes.
- **Verification:** frontend tests passed (`3 passed`), typecheck and
  production build passed. The Python suite passed (`43 passed`), Ruff,
  format, mypy, compilation, and diff checks passed. The environment still
  reports 11 third-party Python 3.14 deprecation warnings.
- **Explicit deferral:** browser component automation, advanced client-side
  caching, and unrelated frontend features remain out of scope.

## 2026-10-15 — Frontend workflow coverage / Slice 12

- **Phase:** Verification
- **Status:** Implemented; pending human review and acceptance
- **Scope:** add a DOM-based dashboard test for the Finisher-to-Toy detail
  workflow and Supplier flag mutation.
- **Coverage:** verify API-backed loading, Toy selection, traceability detail
  rendering, explicit Supplier flagging, and refetch-driven status updates.
- **Behavior:** no UI, backend, or API contract changes.
- **Verification:** frontend tests passed (`4 passed`), typecheck and
  production build passed. The Python suite passed (`43 passed`), Ruff,
  format, mypy, compilation, and diff checks passed. The environment still
  reports 11 third-party Python 3.14 deprecation warnings.
- **Explicit deferral:** full browser automation, visual regression testing,
  advanced client-side caching, and unrelated frontend features remain out of
  scope.

## 2026-10-15 — Product UX refinement / MVP scope reset

- **Phase:** Product design
- **Status:** Accepted; ready for implementation handoff
- **Human decisions:**
  - make Needs Attention the default Finisher view;
  - provide a separate searchable Inventory view for the complete Toy
    catalog;
  - open a dedicated Toy Investigation view from either risk or inventory
    results;
  - require explicit Finisher selection because authentication is out of
    scope;
  - use progressive disclosure for Parts and source paths;
  - confirm global Supplier flag/unflag actions before mutation;
  - keep the existing API and domain contract for this MVP.
- **Scope reset:** do not add a new overview endpoint, exposure projection,
  lazy-loaded path API, pagination/virtualization, a new data-quality status,
  an i18n library, or administration/CRUD screens in this slice.
- **Scale boundary:** the current response and dataset are acceptable for the
  take-home. If fan-out, payload size, or latency grows materially, future
  work should introduce server-side Part/source filtering or pagination,
  monitoring, and an incremental impact projection.
- **Documentation outcome:** update `SPEC.md`, `DECISIONS.md`,
  `SYSTEM_DESIGN.md`, and `README.md` so the implementation handoff and
  final repository describe the same workflow.

## 2026-10-15 — Toy and Supplier navigation refinement

- **Phase:** Product design
- **Status:** Accepted; implementation handoff update
- **Decision:** Consolidate Needs Attention and Inventory into one Toys
  workspace with `Needs attention` as the default mode and `All inventory` as
  the complete-catalog mode.
- **Decision:** Add a separate Finisher-scoped Supplier Review workspace.
  Show one row per relevant Supplier with current flag state, related-Toy
  context, and explicit flag/unflag actions. Keep Supplier actions available
  from Toy Investigation as a contextual shortcut.
- **API boundary:** add one focused `finisher_id`-filtered Supplier read
  rather than reconstructing Supplier relationships through every Toy detail.
  Do not add generic Supplier CRUD or an all-Suppliers Finisher-facing view.
- **Rationale:** Two identical-looking Toy tabs obscured the difference
  between triage and inventory, while hiding Supplier actions inside a random
  source path made the core flagging workflow difficult to discover.

## 2026-10-15 — Toy and Supplier workspace implementation

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** implement the accepted Toys workspace modes and the
  Finisher-scoped Supplier Review workspace without changing the existing
  impact model or general API surface.
- **Backend behavior:** `GET /api/suppliers?finisher_id=...` returns unique
  relevant Suppliers with deterministic ordering and related-Toy counts.
  Finisher validation and the unfiltered Supplier collection remain intact.
- **Frontend behavior:** keep Needs attention as the default Toys mode, offer
  All inventory as the complete-catalog mode, require explicit Finisher
  selection, and provide searchable/filterable Supplier review rows with
  confirmed global flag/unflag actions. Toy Investigation remains the
  traceability drill-down and retains contextual Supplier actions.
- **Verification:** focused backend repository/API tests passed (`25 passed`);
  frontend tests passed (`7 passed`), and frontend typecheck/build passed.
  The full backend suite passed (`46 passed`). Ruff lint/format, mypy,
  compilation, and diff checks also passed. The environment still reports 11
  third-party Python 3.14 deprecation warnings.
- **Explicit deferral:** no new statuses, exposure metrics, pagination,
  lazy loading, i18n, generic CRUD, or deployment infrastructure.

## 2026-10-15 — Single Toys list UX correction

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** replace the Toys mode controls with one status-filtered Toys
  workspace while preserving the separate Finisher-scoped Supplier workspace
  and Toy Investigation drill-down.
- **UI behavior:** default the status filter to Needs attention (affected and
  potentially affected), provide All statuses to include unaffected Toys,
  apply search and status filtering to the same list, and paginate the loaded
  summaries in ten-row client-side pages.
- **Compatibility:** no new API endpoint or server-side pagination was added.
  Explicit Finisher selection, Supplier confirmation, contextual Supplier
  actions, impact semantics, and expandable traceability detail remain
  unchanged.
- **Verification:** frontend tests passed (`7 passed`), frontend typecheck
  and production build passed, and the full backend suite passed (`46
  passed`). Mypy, Ruff lint/format, compilation, and diff checks also passed.
  The environment still reports 11 third-party Python 3.14 deprecation
  warnings.
- **Explicit deferral:** React Router, separate URLs, new statuses, exposure
  metrics, generic CRUD, and deployment infrastructure remain out of scope.

## 2026-10-15 — Remove risk-only Toys filter

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** remove the Needs attention status filter from the single Toys
  workspace without changing Supplier scoping or the Toy Investigation flow.
- **UI behavior:** default the same Toys list to All statuses and retain
  explicit Affected, Potentially affected, and Unaffected filters, search,
  and ten-row client-side pagination.
- **Compatibility:** no API, domain, impact, or Supplier query changes were
  needed.
- **Verification:** frontend tests passed (`7 passed`), frontend typecheck
  and production build passed, and the full backend suite passed (`46
  passed`). Mypy, Ruff lint/format, compilation, and diff checks also passed.
  The environment still reports 11 third-party Python 3.14 deprecation
  warnings.

## 2026-10-15 — Add a small demo fixture set

- **Phase:** Foundation / developer experience
- **Status:** Implemented and verified
- **Scope:** preserve the original assignment export under `data/full/` and
  add a curated `data/demo/` fixture set used by default local setup.
- **Demo shape:** three Finishers with two Toys each, three Suppliers, three
  Factories, nine Parts, and intentionally non-global Supplier coverage:
  `FIN-001` uses `SUP-001`/`SUP-002`, `FIN-002` uses
  `SUP-002`/`SUP-003`, and `FIN-003` uses `SUP-001`/`SUP-003`.
- **Reset behavior:** `fairtoy setup` and `fairtoy reset` use `data/demo/` by
  default; the full dataset can be loaded into a separate database with
  `--data-dir data/full`. Existing reset semantics remain unchanged:
  validation occurs before a destructive reset, and normal setup preserves
  runtime Supplier flags.
- **Verification:** demo, full, and default resets completed successfully;
  the full Python suite passed (`47 passed`), Ruff lint/format and mypy
  passed, and the demo-specific scope test confirms that no Supplier is
  related to all three Finishers.

## 2026-10-16 — Hide redundant Toy reason-code presentation

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** remove the visible Toy-level `reason_code` tag from Toy
  Investigation because the user-facing status badge and explanation already
  communicate the result.
- **Compatibility:** retain `reason_code` in the API and frontend data
  contract; presentation of the stable code is a separate UI decision.
- **Verification:** frontend tests passed (`7 passed`), frontend typecheck
  and production build passed, and the full backend suite passed (`47
  passed`). Mypy, Ruff lint/format, compilation, and diff checks also passed.
  The environment still reports 11 third-party Python 3.14 deprecation
  warnings.

## 2026-10-16 — Make Supplier Review global

- **Phase:** Product design
- **Status:** Accepted; implementation update required
- **Decision:** Supplier Review is a global workspace available without a
  selected Finisher. It lists all Suppliers, supports search and
  flagged/unflagged filtering, and allows a confirmed flag or unflag action.
  Finisher relevance is optional context rather than a hard scope.
- **Rationale:** Supplier is the global risk subject. A Supplier may need to
  be flagged before it is related to a selected Finisher, and hiding the
  action inside a Toy source path makes the required workflow difficult to
  discover.
- **Compatibility:** The existing unfiltered Supplier API already supports
  the primary read; the optional `finisher_id` query remains useful for
  relevance context. A global flag still recalculates every relevant Toy.
- **UI behavior:** When a flagged unrelated Supplier has no current impact on
  the selected Finisher, explain that explicitly rather than hiding or
  preventing the action.

## 2026-10-16 — Global Supplier Review implementation

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** make Supplier Review available before Finisher selection and use
  the unfiltered Supplier collection as its primary read.
- **UI behavior:** show all Suppliers with search/filter controls and
  confirmed global flag/unflag actions. When a Finisher is selected, merge
  contextual related-Toy counts into those global rows and explain when a
  flagged Supplier has no current Toy impact for that Finisher.
- **Compatibility:** Toys remain Finisher-scoped and require explicit
  selection; Toy Investigation and contextual Supplier actions remain
  unchanged. No new endpoint or generic CRUD was added.
- **Verification:** frontend tests passed (`9 passed`), frontend typecheck and
  production build passed, and the full backend suite passed (`47 passed`).
  Mypy, Ruff lint/format, compilation, and diff checks also passed. The
  environment still reports 11 third-party Python 3.14 deprecation warnings.

## 2026-10-16 — Final two-page product boundary

- **Phase:** Product design
- **Status:** Accepted; implementation handoff
- **Decision:** Treat the UI as two top-level product pages:
  **Finisher Traceability** for a selected Finisher's Toys and
  Toy → Part → Supplier → Factory investigation, and **Suppliers** for the
  global Supplier registry and read-only Supplier → Factory/Part detail.
- **Scope:** Supplier detail is read-only; flag/unflag is the only Supplier
  mutation. Authentication, generic CRUD, history, and operational
  administration remain out of scope.
- **Rationale:** Finisher traceability and global Supplier risk management are
  distinct workflows. This is a coherent interview-sized product boundary,
  not a full administration system.

## 2026-10-16 — Separate frontend workflow boundaries

- **Phase:** User workflow
- **Status:** Implemented; pending human review and acceptance
- **Scope:** reimplement the existing UI behavior with explicit boundaries
  instead of keeping data loading, mutation handling, filtering, pagination,
  and all rendering in `App.tsx`.
- **Structure:** `App.tsx` is now a small entrypoint that exports
  `AppShell`. `useFairToyData.ts` owns request lifecycle and authoritative
  refreshes; `view-model.ts` owns pure filtering, sorting, pagination, and
  Supplier relevance transformations; and the workspace/detail components own
  their local presentation state.
- **Compatibility:** no API, schema, impact-rule, workspace, or confirmation
  behavior changed. Toys remain explicitly Finisher-scoped, Supplier Review
  remains global, and Toy Investigation retains expandable source paths and
  contextual Supplier actions.
- **Verification:** frontend tests passed (`12 passed`), frontend typecheck
  and production build passed, and `git diff --check` passed.

## 2026-10-16 — Polish frontend visual design

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** improve the existing UI presentation without changing workflow
  behavior, API contracts, or domain semantics.
- **Visual changes:** introduce shared color tokens, stronger panel and card
  hierarchy, clearer status and action treatments, improved form controls and
  focus states, refined spacing and shadows, and more deliberate responsive
  breakpoints.
- **Compatibility:** no markup workflow, API, schema, impact rule, or
  navigation behavior changed.
- **Verification:** frontend tests passed (`12 passed`), frontend typecheck
  and production build passed, and `git diff --check` passed.

## 2026-10-16 — Add a traceability icon and restrained motion

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** replace the text-only `FT` marks with a reusable inline SVG
  traceability mark and add subtle visual motion to the existing surfaces.
- **Accessibility:** the motion is disabled for users who prefer reduced
  motion; the icon includes an accessible label when it is not decorative.
- **Compatibility:** no dependency, API, workflow, or domain changes.
- **Verification:** frontend tests passed (`12 passed`), frontend typecheck
  and production build passed, and `git diff --check` passed.

## 2026-10-16 — Add entity icons to the traceability workflow

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** add reusable inline SVG icons for Finishers, Suppliers, Toys,
  Parts, and Factories at the existing workspace, row, and detail
  touchpoints.
- **Design:** icons are color-coded by entity type and remain decorative for
  assistive technology because the adjacent text supplies the entity label.
  No icon dependency was introduced.
- **Compatibility:** no workflow, API, schema, impact, or navigation changes.
- **Verification:** frontend tests passed (`12 passed`), frontend typecheck
  and production build passed, and `git diff --check` passed.

## 2026-10-16 — Hide redundant Part reason-code presentation

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** remove the visible Part-level `reason_code` from Toy
  Investigation because the human-readable Part explanation is sufficient for
  the current UI.
- **Compatibility:** retain `reason_code` in the API and frontend data
  contract for machine clients, tests, and future localization.
- **Verification:** frontend tests passed (`12 passed`), frontend typecheck
  and production build passed, and `git diff --check` passed.

## 2026-10-16 — Complete the two-page product boundary

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** complete the final two-page boundary with a Finisher
  Traceability page and a global Suppliers page. The traceability page keeps
  explicit Finisher selection, one Toys table, status/search/pagination
  controls, related Supplier context, and Toy Investigation as an in-page
  drill-down. The Suppliers page adds global Supplier search/filtering,
  confirmed flag/unflag actions, and read-only Supplier detail with Factories
  and supplied Parts.
- **API:** add `GET /api/suppliers/{supplier_id}` and the focused repository
  query and response contracts required by Supplier detail. Existing list,
  impact, and PATCH semantics remain unchanged.
- **Compatibility:** no new top-level route, React Router, generic CRUD,
  authentication, history, approvals, notifications, exposure metrics,
  pagination backend, or production infrastructure.
- **Verification:** backend tests (`50 passed`), frontend tests (`14
  passed`), mypy, Ruff check/format, TypeScript typecheck, production build,
  Python compilation, and `git diff --check` passed.

## 2026-10-16 — Move catalog selection into Traceability

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** move the two-page navigation into the application header and
  move Finisher selection into the main Finisher Traceability workspace.
  Suppliers no longer render a catalog selector because that workspace is
  global.
- **State behavior:** preserve the selected Finisher while switching between
  workspaces, clear Toy/Supplier drill-down state when changing pages, and
  continue requiring an explicit selection before loading Toys.
- **Compatibility:** no API, schema, impact-rule, or domain changes. The app
  remains one SPA route with two client-side top-level page states.
- **Verification:** frontend tests (`14 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Use one default local database

- **Phase:** Foundation / developer experience
- **Status:** Implemented and verified
- **Decision:** default `fairtoy setup` and `fairtoy reset` to the full
  assignment fixtures in `data/full/`, writing to
  `data/generated/fairtoy.sqlite3`.
- **Scope:** keep the demo fixture for explicit tests or UI experiments, but
  do not load demo and full fixtures into the same database because they share
  identifiers and the schema has no dataset-isolation dimension.
- **Operational effect:** switching fixtures is an explicit reset of the same
  SQLite file; the running API should be restarted after a reset.
- **Verification:** default `fairtoy reset` imported 8 Finishers, 50
  Suppliers, 232 Factories, 300 Toys, and 10,463 Toy-Part relationships;
  the live API returned all 8 Finishers. The Python suite passed (`51
  passed`), Ruff and mypy passed, and `git diff --check` passed.

## 2026-10-16 — Paginate Supplier workspaces

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** add ten-row client-side pagination to the global Suppliers list
  and the Related Suppliers context list on Finisher Traceability.
- **Behavior:** Supplier search and risk filtering run before pagination and
  reset the global list to page one. Related Suppliers reset to page one when
  the selected Finisher changes. Both lists use the same shared pagination
  presentation and retain their existing click-through and flag actions.
- **Compatibility:** no API, backend, domain, or Supplier detail-list
  changes. Factories and supplied Parts remain compact read-only detail
  lists.
- **Verification:** frontend tests (`16 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Collapse Related Supplier context

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** combine the Finisher selector and Related Suppliers into one
  Catalog Context card. Related Suppliers now uses a native accessible
  disclosure and is collapsed by default.
- **Behavior:** retain the Related Supplier count, ten-row pagination, and
  Supplier click-through inside the expanded disclosure. The global
  Suppliers workspace remains unchanged.
- **Compatibility:** no API, backend, domain, or impact-rule changes.
- **Verification:** frontend tests (`16 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Align frontend entity surfaces

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** normalize visual alignment for entity icons, navigation counts,
  headings, row content, status badges, risk actions, pagination controls,
  and traceability fact columns.
- **Responsive behavior:** desktop rows use stable content/action columns;
  mobile overrides stack those areas without changing interaction behavior.
- **Compatibility:** no API, schema, domain, impact-rule, or workflow
  changes.
- **Verification:** frontend tests (`16 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Standardize counter alignment

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** give navigation and workspace counters fixed dimensions,
  centered numerals, and consistent placement across headings, disclosures,
  and detail sections.
- **Compatibility:** no API, schema, domain, impact-rule, or workflow
  changes.
- **Verification:** frontend tests (`16 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Fix Related Supplier counter placement

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** align the Related Suppliers counter to the right side of its
  disclosure header, immediately before the expand/collapse affordance.
- **Compatibility:** no API, schema, domain, impact-rule, or workflow
  changes.
- **Verification:** frontend tests (`16 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Make demo Supplier coverage uneven

- **Phase:** Foundation / developer experience
- **Status:** Implemented and verified
- **Scope:** keep the demo fixture small while making Supplier coverage
  visibly different across Finishers: FIN-001 uses one Supplier, FIN-002 uses
  two, and FIN-003 uses all three.
- **Review scenario:** flagging SUP-001 for FIN-002 produces one affected,
  one potentially affected, and one unaffected Toy, making the status filters
  and traceability drill-down easy to exercise.
- **Compatibility:** the full assignment fixture and canonical schema are
  unchanged; only `data/demo/` and its fixture assertions changed.
- **Verification:** the demo fixture tests and full backend suite passed (`52
  passed`), Ruff and mypy passed, and `git diff --check` passed.

## 2026-10-16 — Paginate Toy Investigation Parts

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** add ten-row client-side pagination to the Parts list inside Toy
  Investigation.
- **Behavior:** opening a different Toy resets to page one. Part expansion,
  Supplier actions, and all Supplier/Factory source paths remain unchanged
  within each Part.
- **Compatibility:** no API, backend, domain, or detail-response changes.
- **Verification:** frontend tests (`17 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Align Part row metadata

- **Phase:** User workflow
- **Status:** Implemented; pending human review
- **Scope:** align Part quantity and status metadata to the right side of
  each expandable Part row, immediately before the expand/collapse affordance.
- **Responsive behavior:** retain stacked Part rows on narrow screens with
  the expand affordance pinned to the row corner.
- **Compatibility:** no API, schema, domain, impact-rule, or workflow
  changes.
- **Verification:** frontend tests (`17 passed`), TypeScript typecheck,
  production build, and `git diff --check` passed.

## 2026-10-16 — Add observability foundations

- **Phase:** Verification / operational readiness
- **Status:** Implemented and verified
- **Scope:** add standard-library structured key-value logging, safe request
  correlation IDs, API request/mutation events, and importer lifecycle events
  with duration and record-count context.
- **Safety boundary:** do not log request bodies, credentials, full
  traceability payloads, or per-row repository/impact activity. Metrics,
  tracing backends, health checks, dashboards, alerting, and deployment
  monitoring remain deferred until runtime requirements exist.
- **Verification:** focused observability tests passed (`25 passed` across
  API, CLI, and logging tests); the full backend suite passed (`55 passed`).
  Frontend tests passed (`17 passed`), TypeScript typecheck and production
  build passed, and Ruff lint/format, mypy, compilation, and diff checks
  passed. The environment still reports 13 third-party Python 3.14
  deprecation warnings.

## 2026-10-16 — Clarify repository boundaries

- **Phase:** Verification / repository presentation
- **Status:** Implemented and verified
- **Scope:** group the Python package and backend tests under `backend/`, and
  move frontend tests under `frontend/tests/`. Keep the existing API, domain
  model, UI behavior, and fixture layout unchanged.
- **Reason:** make the two application surfaces and their test ownership
  immediately clear to a reviewer without introducing new runtime abstractions.
- **Verification:** backend tests (`55 passed`), Ruff lint/format, mypy,
  frontend tests (`17 passed`), TypeScript typecheck, production build, and
  `git diff --check` passed. The test fixture root and CLI default paths were
  updated for the new backend location.

## 2026-10-16 — Reframe design documentation for interview review

- **Phase:** Documentation / interview preparation
- **Status:** Implemented
- **Scope:** reorganize `SYSTEM_DESIGN.md` around requirements, non-functional
  goals, known scale, data model, API design, architecture, main flows, deep
  dives, and production evolution. Clarify in `SPEC.md` that it owns product
  behavior while the system design owns implementation choices.
- **Reason:** make the spec-driven process legible to a reviewer unfamiliar
  with the repository without duplicating the decision log.
- **Verification:** documentation diff reviewed and `git diff --check` passed.

## Working method

1. Human defines or approves the product boundary and business semantics.
2. The current specification and decision log are updated.
3. AI receives one bounded implementation or design task at a time.
4. Human reviews the complete result and runs the relevant checks.
5. Decisions or rejected suggestions are recorded before the next phase.

AI is an implementation accelerator, not the product decision-maker.

## Original planned phases

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
