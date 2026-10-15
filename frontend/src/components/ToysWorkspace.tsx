import { useEffect, useMemo, useState } from "react";

import type { ToySummary } from "../api";
import {
  filterAndSortToys,
  paginate,
  statusClass,
  statusLabel,
  TOYS_PER_PAGE,
  type ToyStatusFilter,
} from "../view-model";
import { EmptyNotice, EntityIcon, ErrorNotice } from "./Shared";

interface ToysWorkspaceProps {
  finisherId: string;
  toys: ToySummary[];
  loading: boolean;
  error: string | null;
  selectedToyId: string;
  onSelectToy: (toyId: string) => void;
}

export function ToysWorkspace({
  finisherId,
  toys,
  loading,
  error,
  selectedToyId,
  onSelectToy,
}: ToysWorkspaceProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<ToyStatusFilter>("all");
  const [page, setPage] = useState(1);

  useEffect(() => {
    setSearchQuery("");
    setStatusFilter("all");
    setPage(1);
  }, [finisherId]);

  const filteredToys = useMemo(
    () => filterAndSortToys(toys, searchQuery, statusFilter),
    [searchQuery, statusFilter, toys],
  );
  const toyPage = useMemo(
    () => paginate(filteredToys, page, TOYS_PER_PAGE),
    [filteredToys, page],
  );

  return (
    <section aria-labelledby="toys-title">
      <div className="view-heading">
        <div className="heading-with-icon">
          <EntityIcon type="toy" />
          <div>
            <p className="eyebrow">TOY CATALOG</p>
            <h2 id="toys-title">Toys</h2>
            <p className="view-description">
              Search the selected Finisher&apos;s Toys, filter by current impact
              status, and open a Toy investigation for evidence.
            </p>
          </div>
        </div>
        <span className="record-count">{filteredToys.length}</span>
      </div>

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
    </section>
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
      <div className="pagination" aria-label="Toy pagination">
        <span className="pagination-summary">
          Showing{" "}
          {totalToys === 0 ? 0 : (currentPage - 1) * TOYS_PER_PAGE + 1}–
          {Math.min(currentPage * TOYS_PER_PAGE, totalToys)} of {totalToys}
        </span>
        {pageCount > 1 && (
          <div className="pagination-controls">
            <button
              type="button"
              disabled={currentPage === 1}
              onClick={() => onPageChange(currentPage - 1)}
            >
              Previous
            </button>
            <span>
              Page {currentPage} of {pageCount}
            </span>
            <button
              type="button"
              disabled={currentPage === pageCount}
              onClick={() => onPageChange(currentPage + 1)}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
