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

## D016 — Separate database setup from application startup

- **Status:** Accepted
- **Decision:** Use SQLAlchemy with a file-backed SQLite database and a
  deterministic setup/import command. Normal application startup reuses the
  existing database and does not reseed it.
- **Alternatives considered:** in-memory data, seeding on every startup,
  PostgreSQL with external infrastructure, and direct raw SQLite access.
- **Rationale:** SQLite provides persistence without infrastructure for the
  small take-home dataset. SQLAlchemy makes the canonical relational model and
  constraints explicit. Separating setup from startup prevents runtime
  Supplier flags from being reset on every restart.
- **Trade-off:** This is not a production concurrency or migration strategy.
  A production version would move to PostgreSQL and add migrations.

## D017 — Choose a normalized relational model

- **Status:** Accepted
- **Decision:** Use canonical entity tables plus explicit relationship tables:
  `finishers`, `toys`, `finisher_toys`, `suppliers`, `factories`, `parts`,
  `toy_parts`, and `part_sources`.
- **Alternatives considered:** mirror the flat CSVs, use a graph database, or
  keep the data in memory/JSON.
- **Rationale:** The normalized model preserves repeated relationships,
  supports the impact calculation, and fits SQLite and SQLAlchemy. Mirroring
  the CSVs would make duplicate identities and sourcing options ambiguous.
  A graph database or document store would add infrastructure without solving
  a current problem.
- **Trade-off:** The importer has more mapping work than a direct CSV loader,
  but the domain and business logic remain explicit and testable.

## D018 — Use source identifiers as canonical keys

- **Status:** Accepted
- **Decision:** Use the supplied `toy_id`, `part_id`, `supplier_id`,
  `factory_id`, and `finisher_id` as primary keys. Use composite keys for
  `finisher_toys` and `toy_parts`, with a uniqueness constraint for distinct
  `part_sources`.
- **Alternatives considered:** internal surrogate IDs with separate external
  key mappings.
- **Rationale:** The source identifiers already appear in the relationship
  files, so using them keeps import and traceability queries clear.
- **Trade-off:** A production multi-source platform may need internal IDs if
  customer identifiers can change or collide across sources.

## D019 — Make nullability reflect domain importance

- **Status:** Accepted
- **Decision:** Keep identifiers, relationship references, names needed for
  explanation, BOM quantities, and the current Supplier flag non-null.
  Preserve missing optional fields as null, including factory address/city,
  flag timestamps while unflagged, and optional commercial or location
  attributes.
- **Rationale:** Missing enrichment data should not prevent traceability, but
  missing graph identity or relationship data should fail import validation.
  The current fixtures contain blank factory address and city values.
- **Invariant:** An unflagged Supplier has no `flagged_at`; a flagged Supplier
  has a timestamp.

## D020 — Restrict destructive relationship changes

- **Status:** Accepted
- **Decision:** Enable foreign keys and restrict deletes for entities that are
  referenced by the traceability graph. Do not cascade-delete BOM or sourcing
  relationships.
- **Rationale:** A cascading delete could silently erase evidence paths and
  make impact analysis unreliable. The current workflow does not require
  destructive CRUD.
- **Future:** If CRUD is added, use soft deletion or archival where historical
  traceability matters.

## D021 — Make imports atomic and separate from runtime state

- **Status:** Accepted
- **Decision:** Validate all source files before writing, load canonical data
  in one transaction, make normal setup safe to rerun, and preserve runtime
  Supplier flags during normal seeding. Database recreation requires an
  explicit reset operation.
- **Rationale:** An import failure must not leave a partially populated graph.
  Runtime risk state is application state and must not be overwritten by
  fixture initialization.
- **Trade-off:** Handling source updates is more deliberate than dropping and
  recreating the database, but it protects current state and makes setup
  predictable.

## D022 — Separate fact retrieval from impact classification

- **Status:** Accepted
- **Decision:** Repository queries retrieve filtered traceability facts.
  A backend domain service groups those facts and calculates impact status and
  explanation paths.
- **Alternatives considered:** put all classification in a large SQL query or
  load the entire dataset into Python.
- **Rationale:** The two-stage design keeps business rules explicit and
  testable while allowing SQL to filter the data efficiently.
- **Trade-off:** It adds a small mapping step between query results and the
  domain service, but avoids hiding the rule in SQL or the frontend.

## D023 — Design the API around user workflows

- **Status:** Accepted
- **Decision:** Expose Finisher catalog reads, Toy traceability detail,
  Supplier state, and Supplier flagging rather than generic CRUD for every
  canonical table.
- **Rationale:** The API should directly support the required workflow and
  keep the take-home focused on traceability.
- **Trade-off:** Administrative data-management endpoints are deferred until
  they have a demonstrated product need.

## D024 — Update Supplier risk state with an explicit PATCH

- **Status:** Accepted
- **Decision:** Update the current Supplier child-labor state with an
  explicit desired value, conceptually `PATCH /suppliers/{supplier_id}` with
  `child_labor_flagged: true|false`.
- **Alternatives considered:** a toggle action, a separate flag subresource,
  or generic unrestricted CRUD.
- **Rationale:** The current flag is a Supplier property, not a separate
  audited entity. An explicit desired value is safe to retry and lets the
  backend maintain the `flagged_at` invariant.
- **Future:** If risk assessments become first-class records with evidence,
  actors, or history, introduce a dedicated risk resource.

## D025 — Separate summary and detail reads

- **Status:** Accepted
- **Decision:** The API will provide compact Finisher toy summaries for the
  dashboard and full traceability detail on demand for an individual Toy.
- **Rationale:** The dashboard does not need the complete relationship graph
  for every Toy. Detail reads keep payloads focused and provide a path to
  larger datasets.
- **Trade-off:** The frontend performs an additional read when a Toy is
  opened, but avoids over-fetching and N+1-style relationship loading.

## D026 — Use one focused Finisher workflow

- **Status:** Superseded by D036
- **Decision:** Keep the frontend focused on one Finisher traceability
  workflow. The original single-dashboard presentation is superseded by a
  small set of focused views rather than unrelated administration navigation.
- **Rationale:** The required behavior remains one coherent workflow even
  when the information is split across views for readability.
- **Trade-off:** Full CRUD navigation and separate operational workflows are
  deferred.

## D027 — Test the domain, import, and API boundaries

- **Status:** Accepted
- **Decision:** Use domain unit tests, importer/database integration tests,
  and API integration tests. Verify the frontend with a production build and
  a manual end-to-end workflow.
- **Rationale:** The impact calculation and data normalization are the
  highest-risk areas. This provides strong signal without spending the
  take-home budget on an exhaustive browser suite.
- **Trade-off:** Browser automation and broad UI regression coverage are
  deferred.

## D028 — Add only supplemental relationship indexes

- **Status:** Accepted
- **Decision:** Rely on primary-key and unique-constraint indexes, then add
  explicit indexes only for reverse relationship lookups not covered by the
  leading columns of those indexes.
- **Indexes considered:** `finisher_toys.toy_id`, `toy_parts.part_id`,
  `part_sources.supplier_id`, `part_sources.factory_id`, and
  `factories.supplier_id`.
- **Rationale:** Primary keys and unique constraints already index their
  columns. Foreign-key columns are not automatically indexed in SQLite, and
  redundant indexes add write and maintenance cost.

## D029 — Use synchronous request-scoped database sessions

- **Status:** Accepted
- **Decision:** Use synchronous SQLAlchemy sessions scoped to each FastAPI
  request. Supplier flag mutations use an explicit transaction.
- **Alternatives considered:** async SQLAlchemy with `aiosqlite`.
- **Rationale:** The local SQLite workload has no meaningful concurrency
  requirement, so synchronous access is simpler and easier to review.
- **Trade-off:** Async access is deferred until a production storage and
  concurrency model justify it.

## D030 — Avoid generic identity and audit boilerplate for now

- **Status:** Accepted
- **Decision:** Do not add generic internal IDs or `created_at`/`updated_at`
  fields to every table. Use the supplied identifiers as canonical keys and
  retain meaningful domain time such as `flagged_at`.
- **Rationale:** There is one source system, imported entities are mostly
  immutable, and generic timestamps would represent ingestion mechanics rather
  than useful business events.
- **Future:** A production multi-source or audited system can introduce
  internal IDs, unique external IDs, and explicitly defined lifecycle
  timestamps.

## D031 — Derive PartSource Supplier through Factory

- **Status:** Accepted
- **Decision:** Keep Factory as a contextual manufacturing-site entity.
  `PartSource` links a Part to a Factory; the Factory links to its Supplier,
  whose flag remains directly mutable.
- **Rationale:** This preserves the exact manufacturing site and supports
  multiple Suppliers for one Part without duplicating the Supplier
  relationship. The importer validates the Supplier value in the CSV against
  the Factory's Supplier.
- **Trade-off:** Impact queries include one additional join. The current
  dataset guarantees a Factory for each Part source, so this is acceptable.
- **Future:** If sources can lack a known Factory, revisit whether Supplier
  should also be stored directly on PartSource.

## D032 — Scope Toy reads by Finisher

- **Status:** Superseded by D033
- **Decision:** Nest Toy summary and detail reads under a Finisher resource.
  Supplier state remains global and is updated independently.
- **Rationale:** The route expresses the catalog boundary and disambiguates
  the same Toy appearing for multiple Finishers.
- **Trade-off:** The API is slightly more explicit than an unscoped filtered
  query, but the relationship is easier to understand and defend.

## D033 — Let the UI use a top-level Toy resource with Finisher filtering

- **Status:** Accepted
- **Decision:** Use a reusable top-level Toy collection with a
  `finisher_id` filter for the dashboard. Keep the Finisher selector as the
  UI context and retain Finisher-scoped semantics in the response.
- **Rationale:** Toy is a canonical global resource while FinisherToy is a
  relationship. The UI workflow needs Finisher context, but the API should
  remain useful to other consumers without duplicating nested and unscoped
  endpoints.
- **Trade-off:** The API must validate and interpret the Finisher filter
  consistently; route nesting alone would communicate that relationship more
  directly.

## D034 — Use a small typed frontend API client

- **Status:** Accepted
- **Decision:** Use native browser `fetch` behind a small typed API client and
  React state for this single-dashboard workflow.
- **Alternatives considered:** TanStack Query for server-state caching or
  Redux for shared client state.
- **Rationale:** The application has a small number of reads and one mutation.
  A thin client keeps loading, error, and refetch behavior visible and easy to
  explain.
- **Future:** Add a server-state library if the application grows to many
  screens, shared queries, or complex cache invalidation.

## D035 — Keep detail payloads explainable but compact

- **Status:** Accepted
- **Decision:** Keep full traceability paths on the Toy detail response, but
  keep the Toy summary response compact. Path objects should not repeat Toy and
  Part fields already present in their parent objects.
- **Rationale:** The measured detail response is approximately 16.5 KB for a
  Toy with many Parts, which is acceptable for an on-demand detail read. The
  response still benefits from avoiding redundant JSON.
- **Contract guidance:** Include a stable `reason_code` alongside the
  human-readable reason. Serialize `unit_cost_usd` consistently; decimal
  strings are acceptable when preserving currency precision.
- **Trade-off:** The detail representation is richer than a minimal resource
  response, but it directly satisfies the traceability requirement. Summary
  reads must not include the full path graph.

## D036 — Use a focused progressive-disclosure workflow

- **Status:** Accepted
- **Decision:** Use two top-level product pages:
  - **Finisher Traceability:** an explicitly selected Finisher's Toys,
    related Suppliers, and Toy → Part → Supplier → Factory investigation;
  - **Suppliers:** a global Supplier registry with search, flag state,
    flag/unflag actions, and read-only Supplier detail for factories and
    supplied Parts.
  Toy and Supplier details are drill-downs within their respective pages.
  Parts and source paths use progressive disclosure.
- **Rationale:** Toys, Suppliers, and traceability evidence are different
  user tasks. A Finisher page keeps catalog context coherent, while a
  separate Supplier page makes the required global risk action discoverable.
- **Trade-off:** The UI has two focused pages, but no generic administration
  area or speculative dashboard infrastructure.

## D037 — Require explicit Finisher context without authentication

- **Status:** Accepted
- **Decision:** Because authentication and user accounts are out of scope,
  the first Toys/catalog view requires an explicit Finisher selection. The
  application must not silently choose the first fixture record. The global
  Supplier Review workspace may be opened without a selected Finisher. When
  selected, the `finisher_id` remains visible and is preserved across the
  Finisher-scoped workflow, with URL or local-storage persistence left as a
  frontend implementation detail.
- **Rationale:** Multiple Finishers exist in the fixture data, and silently
  showing one company's exposure would make the Toy context ambiguous. A
  Supplier flag is global, so Supplier discovery should not be blocked by a
  Toy catalog selection.
- **Trade-off:** The first Toys view has one additional selection step, while
  Supplier Review can start from the global risk registry.

## D038 — Keep the MVP scale boundary explicit

- **Status:** Accepted
- **Decision:** For the take-home, use the existing compact Toy summary and
  on-demand Toy detail reads, plus UI-level filtering and progressive
  disclosure. Do not add an overview projection, lazy-loaded path endpoints,
  server-side pagination, virtualization, or event-driven impact
  recalculation now.
- **Rationale:** The supplied fixture is moderate and the measured detail
  response is approximately 16.5 KB. The assignment evaluates product and
  modeling judgment within a one-to-three-hour target, not production
  infrastructure.
- **Future:** If detail fan-out, payload size, or latency grows materially,
  add server-side Part/source filtering or pagination, query-plan monitoring,
  and an incremental materialized impact projection. Move the operational
  database to PostgreSQL when SQLite's concurrency limits become relevant.

## D039 — Keep explanation codes language-neutral

- **Status:** Accepted
- **Decision:** Treat `reason_code` as the stable machine-readable
  explanation contract. The API may continue returning an English `reason`
  for the current MVP, while a future frontend locale catalog can translate
  the code. Do not add a full internationalization library to this slice.
- **Rationale:** Domain and API data should not need to change when user-facing
  language changes. The current response already carries both the stable code
  and a human-readable fallback.
- **Trade-off:** Only the English presentation is implemented now; locale
  catalogs remain a future UI concern.

## D040 — Confirm global Supplier risk mutations

- **Status:** Accepted
- **Decision:** The Toy Investigation view must confirm a Supplier flag or
  unflag action before sending the explicit PATCH. The confirmation explains
  that the Supplier state is global and may change other Toys' calculated
  statuses. After success, the UI refetches the authoritative summaries and
  detail.
- **Rationale:** A small path-level button can otherwise hide the fan-out of a
  global risk-state mutation.
- **Trade-off:** The action takes one additional interaction, but the impact
  is deliberate and understandable.

## D041 — Defer speculative exposure and data-quality states

- **Status:** Accepted
- **Decision:** Keep the current three impact states and current response
  contract for the MVP. Do not add a new `needs_review` status or annual-unit
  and retail-value exposure metrics until their product semantics and API
  support justify them. If exposure metrics are added later, annual units
  should be considered before retail price as a risk measure.
- **Rationale:** Missing source evidence and commercial values require
  additional product definitions. Adding them now would expand the domain
  contract while the core traceability workflow is still being polished.
- **Future:** Distinguish missing evidence from unaffected status and expose
  physical exposure metrics when the data and workflow support them.

## D042 — Add a focused Finisher-scoped Supplier Review read

- **Status:** Superseded by D045
- **Decision:** An earlier iteration scoped Supplier Review to the selected
  Finisher. The final global behavior is defined by D045.

## D043 — Use one Toys list with a status filter

- **Status:** Superseded by D044
- **Decision:** An earlier iteration used a risk-only default for the Toys
  list. The final explicit-filter behavior is defined by D044.

## D044 — Keep status filtering explicit without a risk-only default

- **Status:** Accepted
- **Decision:** Remove the `Needs attention` filter from the Toys workspace.
  Keep one list with `All statuses` as the default and retain explicit
  Affected, Potentially affected, and Unaffected filters. Search and
  ten-row client-side pagination continue to apply to that same list.
- **Rationale:** The Toys workspace should not imply a separate risk queue
  when the product only needs one catalog list. Users can still narrow to
  risk states directly when triage is the goal.
- **Compatibility:** Toy Investigation, impact semantics, and the existing
  Supplier API contract remain intact; Supplier Review scope is refined by
  D045.

## D045 — Make Supplier Review a global risk workspace

- **Status:** Accepted
- **Decision:** Supplier Review is available without a selected Finisher and
  lists all Suppliers by default. It supports search, flagged/unflagged
  filtering, one explicit `Flag supplier`/`Unflag supplier` action per
  Supplier, and read-only detail for the Supplier's Factories and supplied
  Parts. When a Finisher is selected, the UI may show or filter by relevance
  to that catalog, but relevance is not required to flag a Supplier. Use the
  unfiltered `GET /api/suppliers` collection as the primary read; retain the
  optional `finisher_id` query for contextual relevance.
- **Rationale:** Supplier is the global risk subject. A Finisher may need to
  flag a Supplier before it is currently related to that Finisher's catalog,
  and hiding the action inside a Toy source path makes the core workflow hard
  to discover.
- **Trade-off:** Flagging an unrelated Supplier has no current Toy impact for
  the active Finisher. The UI must explain that the mutation is global and
  may affect other Finishers or future relationships.
