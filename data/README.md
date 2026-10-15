# FairToy source data

The importer expects six customer-export-style CSV files in one fixture
directory:

- `finishers.csv`
- `suppliers.csv`
- `factories.csv`
- `parts.csv`
- `toys.csv`
- `bill_of_materials.csv`

These files are input fixtures, not the application's canonical schema. The
importer normalizes them according to the root [`SPEC.md`](../SPEC.md).

## Fixture sets

- `demo/` is the default local dataset. It contains three Finishers, two Toys
  per Finisher, three Suppliers, and deliberately different Supplier
  coverage: `FIN-001` uses `SUP-001`/`SUP-002`, `FIN-002` uses
  `SUP-002`/`SUP-003`, and `FIN-003` uses `SUP-001`/`SUP-003`.
- `full/` preserves the original assignment dataset for broad integration
  coverage and scale checks.
- `generated/` contains local SQLite databases and is ignored by git.

Use `fairtoy setup` or `fairtoy reset` for the small demo dataset. Pass
`--data-dir data/full` when you want to load the original assignment data.

The `__MACOSX/` entries from the original archive are intentionally excluded.
