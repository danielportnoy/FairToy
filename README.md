# FairToy

FairToy is a focused traceability application for Finishers. It shows how
finished toys relate to parts, suppliers, and factories, and identifies toys
that are affected or potentially affected when a supplier is flagged for child
labor.

## Status

The project is currently in the domain and system-design preparation phase.
The implementation will follow the decisions in [`SPEC.md`](SPEC.md).

## Current scope

The core workflow will allow a Finisher to:

1. Browse its toys.
2. Trace a toy through its parts to possible suppliers and factories.
3. Flag or unflag a supplier for child labor.
4. See affected and potentially affected toys with an explainable path.

Retailers, basic-material companies, raw materials, orders, recalls,
authentication, multi-tenancy, notifications, real-time updates, and
production deployment are intentionally deferred.

## Planned technology

- Python and FastAPI
- SQLite
- React, TypeScript, and Vite
- A deterministic importer for the supplied CSV fixtures

## Project records

- [`SPEC.md`](SPEC.md) — product boundary, domain rules, assumptions, and
  acceptance criteria
- [`DECISIONS.md`](DECISIONS.md) — decisions and deferred extensions
- [`PROCESS_LOG.md`](PROCESS_LOG.md) — implementation phases, AI usage, and
  review checkpoints

## Source data

The assignment data is currently available at
`../toy_data/` in the preparation workspace. Before implementation, the
original six CSV files will be copied into this repository under
`data/source/` so a fresh checkout can be seeded reproducibly. macOS metadata
under `__MACOSX/` is not part of the application data.

Run instructions will be added when the backend and frontend are scaffolded.
