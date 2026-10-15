import type { Finisher } from "../api";
import type { AppPage } from "../view-model";
import { EmptyNotice, EntityIcon, ErrorNotice } from "./Shared";

interface FinisherSidebarProps {
  finishers: Finisher[];
  finishersLoading: boolean;
  finishersError: string | null;
  selectedFinisherId: string;
  selectedFinisher: Finisher | undefined;
  activePage: AppPage;
  toyCount: number;
  supplierCount: number;
  onFinisherChange: (finisherId: string) => void;
  onPageChange: (page: AppPage) => void;
}

export function FinisherSidebar({
  finishers,
  finishersLoading,
  finishersError,
  selectedFinisherId,
  selectedFinisher,
  activePage,
  toyCount,
  supplierCount,
  onFinisherChange,
  onPageChange,
}: FinisherSidebarProps) {
  return (
    <aside className="catalog-panel panel">
      <div className="panel-heading">
        <div className="heading-with-icon">
          <EntityIcon type="finisher" />
          <div>
            <p className="eyebrow">CATALOG CONTEXT</p>
            <h2>Choose a Finisher</h2>
          </div>
        </div>
        <span className="record-count">{finishers.length}</span>
      </div>

      {finishersLoading && <p className="muted">Loading Finishers…</p>}
      {finishersError && <ErrorNotice message={finishersError} />}
      {!finishersLoading && !finishersError && finishers.length === 0 && (
        <EmptyNotice message="No Finishers are available." />
      )}
      {!finishersLoading && !finishersError && finishers.length > 0 && (
        <label className="field-label" htmlFor="finisher-select">
          Finisher
          <select
            id="finisher-select"
            value={selectedFinisherId}
            onChange={(event) => onFinisherChange(event.target.value)}
          >
            <option value="">Select a Finisher…</option>
            {finishers.map((finisher) => (
              <option key={finisher.finisher_id} value={finisher.finisher_id}>
                {finisher.finisher_name}
              </option>
            ))}
          </select>
        </label>
      )}

      {selectedFinisher && (
        <div className="context-card">
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

      <nav className="view-tabs" aria-label="Pages">
        <button
          className={activePage === "traceability" ? "is-active" : ""}
          type="button"
          onClick={() => onPageChange("traceability")}
        >
          <span>Finisher Traceability</span>
          <strong>{toyCount}</strong>
        </button>
        <button
          className={activePage === "suppliers" ? "is-active" : ""}
          type="button"
          onClick={() => onPageChange("suppliers")}
        >
          <span>Suppliers</span>
          <strong>{supplierCount}</strong>
        </button>
      </nav>

      {!selectedFinisherId && (
        <div className="selection-state">
          <span className="scope-dot" />
          Select a Finisher to load Toys; the Suppliers page is available now.
        </div>
      )}

      <div className="scope-note">
        <span className="scope-dot" />
        Supplier risk is global and updates every relevant catalog view.
      </div>
    </aside>
  );
}
