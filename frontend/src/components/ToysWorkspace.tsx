import { useEffect, useMemo, useState } from "react";

import type { Finisher, Supplier, ToySummary } from "../api";
import {
  filterAndSortToys,
  paginate,
  statusClass,
  statusLabel,
  SUPPLIERS_PER_PAGE,
  TOYS_PER_PAGE,
  type ToyStatusFilter,
} from "../view-model";
import {
  EmptyNotice,
  EntityIcon,
  ErrorNotice,
  Pagination,
  SelectionRequired,
} from "./Shared";

interface ToysWorkspaceProps {
  finishers: Finisher[];
  finishersLoading: boolean;
  finishersError: string | null;
  selectedFinisherId: string;
  toys: ToySummary[];
  relatedSuppliers: Supplier[];
  suppliersLoading: boolean;
  loading: boolean;
  error: string | null;
  selectedToyId: string;
  onFinisherChange: (finisherId: string) => void;
  onSelectToy: (toyId: string) => void;
  onSelectSupplier: (supplierId: string) => void;
}

export function ToysWorkspace({
  finishers,
  finishersLoading,
  finishersError,
  selectedFinisherId,
  toys,
  relatedSuppliers,
  suppliersLoading,
  loading,
  error,
  selectedToyId,
  onFinisherChange,
  onSelectToy,
  onSelectSupplier,
}: ToysWorkspaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ToyStatusFilter>("all");
  const [page, setPage] = useState(1);

  useEffect(() => {
    setSearchQuery("");
    setStatusFilter("all");
    setPage(1);
  }, [selectedFinisherId]);

  const filteredToys = useMemo(
    () => filterAndSortToys(toys, searchQuery, statusFilter),
    [searchQuery, statusFilter, toys],
  );
  const toyPage = useMemo(
    () => paginate(filteredToys, page, TOYS_PER_PAGE),
    [filteredToys, page],
  );

  return (
    <section aria-labelledby="traceability-title">
      <div className="view-heading">
        <div className="heading-with-icon">
          <EntityIcon type="toy" />
          <div>
            <p className="eyebrow">TOY CATALOG</p>
            <h2 id="traceability-title">Finisher Traceability</h2>
            <p className="view-description">
              Search the selected Finisher&apos;s Toys, filter by current impact
              status, and open a Toy investigation for evidence.
            </p>
          </div>
        </div>
        <span className="record-count">{filteredToys.length}</span>
      </div>

      <div className="catalog-context-card">
        <FinisherPicker
          finishers={finishers}
          loading={finishersLoading}
          error={finishersError}
          selectedFinisherId={selectedFinisherId}
          onChange={onFinisherChange}
        />
        {selectedFinisherId && (
          <RelatedSupplierContext
            key={selectedFinisherId}
            suppliers={relatedSuppliers}
            loading={suppliersLoading}
            onSelectSupplier={onSelectSupplier}
          />
        )}
      </div>

      {!selectedFinisherId && (
        <SelectionRequired loading={finishersLoading} error={finishersError} />
      )}

      {selectedFinisherId && (
        <>
          <div className="search-controls">
            <label className="search-label" htmlFor="toy-search">
              Search Toys
              <input
                id="toy-search"
                type="search"
                placeholder="Name, ID, or reason…"
                value={searchQuery}
                onChange={(event) => {
                  setSearchQuery(event.target.value);
                  setPage(1);
                }}
              />
            </label>
            <label className="search-label" htmlFor="status-filter">
              Status
              <select
                id="status-filter"
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as ToyStatusFilter);
                  setPage(1);
                }}
              >
                <option value="all">All statuses</option>
                <option value="affected">Affected</option>
                <option value="potentially_affected">
                  Potentially affected
                </option>
                <option value="unaffected">Unaffected</option>
              </select>
            </label>
          </div>

          {loading && <p className="muted">Calculating current impact…</p>}
          {error && <ErrorNotice message={error} />}
          {!loading && !error && (
            <ToyQueue
              toys={toyPage.items}
              selectedToyId={selectedToyId}
              totalToys={toyPage.total}
              currentPage={toyPage.page}
              pageCount={toyPage.pageCount}
              onPageChange={setPage}
              onSelect={onSelectToy}
            />
          )}
        </>
      )}
    </section>
  );
}

interface FinisherPickerProps {
  finishers: Finisher[];
  loading: boolean;
  error: string | null;
  selectedFinisherId: string;
  onChange: (finisherId: string) => void;
}

function FinisherPicker({
  finishers,
  loading,
  error,
  selectedFinisherId,
  onChange,
}: FinisherPickerProps) {
  const selectedFinisher = finishers.find(
    ({ finisher_id }) => finisher_id === selectedFinisherId,
  );

  return (
    <div className="finisher-picker">
      <div className="finisher-picker-copy">
        <EntityIcon type="finisher" />
        <div>
          <p className="eyebrow">CATALOG CONTEXT</p>
          <strong>Select the Finisher catalog to inspect</strong>
          <span>
            Toy impact is calculated within one explicit Finisher context.
          </span>
        </div>
      </div>
      <label className="field-label" htmlFor="finisher-select">
        Finisher
        <select
          id="finisher-select"
          value={selectedFinisherId}
          disabled={loading || Boolean(error)}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="">Select a Finisher…</option>
          {finishers.map((finisher) => (
            <option key={finisher.finisher_id} value={finisher.finisher_id}>
              {finisher.finisher_name}
            </option>
          ))}
        </select>
      </label>
      {selectedFinisher && (
        <div className="finisher-picker-active">
          <span className="context-label">Active catalog</span>
          <strong>{selectedFinisher.finisher_name}</strong>
          <span>
            {selectedFinisher.finisher_id}
            {selectedFinisher.hq_country
              ? ` · ${selectedFinisher.hq_country}`
              : ""}
          </span>
        </div>
      )}
    </div>
  );
}

interface RelatedSupplierContextProps {
  suppliers: Supplier[];
  loading: boolean;
  onSelectSupplier: (supplierId: string) => void;
}

function RelatedSupplierContext({
  suppliers,
  loading,
  onSelectSupplier,
}: RelatedSupplierContextProps) {
  const [page, setPage] = useState(1);
  const supplierPage = useMemo(
    () => paginate(suppliers, page, SUPPLIERS_PER_PAGE),
    [page, suppliers],
  );

  return (
    <details className="related-supplier-disclosure">
      <summary className="related-supplier-summary">
        <span className="related-supplier-summary-copy">
          <EntityIcon type="supplier" />
          <span>
            <span className="context-label">Supplier context</span>
            <span role="heading" aria-level={3}>
              Related Suppliers
            </span>
          </span>
        </span>
        <span className="record-count">{suppliers.length}</span>
      </summary>
      <div className="related-supplier-content">
        {loading && <p className="muted">Loading Supplier context…</p>}
        {!loading && suppliers.length === 0 && (
          <p className="muted">No related Suppliers are recorded.</p>
        )}
        {!loading && suppliers.length > 0 && (
          <>
            <div className="related-supplier-list">
              {supplierPage.items.map((supplier) => (
                <button
                  className="related-supplier"
                  key={supplier.supplier_id}
                  type="button"
                  onClick={() => onSelectSupplier(supplier.supplier_id)}
                >
                  <span className="related-supplier-copy">
                    <strong>{supplier.supplier_name}</strong>
                    <span>
                      {supplier.related_toy_count ?? 0} related Toy
                      {supplier.related_toy_count === 1 ? "" : "s"}
                    </span>
                  </span>
                  <span
                    className={`status ${
                      supplier.child_labor_flagged
                        ? "status-affected"
                        : "status-unaffected"
                    }`}
                  >
                    {supplier.child_labor_flagged ? "Flagged" : "Unflagged"}
                  </span>
                </button>
              ))}
            </div>
            <Pagination
              ariaLabel="Related Supplier pagination"
              currentPage={supplierPage.page}
              itemLabel="Suppliers"
              onPageChange={setPage}
              pageCount={supplierPage.pageCount}
              pageSize={SUPPLIERS_PER_PAGE}
              totalItems={supplierPage.total}
            />
          </>
        )}
      </div>
    </details>
  );
}

interface ToyQueueProps {
  toys: ToySummary[];
  selectedToyId: string;
  totalToys: number;
  currentPage: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  onSelect: (toyId: string) => void;
}

function ToyQueue({
  toys,
  selectedToyId,
  totalToys,
  currentPage,
  pageCount,
  onPageChange,
  onSelect,
}: ToyQueueProps) {
  if (toys.length === 0) {
    return (
      <EmptyNotice message="No Toys match the current search and status filters." />
    );
  }

  return (
    <div className="toy-list">
      {toys.map((toy) => (
        <button
          className={`toy-row ${
            toy.toy_id === selectedToyId ? "is-selected" : ""
          }`}
          key={toy.toy_id}
          type="button"
          onClick={() => onSelect(toy.toy_id)}
        >
          <span className="toy-row-leading">
            <EntityIcon type="toy" />
            <span className="toy-row-copy">
              <strong>{toy.toy_name}</strong>
              <span>
                {toy.toy_id} · {toy.reason}
              </span>
            </span>
          </span>
          <span className={statusClass(toy.status)}>
            {statusLabel(toy.status)}
          </span>
        </button>
      ))}
      <Pagination
        ariaLabel="Toy pagination"
        currentPage={currentPage}
        itemLabel="Toys"
        onPageChange={onPageChange}
        pageCount={pageCount}
        pageSize={TOYS_PER_PAGE}
        totalItems={totalToys}
      />
    </div>
  );
}
