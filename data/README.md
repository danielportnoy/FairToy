# FairToy source data

This directory contains the six CSV fixtures supplied with the assignment:

- `finishers.csv`
- `suppliers.csv`
- `factories.csv`
- `parts.csv`
- `toys.csv`
- `bill_of_materials.csv`

These files are customer-export-style input data, not the application's
canonical schema. The importer will normalize them according to the root
[`SPEC.md`](../SPEC.md).

The `__MACOSX/` entries from the original archive are intentionally excluded.
