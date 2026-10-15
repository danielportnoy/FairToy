import { useEffect, useMemo, useState } from "react";

import type { ImpactPath, ToyDetail } from "../api";
import {
  formatCost,
  paginate,
  PARTS_PER_PAGE,
  statusClass,
  statusLabel,
} from "../view-model";
import { EmptyNotice, EntityIcon, ErrorNotice, Pagination } from "./Shared";

interface ToyInvestigationProps {
  detail: ToyDetail | null;
  loading: boolean;
  error: string | null;
  mutationError: string | null;
  updatingSupplierId: string | null;
  onBack: () => void;
  onSupplierFlag: (
    supplierId: string,
    supplierName: string,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

export function ToyInvestigation({
  detail,
  loading,
  error,
  mutationError,
  updatingSupplierId,
  onBack,
  onSupplierFlag,
}: ToyInvestigationProps) {
  return (
    <section aria-labelledby="detail-title">
      <button className="back-button" type="button" onClick={onBack}>
        ← Back to Toys
      </button>
      <div className="view-heading investigation-heading">
        <div className="heading-with-icon">
          <EntityIcon type="toy" />
          <div>
            <p className="eyebrow">TOY INVESTIGATION</p>
            <h2 id="detail-title">Trace the evidence path</h2>
          </div>
        </div>
        {detail && (
          <span className={statusClass(detail.status)}>
            {statusLabel(detail.status)}
          </span>
        )}
      </div>

      {loading && <p className="muted">Loading traceability paths…</p>}
      {error && <ErrorNotice message={error} />}
      {!loading && !error && !detail && (
        <EmptyNotice message="Select a Toy from the Toys workspace." />
      )}
      {!loading && !error && detail && (
        <ToyDetailContent
          detail={detail}
          mutationError={mutationError}
          updatingSupplierId={updatingSupplierId}
          onSupplierFlag={onSupplierFlag}
        />
      )}
    </section>
  );
}

interface ToyDetailContentProps {
  detail: ToyDetail;
  mutationError: string | null;
  updatingSupplierId: string | null;
  onSupplierFlag: (
    supplierId: string,
    supplierName: string,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

function ToyDetailContent({
  detail,
  mutationError,
  updatingSupplierId,
  onSupplierFlag,
}: ToyDetailContentProps) {
  const [page, setPage] = useState(1);
  const partPage = useMemo(
    () => paginate(detail.parts, page, PARTS_PER_PAGE),
    [detail.parts, page],
  );

  useEffect(() => {
    setPage(1);
  }, [detail.toy_id]);

  return (
    <div className="detail-content">
      <div className="detail-title">
        <div className="detail-identity">
          <EntityIcon type="toy" />
          <div>
            <span className="detail-id">{detail.toy_id}</span>
            <h3>{detail.toy_name}</h3>
          </div>
        </div>
      </div>
      <p className="detail-reason">{detail.reason}</p>
      {mutationError && <ErrorNotice message={mutationError} />}

      {detail.parts.length === 0 ? (
        <EmptyNotice message="This Toy has no required Parts." />
      ) : (
        <>
          <div className="part-list">
            {partPage.items.map((part) => (
              <details className="part-card" key={part.part_id}>
                <summary className="part-summary">
                  <div className="part-identity">
                    <EntityIcon type="part" />
                    <div>
                      <span className="detail-id">{part.part_id}</span>
                      <h4>{part.part_name}</h4>
                    </div>
                  </div>
                  <div className="part-meta">
                    <span className="quantity">Qty {part.quantity}</span>
                    <span className={statusClass(part.status)}>
                      {statusLabel(part.status)}
                    </span>
                  </div>
                </summary>
                <div className="part-detail">
                  <p className="part-reason">{part.reason}</p>
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
                </div>
              </details>
            ))}
          </div>
          <Pagination
            ariaLabel="Part pagination"
            currentPage={partPage.page}
            itemLabel="Parts"
            onPageChange={setPage}
            pageCount={partPage.pageCount}
            pageSize={PARTS_PER_PAGE}
            totalItems={partPage.total}
          />
        </>
      )}
    </div>
  );
}

interface PathCardProps {
  path: ImpactPath;
  updating: boolean;
  onSupplierFlag: (
    supplierId: string,
    supplierName: string,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

function PathCard({ path, updating, onSupplierFlag }: PathCardProps) {
  return (
    <div className={`path-card ${path.supplier_flagged ? "is-flagged" : ""}`}>
      <div className="path-topline">
        <div className="path-identity">
          <EntityIcon type="supplier" />
          <div>
            <span className="path-kicker">SUPPLIER</span>
            <strong>{path.supplier_name}</strong>
            <span className="detail-id">{path.supplier_id}</span>
          </div>
        </div>
        <button
          className={`risk-button ${path.supplier_flagged ? "is-flagged" : ""}`}
          type="button"
          disabled={updating}
          onClick={() =>
            void onSupplierFlag(
              path.supplier_id,
              path.supplier_name,
              !path.supplier_flagged,
            )
          }
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
          <span className="path-fact-label">
            <EntityIcon type="factory" />
            <small>Factory</small>
          </span>
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
