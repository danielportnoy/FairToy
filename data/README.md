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

- `full/` is the default local dataset and preserves the original assignment
  export for broad integration coverage and scale checks.
- `demo/` is a deliberately small fixture for focused UI work and tests. It
  contains three Finishers, three Toys per Finisher, three Suppliers, and
  deliberately uneven Supplier coverage: `FIN-001` uses only `SUP-001`,
  `FIN-002` uses `SUP-001`/`SUP-002`, and `FIN-003` uses all three Suppliers.
- The two- and three-Supplier Finishers' Toys are arranged so flagging one
  Supplier produces one affected, one potentially affected, and one
  unaffected Toy. For example, select `FIN-002`, flag `SUP-001`, and review
  the three Toy statuses.
- `generated/` contains local SQLite databases and is ignored by git.

Use `fairtoy setup` or `fairtoy reset` for the default full dataset. Pass
`--data-dir data/demo` when you want to load the small demo fixture.

The `__MACOSX/` entries from the original archive are intentionally excluded.
