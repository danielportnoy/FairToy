import type { Finisher } from "../api";
import type { Workspace } from "../view-model";
import { EmptyNotice, EntityIcon, ErrorNotice } from "./Shared";

interface FinisherSidebarProps {
  finishers: Finisher[];
  finishersLoading: boolean;
  finishersError: string | null;
  selectedFinisherId: string;
  selectedFinisher: Finisher | undefined;
  activeWorkspace: Workspace;
  toyCount: number;
  supplierCount: number;
  onFinisherChange: (finisherId: string) => void;
  onWorkspaceChange: (workspace: "toys" | "suppliers") => void;
}

export function FinisherSidebar({
  finishers,
  finishersLoading,
  finishersError,
  selectedFinisherId,
  selectedFinisher,
  activeWorkspace,
  toyCount,
  supplierCount,
  onFinisherChange,
  onWorkspaceChange,
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

      <nav className="view-tabs" aria-label="Workspaces">
        <button
          className={
            activeWorkspace === "toys" || activeWorkspace === "investigation"
              ? "is-active"
              : ""
          }
          type="button"
          onClick={() => onWorkspaceChange("toys")}
        >
          <span>Toys</span>
          <strong>{toyCount}</strong>
        </button>
        <button
          className={activeWorkspace === "suppliers" ? "is-active" : ""}
          type="button"
          onClick={() => onWorkspaceChange("suppliers")}
        >
          <span>Suppliers</span>
          <strong>{supplierCount}</strong>
        </button>
      </nav>

      {!selectedFinisherId && (
        <div className="selection-state">
          <span className="scope-dot" />
          Select a Finisher to load Toys; Supplier Review is available now.
        </div>
      )}

      <div className="scope-note">
        <span className="scope-dot" />
        Supplier risk is global and updates every relevant catalog view.
      </div>
    </aside>
  );
}
