import { useMemo, useState } from "react";

import type { Finisher, Supplier, SupplierDetail as SupplierDetailData } from "../api";
import {
  filterSuppliers,
  formatDate,
  paginate,
  SUPPLIERS_PER_PAGE,
  type SupplierFilter,
} from "../view-model";
import {
  EmptyNotice,
  EntityIcon,
  ErrorNotice,
  Pagination,
} from "./Shared";
import { SupplierDetail } from "./SupplierDetail";

interface SupplierWorkspaceProps {
  suppliers: Supplier[];
  selectedFinisher: Finisher | undefined;
  selectedSupplierId: string;
  supplierDetail: SupplierDetailData | null;
  supplierDetailLoading: boolean;
  supplierDetailError: string | null;
  loading: boolean;
  error: string | null;
  mutationError: string | null;
  updatingSupplierId: string | null;
  onSelectSupplier: (supplierId: string) => void;
  onBack: () => void;
  onSupplierFlag: (
    supplier: Supplier,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

export function SupplierWorkspace({
  suppliers,
  selectedFinisher,
  selectedSupplierId,
  supplierDetail,
  supplierDetailLoading,
  supplierDetailError,
  loading,
  error,
  mutationError,
  updatingSupplierId,
  onSelectSupplier,
  onBack,
  onSupplierFlag,
}: SupplierWorkspaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filter, setFilter] = useState<SupplierFilter>("all");
  const [page, setPage] = useState(1);
  const visibleSuppliers = useMemo(
    () => filterSuppliers(suppliers, searchQuery, filter),
    [filter, searchQuery, suppliers],
  );
  const supplierPage = useMemo(
    () => paginate(visibleSuppliers, page, SUPPLIERS_PER_PAGE),
    [page, visibleSuppliers],
  );
  const selectedSupplier = suppliers.find(
    (supplier) => supplier.supplier_id === selectedSupplierId,
  );

  if (selectedSupplierId) {
    return (
      <SupplierDetail
        detail={supplierDetail}
        selectedFinisher={selectedFinisher}
        relatedToyCount={selectedSupplier?.related_toy_count}
        loading={supplierDetailLoading}
        error={supplierDetailError}
        mutationError={mutationError}
        updating={updatingSupplierId === selectedSupplierId}
        onBack={onBack}
        onSupplierFlag={onSupplierFlag}
      />
    );
  }

  return (
    <section aria-labelledby="suppliers-title">
      <div className="view-heading">
        <div className="heading-with-icon">
          <EntityIcon type="supplier" />
          <div>
            <p className="eyebrow">SUPPLIERS PAGE</p>
            <h2 id="suppliers-title">Suppliers</h2>
            <p className="view-description">
              Review all Suppliers and their global risk state.
              {selectedFinisher
                ? ` Related-Toy counts below are for ${selectedFinisher.finisher_name}.`
                : " Catalog relevance appears when a Finisher is selected in Traceability."}
            </p>
          </div>
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
            onChange={(event) => {
              setSearchQuery(event.target.value);
              setPage(1);
            }}
          />
        </label>
        <label className="search-label" htmlFor="supplier-filter">
          Risk state
          <select
            id="supplier-filter"
            value={filter}
            onChange={(event) => {
              setFilter(event.target.value as SupplierFilter);
              setPage(1);
            }}
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
          <div className="supplier-list">
            {supplierPage.items.map((supplier) => (
              <SupplierRow
                key={supplier.supplier_id}
                supplier={supplier}
                selectedFinisher={selectedFinisher}
                updating={updatingSupplierId === supplier.supplier_id}
                onSelectSupplier={onSelectSupplier}
                onSupplierFlag={onSupplierFlag}
              />
            ))}
          </div>
          <Pagination
            ariaLabel="Supplier pagination"
            currentPage={supplierPage.page}
            itemLabel="Suppliers"
            onPageChange={setPage}
            pageCount={supplierPage.pageCount}
            pageSize={SUPPLIERS_PER_PAGE}
            totalItems={supplierPage.total}
          />
        </>
      )}
    </section>
  );
}

interface SupplierRowProps {
  supplier: Supplier;
  selectedFinisher: Finisher | undefined;
  updating: boolean;
  onSelectSupplier: (supplierId: string) => void;
  onSupplierFlag: (
    supplier: Supplier,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

function SupplierRow({
  supplier,
  selectedFinisher,
  updating,
  onSelectSupplier,
  onSupplierFlag,
}: SupplierRowProps) {
  const relatedToyCount = supplier.related_toy_count ?? 0;
  const hasNoCurrentImpact =
    Boolean(selectedFinisher) &&
    supplier.child_labor_flagged &&
    relatedToyCount === 0;

  return (
    <article className="supplier-row">
      <button
        className="supplier-link"
        type="button"
        onClick={() => onSelectSupplier(supplier.supplier_id)}
      >
        <EntityIcon type="supplier" />
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
      </button>
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
