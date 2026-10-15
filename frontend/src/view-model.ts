import {
  type ImpactStatus,
  type Supplier,
  type ToySummary,
} from "./api";

export type AppPage = "traceability" | "suppliers";
export type ToyStatusFilter = "all" | ImpactStatus;
export type SupplierFilter = "all" | "flagged" | "unflagged";

export const TOYS_PER_PAGE = 10;
export const SUPPLIERS_PER_PAGE = 10;
export const PARTS_PER_PAGE = 10;

const STATUS_LABELS: Record<ImpactStatus, string> = {
  unaffected: "Unaffected",
  potentially_affected: "Potentially affected",
  affected: "Affected",
};

const STATUS_RANK: Record<ImpactStatus, number> = {
  affected: 0,
  potentially_affected: 1,
  unaffected: 2,
};

export function statusLabel(status: ImpactStatus): string {
  return STATUS_LABELS[status];
}

export function statusClass(status: ImpactStatus): string {
  return `status status-${status.replace("_", "-")}`;
}

export function formatCost(cost: string | null): string {
  return cost === null ? "Not provided" : `$${cost}`;
}

export function formatDate(value: string): string {
  return value.slice(0, 10);
}

export function filterAndSortToys(
  toys: ToySummary[],
  searchQuery: string,
  statusFilter: ToyStatusFilter,
): ToySummary[] {
  const normalizedSearch = searchQuery.trim().toLowerCase();
  return toys
    .filter((toy) => {
      const matchesSearch =
        !normalizedSearch ||
        `${toy.toy_name} ${toy.toy_id} ${toy.reason}`
          .toLowerCase()
          .includes(normalizedSearch);
      const matchesStatus =
        statusFilter === "all" || toy.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((left, right) => STATUS_RANK[left.status] - STATUS_RANK[right.status]);
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  pageCount: number;
}

export function paginate<T>(
  items: T[],
  requestedPage: number,
  pageSize: number,
): Page<T> {
  const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
  const page = Math.min(Math.max(requestedPage, 1), pageCount);
  return {
    items: items.slice((page - 1) * pageSize, page * pageSize),
    total: items.length,
    page,
    pageCount,
  };
}

export function filterSuppliers(
  suppliers: Supplier[],
  searchQuery: string,
  filter: SupplierFilter,
): Supplier[] {
  const normalizedSearch = searchQuery.trim().toLowerCase();
  return suppliers.filter((supplier) => {
    const matchesSearch =
      !normalizedSearch ||
      `${supplier.supplier_name} ${supplier.supplier_id}`
        .toLowerCase()
        .includes(normalizedSearch);
    const matchesFilter =
      filter === "all" ||
      (filter === "flagged"
        ? supplier.child_labor_flagged
        : !supplier.child_labor_flagged);
    return matchesSearch && matchesFilter;
  });
}

export function mergeSupplierRelevance(
  suppliers: Supplier[],
  relevantSuppliers: Supplier[] | null,
): Supplier[] {
  if (relevantSuppliers === null) {
    return suppliers;
  }

  const relatedToyCounts = new Map(
    relevantSuppliers.map((supplier) => [
      supplier.supplier_id,
      supplier.related_toy_count ?? 0,
    ]),
  );
  return suppliers.map((supplier) => ({
    ...supplier,
    related_toy_count: relatedToyCounts.get(supplier.supplier_id) ?? 0,
  }));
}
