import { useCallback, useEffect, useState } from "react";

import {
  type Finisher,
  fairtoyApi,
  type ImpactPath,
  type ImpactStatus,
  type ToyDetail,
  type ToySummary,
} from "./api";
import "./styles.css";

const STATUS_LABELS: Record<ImpactStatus, string> = {
  unaffected: "Unaffected",
  potentially_affected: "Potentially affected",
  affected: "Affected",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function statusLabel(status: ImpactStatus): string {
  return STATUS_LABELS[status];
}

function statusClass(status: ImpactStatus): string {
  return `status status-${status.replace("_", "-")}`;
}

function formatCost(cost: string | null): string {
  return cost === null ? "Not provided" : `$${cost}`;
}

function App() {
  const [finishers, setFinishers] = useState<Finisher[]>([]);
  const [finishersLoading, setFinishersLoading] = useState(true);
  const [finishersError, setFinishersError] = useState<string | null>(null);
  const [selectedFinisherId, setSelectedFinisherId] = useState("");

  const [toys, setToys] = useState<ToySummary[]>([]);
  const [toysLoading, setToysLoading] = useState(false);
  const [toysError, setToysError] = useState<string | null>(null);
  const [selectedToyId, setSelectedToyId] = useState("");

  const [toyDetail, setToyDetail] = useState<ToyDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [updatingSupplierId, setUpdatingSupplierId] = useState<string | null>(
    null,
  );
  const [mutationError, setMutationError] = useState<string | null>(null);

  const loadFinishers = useCallback(async (signal: AbortSignal) => {
    setFinishersLoading(true);
    setFinishersError(null);
    try {
      const nextFinishers = await fairtoyApi.listFinishers(signal);
      if (signal.aborted) {
        return;
      }
      setFinishers(nextFinishers);
      setSelectedFinisherId((currentId) => {
        if (currentId && nextFinishers.some(({ finisher_id }) => finisher_id === currentId)) {
          return currentId;
        }
        return nextFinishers[0]?.finisher_id ?? "";
      });
    } catch (error) {
      if (!signal.aborted && !isAbortError(error)) {
        setFinishersError(errorMessage(error));
      }
    } finally {
      if (!signal.aborted) {
        setFinishersLoading(false);
      }
    }
  }, []);

  const loadToys = useCallback(
    async (finisherId: string, signal: AbortSignal) => {
      setToysLoading(true);
      setToysError(null);
      try {
        const nextToys = await fairtoyApi.listToys(finisherId, signal);
        if (signal.aborted) {
          return;
        }
        setToys(nextToys);
      } catch (error) {
        if (!signal.aborted && !isAbortError(error)) {
          setToysError(errorMessage(error));
        }
      } finally {
        if (!signal.aborted) {
          setToysLoading(false);
        }
      }
    },
    [],
  );

  const loadToyDetail = useCallback(
    async (finisherId: string, toyId: string, signal: AbortSignal) => {
      setDetailLoading(true);
      setDetailError(null);
      try {
        const nextDetail = await fairtoyApi.getToy(toyId, finisherId, signal);
        if (!signal.aborted) {
          setToyDetail(nextDetail);
        }
      } catch (error) {
        if (!signal.aborted && !isAbortError(error)) {
          setDetailError(errorMessage(error));
        }
      } finally {
        if (!signal.aborted) {
          setDetailLoading(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();
    void loadFinishers(controller.signal);
    return () => controller.abort();
  }, [loadFinishers]);

  useEffect(() => {
    setSelectedToyId("");
    setToys([]);
    setToyDetail(null);
    setDetailError(null);
    setMutationError(null);
    if (!selectedFinisherId) {
      setToys([]);
      return;
    }

    const controller = new AbortController();
    void loadToys(selectedFinisherId, controller.signal);
    return () => controller.abort();
  }, [loadToys, selectedFinisherId]);

  useEffect(() => {
    setToyDetail(null);
    setDetailError(null);
    if (!selectedFinisherId || !selectedToyId) {
      return;
    }

    const controller = new AbortController();
    void loadToyDetail(selectedFinisherId, selectedToyId, controller.signal);
    return () => controller.abort();
  }, [loadToyDetail, selectedFinisherId, selectedToyId]);

  const selectedFinisher = finishers.find(
    ({ finisher_id }) => finisher_id === selectedFinisherId,
  );

  async function handleSupplierFlag(
    supplierId: string,
    childLaborFlagged: boolean,
  ) {
    if (!selectedFinisherId) {
      return;
    }

    setUpdatingSupplierId(supplierId);
    setMutationError(null);
    try {
      await fairtoyApi.updateSupplierFlag(supplierId, childLaborFlagged);
      const [nextToys, nextDetail] = await Promise.all([
        fairtoyApi.listToys(selectedFinisherId),
        selectedToyId
          ? fairtoyApi.getToy(selectedToyId, selectedFinisherId)
          : Promise.resolve(null),
      ]);
      setToys(nextToys);
      setToyDetail(nextDetail);
    } catch (error) {
      setMutationError(errorMessage(error));
    } finally {
      setUpdatingSupplierId(null);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">FAIRTOY / TRACEABILITY WORKSPACE</p>
          <h1>See the path behind every toy.</h1>
          <p className="intro">
            Explore catalog exposure from Toy to Part, Supplier, and Factory.
            The impact status is calculated from current Supplier flags.
          </p>
        </div>
        <div className="header-mark" aria-hidden="true">
          <span>FT</span>
        </div>
      </header>

      <main className="dashboard">
        <aside className="catalog-panel panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">CATALOG CONTEXT</p>
              <h2>Select a Finisher</h2>
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
                onChange={(event) => setSelectedFinisherId(event.target.value)}
              >
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

          <div className="scope-note">
            <span className="scope-dot" />
            Supplier risk is global and updates every relevant catalog view.
          </div>
        </aside>

        <section className="toy-panel panel" aria-labelledby="toy-list-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">TOY IMPACT SUMMARY</p>
              <h2 id="toy-list-title">Catalog Toys</h2>
            </div>
            <span className="record-count">{toys.length}</span>
          </div>

          {toysLoading && <p className="muted">Calculating current impact…</p>}
          {toysError && <ErrorNotice message={toysError} />}
          {!toysLoading && !toysError && selectedFinisherId && toys.length === 0 && (
            <EmptyNotice message="This Finisher has no catalog Toys." />
          )}
          {!toysLoading && !toysError && toys.length > 0 && (
            <div className="toy-list">
              {toys.map((toy) => (
                <button
                  className={`toy-row ${
                    toy.toy_id === selectedToyId ? "is-selected" : ""
                  }`}
                  key={toy.toy_id}
                  type="button"
                  onClick={() => setSelectedToyId(toy.toy_id)}
                >
                  <span className="toy-row-copy">
                    <strong>{toy.toy_name}</strong>
                    <span>
                      {toy.toy_id} · {toy.reason}
                    </span>
                  </span>
                  <span className={statusClass(toy.status)}>
                    {statusLabel(toy.status)}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="detail-panel panel" aria-labelledby="detail-title">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">TRACEABILITY DETAIL</p>
              <h2 id="detail-title">Why this status?</h2>
            </div>
            {toyDetail && <span className={statusClass(toyDetail.status)}>{statusLabel(toyDetail.status)}</span>}
          </div>

          {detailLoading && <p className="muted">Loading traceability paths…</p>}
          {detailError && <ErrorNotice message={detailError} />}
          {!detailLoading && !detailError && !toyDetail && (
            <EmptyNotice message="Select a Toy to inspect its parts and possible sourcing paths." />
          )}
          {!detailLoading && !detailError && toyDetail && (
            <ToyDetailView
              detail={toyDetail}
              mutationError={mutationError}
              updatingSupplierId={updatingSupplierId}
              onSupplierFlag={handleSupplierFlag}
            />
          )}
        </section>
      </main>
    </div>
  );
}

interface ToyDetailViewProps {
  detail: ToyDetail;
  mutationError: string | null;
  updatingSupplierId: string | null;
  onSupplierFlag: (supplierId: string, childLaborFlagged: boolean) => Promise<void>;
}

function ToyDetailView({
  detail,
  mutationError,
  updatingSupplierId,
  onSupplierFlag,
}: ToyDetailViewProps) {
  return (
    <div className="detail-content">
      <div className="detail-title">
        <div>
          <span className="detail-id">{detail.toy_id}</span>
          <h3>{detail.toy_name}</h3>
        </div>
        <span className="reason-code">{detail.reason_code}</span>
      </div>
      <p className="detail-reason">{detail.reason}</p>
      {mutationError && <ErrorNotice message={mutationError} />}

      {detail.parts.length === 0 ? (
        <EmptyNotice message="This Toy has no required Parts." />
      ) : (
        <div className="part-list">
          {detail.parts.map((part) => (
            <article className="part-card" key={part.part_id}>
              <div className="part-heading">
                <div>
                  <span className="detail-id">{part.part_id}</span>
                  <h4>{part.part_name}</h4>
                </div>
                <div className="part-meta">
                  <span className="quantity">Qty {part.quantity}</span>
                  <span className={statusClass(part.status)}>
                    {statusLabel(part.status)}
                  </span>
                </div>
              </div>
              <p className="part-reason">
                <span>{part.reason_code}</span>
                {part.reason}
              </p>
              {part.paths.length === 0 ? (
                <EmptyNotice message="No known possible sources." compact />
              ) : (
                <div className="path-list">
                  {part.paths.map((path) => (
                    <PathCard
                      key={`${path.supplier_id}-${path.factory_id}`}
                      path={path}
                      updating={updatingSupplierId === path.supplier_id}
                      onSupplierFlag={onSupplierFlag}
                    />
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

interface PathCardProps {
  path: ImpactPath;
  updating: boolean;
  onSupplierFlag: (supplierId: string, childLaborFlagged: boolean) => Promise<void>;
}

function PathCard({ path, updating, onSupplierFlag }: PathCardProps) {
  return (
    <div className={`path-card ${path.supplier_flagged ? "is-flagged" : ""}`}>
      <div className="path-topline">
        <div>
          <span className="path-kicker">SUPPLIER</span>
          <strong>{path.supplier_name}</strong>
          <span className="detail-id">{path.supplier_id}</span>
        </div>
        <button
          className={`risk-button ${path.supplier_flagged ? "is-flagged" : ""}`}
          type="button"
          disabled={updating}
          onClick={() => void onSupplierFlag(path.supplier_id, !path.supplier_flagged)}
        >
          {updating
            ? "Saving…"
            : path.supplier_flagged
              ? "Unflag supplier"
              : "Flag supplier"}
        </button>
      </div>
      <div className="path-facts">
        <span>
          <small>Factory</small>
          {path.factory_name} <em>{path.factory_id}</em>
        </span>
        <span>
          <small>Unit cost</small>
          {formatCost(path.unit_cost_usd)}
        </span>
        <span>
          <small>Current risk</small>
          {path.supplier_flagged ? "Flagged for child labor" : "No current flag"}
        </span>
      </div>
    </div>
  );
}

interface NoticeProps {
  message: string;
  compact?: boolean;
}

function EmptyNotice({ message, compact = false }: NoticeProps) {
  return <p className={`notice notice-empty ${compact ? "is-compact" : ""}`}>{message}</p>;
}

function ErrorNotice({ message }: NoticeProps) {
  return (
    <p className="notice notice-error" role="alert">
      {message}
    </p>
  );
}

export default App;
