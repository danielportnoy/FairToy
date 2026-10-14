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
