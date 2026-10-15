import { useMemo, useState } from "react";

import type { Finisher, Supplier } from "../api";
import {
  filterSuppliers,
  formatDate,
  type SupplierFilter,
} from "../view-model";
import { EmptyNotice, ErrorNotice } from "./Shared";

interface SupplierWorkspaceProps {
  suppliers: Supplier[];
  selectedFinisher: Finisher | undefined;
  loading: boolean;
  error: string | null;
  mutationError: string | null;
  updatingSupplierId: string | null;
  onSupplierFlag: (
    supplier: Supplier,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

export function SupplierWorkspace({
  suppliers,
  selectedFinisher,
  loading,
  error,
  mutationError,
  updatingSupplierId,
  onSupplierFlag,
}: SupplierWorkspaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<SupplierFilter>("all");
  const visibleSuppliers = useMemo(
    () => filterSuppliers(suppliers, searchQuery, filter),
    [filter, searchQuery, suppliers],
  );

  return (
    <section aria-labelledby="supplier-review-title">
      <div className="view-heading">
        <div>
          <p className="eyebrow">SUPPLIER WORKSPACE</p>
          <h2 id="supplier-review-title">Supplier Review</h2>
          <p className="view-description">
            Review all Suppliers and their global risk state.
            {selectedFinisher
              ? ` Related-Toy counts below are for ${selectedFinisher.finisher_name}.`
              : " Select a Finisher to see catalog relevance."}
          </p>
        </div>
        <span className="record-count">{visibleSuppliers.length}</span>
      </div>

      <div className="search-controls">
        <label className="search-label" htmlFor="supplier-search">
          Search Suppliers
          <input
            id="supplier-search"
            type="search"
            placeholder="Name or ID…"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
          />
        </label>
        <label className="search-label" htmlFor="supplier-filter">
          Risk state
          <select
            id="supplier-filter"
            value={filter}
            onChange={(event) =>
              setFilter(event.target.value as SupplierFilter)
            }
          >
            <option value="all">All Suppliers</option>
            <option value="flagged">Flagged</option>
            <option value="unflagged">Unflagged</option>
          </select>
        </label>
      </div>

      {loading && <p className="muted">Loading Suppliers…</p>}
      {error && <ErrorNotice message={error} />}
      {mutationError && <ErrorNotice message={mutationError} />}
      {!loading && !error && visibleSuppliers.length === 0 && (
        <EmptyNotice
          message={
            suppliers.length === 0
              ? "No Suppliers are available."
              : "No Suppliers match the current search and risk filters."
          }
        />
      )}
      {!loading && !error && visibleSuppliers.length > 0 && (
        <>
          <p className="result-note">
            Showing {visibleSuppliers.length} of {suppliers.length} Suppliers.
          </p>
          <div className="supplier-list">
            {visibleSuppliers.map((supplier) => (
              <SupplierRow
                key={supplier.supplier_id}
                supplier={supplier}
                selectedFinisher={selectedFinisher}
                updating={updatingSupplierId === supplier.supplier_id}
                onSupplierFlag={onSupplierFlag}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

interface SupplierRowProps {
  supplier: Supplier;
  selectedFinisher: Finisher | undefined;
  updating: boolean;
  onSupplierFlag: (
    supplier: Supplier,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

function SupplierRow({
  supplier,
  selectedFinisher,
  updating,
  onSupplierFlag,
}: SupplierRowProps) {
  const relatedToyCount = supplier.related_toy_count ?? 0;
  const hasNoCurrentImpact =
    Boolean(selectedFinisher) &&
    supplier.child_labor_flagged &&
    relatedToyCount === 0;

  return (
    <article className="supplier-row">
      <div className="supplier-main">
        <span className="detail-id">{supplier.supplier_id}</span>
        <strong>{supplier.supplier_name}</strong>
        <span>
          {selectedFinisher ? (
            <>
              {relatedToyCount} related Toy{relatedToyCount === 1 ? "" : "s"}
              {hasNoCurrentImpact
                ? " · no current Toy impact for this Finisher"
                : ""}
            </>
          ) : (
            "Global Supplier"
          )}
          {supplier.flagged_at
            ? ` · flagged ${formatDate(supplier.flagged_at)}`
            : " · not flagged"}
        </span>
      </div>
      <div className="supplier-action">
        <span
          className={`status ${
            supplier.child_labor_flagged
              ? "status-affected"
              : "status-unaffected"
          }`}
        >
          {supplier.child_labor_flagged ? "Flagged" : "Unflagged"}
        </span>
        <button
          className={`risk-button ${
            supplier.child_labor_flagged ? "is-flagged" : ""
          }`}
          type="button"
          disabled={updating}
          onClick={() =>
            void onSupplierFlag(supplier, !supplier.child_labor_flagged)
          }
        >
          {updating
            ? "Saving…"
            : supplier.child_labor_flagged
              ? "Unflag supplier"
              : "Flag supplier"}
        </button>
      </div>
    </article>
  );
}
