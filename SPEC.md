# FairToy specification

## Document status

This is the product and domain contract for the FairToy take-home assignment.
Technical implementation details live in [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md);
decision rationale lives in [`DECISIONS.md`](DECISIONS.md).

## Outcome

A Finisher should be able to understand which of its toys may be exposed to a
supplier child-labor issue and why.

The core traceability path is:

> Toy → Part → Supplier → Factory

## In scope

- Import the supplied customer-export-style CSV data into a canonical model.
- Browse a Finisher's toys.
- Browse the parts and possible sourcing paths for a toy.
- Flag and unflag a supplier for child labor.
- Calculate each toy's current impact status.
- Show the paths and source facts that explain that status.
- Persist the current supplier flag across application restarts.

## Out of scope

- Retailer workflows.
- Basic Materials companies and raw-material relationships.
- Orders, order halts, and recall workflows.
- Factory-level risk flags.
- Flag evidence, approvals, users, and historical risk events.
- Authentication and multi-tenancy.
- Notifications, email, websockets, and real-time updates.
- Deployment and production infrastructure.
- Generic CRUD screens for every imported entity.

These may be future extensions, but they are not required to demonstrate the
Finisher traceability workflow.

## Canonical domain model

The CSVs are external input fixtures, not the application's domain schema.
The importer will transform them into a canonical relational model.

### Finisher

A customer organization using FairToy.

### Toy

A canonical finished-toy product, identified by the source product identity
for this assignment.

### FinisherToy

The relationship between a Finisher and a Toy in that Finisher's catalog.
Finisher-specific commercial values such as retail price and annual volume
belong here.

### Part

A canonical component used by one or more toys.

### ToyPart

The BOM relationship between a Toy and a Part, including quantity.

### Supplier

A contract manufacturer that may provide parts. The current child-labor risk
state belongs to the Supplier:

- current flagged/unflagged state;
- timestamp for when it was flagged.

A separate risk-history entity is deferred.

### Factory

A site operated by a Supplier. A Factory is currently traceability context,
not an independently flaggable risk subject.

### PartSource

A possible or approved source for a Part, connecting it to a Factory and
carrying source-specific values such as unit cost. The Supplier is derived
through the Factory's Supplier relationship.

The supplied BOM does not identify which source produced a particular
instance. Therefore, a PartSource is not treated as proof that every toy
using the Part used that Supplier.

## Impact calculation

Impact status is derived from current relationships and Supplier flags. It is
not stored as a duplicated status column.

### Part-level interpretation

- No flagged possible sources: no impact through that Part.
- At least one flagged and at least one unflagged possible source:
  potentially affected.
- All known possible sources are flagged: affected.

### Toy-level interpretation

- If any required Part is affected, the Toy is affected.
- Otherwise, if any required Part is potentially affected, the Toy is
  potentially affected.
- Otherwise, the Toy is unaffected.

Impact is calculated at the canonical Toy level and shown to every
Finisher–Toy relationship because the current supplier flag and BOM model are
global. A future source-allocation model could make the result
Finisher-specific.

Every impacted result must be explainable through one or more paths:

> Toy → Part (quantity) → Supplier (flag state) → Factory

## Source-data assumptions

- Repeated source identifiers are interpreted through canonical relationships,
  not blindly overwritten.
- Repeated Toy rows can represent one Toy in multiple Finisher catalogs.
- Repeated Part rows can represent multiple possible PartSource records.
- Exact duplicate source rows may be safely deduplicated during import.
- Distinct relationships must be preserved.
- Optional blank source values remain null; the UI may display them as
  “Not provided”.
- Invalid relationship references should fail the import with an actionable
  error rather than being silently skipped.
- The importer is deterministic and idempotent.

These are modeling assumptions about a messy customer export, not claims about
the customer's upstream systems.

## Product behavior

- Supplier flags are global in the current bounded context.
- The Toys/catalog view is filtered to the selected Finisher's catalog
  relationships.
- Because authentication is out of scope, the first visit requires an explicit
  Finisher selection; the UI must not silently choose an arbitrary Finisher.
- The Finisher has one Toys workspace with an `All statuses` filter by
  default. The user can filter to affected, potentially affected, or
  unaffected Toys. Search, status filtering, and ten-row client-side
  pagination apply to the same list.
- Supplier Review is a centralized global workspace showing all Suppliers,
  even when a Supplier is not currently related to the selected Finisher. It
  is the primary place to review and flag Suppliers; Supplier actions may
  also remain available in Toy investigation for context.
- If a Finisher is selected while reviewing Suppliers, the UI may show
  relevance to that catalog. A Supplier that is not currently related can
  still be flagged, with the UI explaining that no current Toy impact is
  expected for that Finisher.
- Selecting a Toy opens an investigation view with its Parts and possible
  source paths. The UI uses progressive disclosure so the full relationship
  graph is available without presenting every path at once.
- Flagging a Supplier is a deliberate, confirmed action because the current
  Supplier state is global and can change other Toys' calculated results.
- A new or removed Supplier flag changes the next calculated impact view.
- There is no real-time push notification; users see the current state when
  they load or refresh the view.
- The backend owns impact calculation. The frontend presents the returned
  status and explanation paths.

## Acceptance criteria

- A fresh setup can import the supplied data reproducibly.
- A user can select a Finisher and browse its toys.
- A first-time user can explicitly select the active Finisher before viewing
  catalog data.
- The user can open the Toys workspace, filter the same list by impact status,
  paginate it, and open a Toy investigation from any result.
- The user can open Supplier Review without a selected Finisher, review all
  Suppliers, and flag or unflag a Supplier.
- A user can inspect a toy's parts, possible sources, suppliers, and factories.
- Supplier flagging is confirmed in the UI and the resulting global impact
  changes are visible after the authoritative data is refreshed.
- With no flags, relevant toys are unaffected.
- A mixed flagged/unflagged source set produces potentially affected.
- A fully flagged known source set produces affected.
- Unflagging a Supplier changes the calculated result on the next read.
- A global Supplier flag is reflected for every relevant Finisher.
- An impacted result includes the path and reason that produced it.
- The core impact rule has automated tests.
- The repository includes clear setup and run instructions.

## Future extensions

- Source allocation per Finisher or production batch.
- Factory-level risk observations and risk precedence.
- Supplier risk history, evidence, actors, and approvals.
- Materialized impact projections or event-driven recalculation at scale.
- Server-side pagination or lazy loading for high-fanout detail reads.
- Optional CRUD and operational workflows.
