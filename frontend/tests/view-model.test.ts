import { describe, expect, it } from "vitest";

import type { Supplier, ToySummary } from "../src/api";
import {
  filterAndSortToys,
  mergeSupplierRelevance,
  paginate,
} from "../src/view-model";

const toys: ToySummary[] = [
  {
    finisher_id: "FIN-1",
    toy_id: "TOY-1",
    toy_name: "Unaffected Toy",
    status: "unaffected",
    reason_code: "toy_unaffected",
    reason: "No impact.",
  },
  {
    finisher_id: "FIN-1",
    toy_id: "TOY-2",
    toy_name: "Affected Toy",
    status: "affected",
    reason_code: "toy_affected",
    reason: "A part is affected.",
  },
];

const suppliers: Supplier[] = [
  {
    supplier_id: "SUP-1",
    supplier_name: "Supplier One",
    hq_country: null,
    child_labor_flagged: false,
    flagged_at: null,
    related_toy_count: null,
  },
];

describe("frontend view model", () => {
  it("filters Toys and keeps risk states first", () => {
    expect(filterAndSortToys(toys, "", "all").map((toy) => toy.toy_id)).toEqual(
      ["TOY-2", "TOY-1"],
    );
    expect(
      filterAndSortToys(toys, "unaffected", "affected"),
    ).toEqual([]);
  });

  it("clamps client pages when a filter has fewer results", () => {
    expect(paginate(toys, 4, 1)).toEqual({
      items: [toys[1]],
      total: 2,
      page: 2,
      pageCount: 2,
    });
  });

  it("adds optional Finisher relevance without changing global Suppliers", () => {
    const relevantSupplier = { ...suppliers[0], related_toy_count: 3 };
    expect(mergeSupplierRelevance(suppliers, [relevantSupplier])).toEqual([
      relevantSupplier,
    ]);
    expect(mergeSupplierRelevance(suppliers, null)).toEqual(suppliers);
  });
});
