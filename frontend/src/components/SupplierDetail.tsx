import type { ReactNode } from "react";

import type {
  Finisher,
  Supplier,
  SupplierDetail as SupplierDetailData,
} from "../api";
import { formatDate } from "../view-model";
import { EmptyNotice, EntityIcon, ErrorNotice } from "./Shared";

interface SupplierDetailProps {
  detail: SupplierDetailData | null;
  selectedFinisher: Finisher | undefined;
  relatedToyCount: number | null | undefined;
  loading: boolean;
  error: string | null;
  mutationError: string | null;
  updating: boolean;
  onBack: () => void;
  onSupplierFlag: (
    supplier: Supplier,
    childLaborFlagged: boolean,
  ) => void | Promise<void>;
}

export function SupplierDetail({
  detail,
  selectedFinisher,
  relatedToyCount,
  loading,
  error,
  mutationError,
  updating,
  onBack,
  onSupplierFlag,
}: SupplierDetailProps) {
  return (
    <section aria-labelledby="supplier-detail-title">
      <button className="back-button" type="button" onClick={onBack}>
        ← Back to Suppliers
      </button>

      <div className="view-heading investigation-heading">
        <div className="heading-with-icon">
          <EntityIcon type="supplier" />
          <div>
            <p className="eyebrow">SUPPLIER DETAIL</p>
            <h2 id="supplier-detail-title">
              {detail?.supplier_name ?? "Supplier detail"}
            </h2>
            {detail && (
              <p className="view-description">
                {detail.supplier_id} · Read-only traceability context
              </p>
            )}
          </div>
        </div>
        {detail && (
          <div className="supplier-detail-risk">
            <span
              className={`status ${
                detail.child_labor_flagged
                  ? "status-affected"
                  : "status-unaffected"
              }`}
            >
              {detail.child_labor_flagged ? "Flagged" : "Unflagged"}
            </span>
            <button
              className={`risk-button ${
                detail.child_labor_flagged ? "is-flagged" : ""
              }`}
              type="button"
              disabled={updating}
              onClick={() =>
                void onSupplierFlag(
                  detail,
                  !detail.child_labor_flagged,
                )
              }
            >
              {updating
                ? "Saving…"
                : detail.child_labor_flagged
                  ? "Unflag supplier"
                  : "Flag supplier"}
            </button>
          </div>
        )}
      </div>

      {loading && <p className="muted">Loading Supplier detail…</p>}
      {error && <ErrorNotice message={error} />}
      {mutationError && <ErrorNotice message={mutationError} />}
      {!loading && !error && !detail && (
        <EmptyNotice message="Select a Supplier to inspect its traceability context." />
      )}
      {!loading && !error && detail && (
        <div className="supplier-detail-content">
          <div className="supplier-detail-summary">
            <div>
              <span className="context-label">Headquarters</span>
              <strong>{detail.hq_country ?? "Not provided"}</strong>
            </div>
            <div>
              <span className="context-label">Flagged at</span>
              <strong>
                {detail.flagged_at
                  ? formatDate(detail.flagged_at)
                  : "Not currently flagged"}
              </strong>
            </div>
            {selectedFinisher && (
              <div>
                <span className="context-label">
                  Relevance · {selectedFinisher.finisher_name}
                </span>
                <strong>
                  {relatedToyCount ?? 0} related Toy
                  {relatedToyCount === 1 ? "" : "s"}
                </strong>
              </div>
            )}
          </div>

          <SupplierEntitySection
            icon="factory"
            title="Factories"
            count={detail.factories.length}
          >
            {detail.factories.length === 0 ? (
              <EmptyNotice message="No Factories are recorded for this Supplier." compact />
            ) : (
              <div className="supplier-detail-list">
                {detail.factories.map((factory) => (
                  <article className="supplier-detail-row" key={factory.factory_id}>
                    <EntityIcon type="factory" />
                    <div>
                      <strong>{factory.factory_name}</strong>
                      <span className="detail-id">{factory.factory_id}</span>
                      <span>
                        {[
                          factory.address_line,
                          factory.city,
                          factory.country,
                        ]
                          .filter(Boolean)
                          .join(" · ") || "Location not provided"}
                      </span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </SupplierEntitySection>

          <SupplierEntitySection
            icon="part"
            title="Supplied Parts"
            count={detail.supplied_parts.length}
          >
            {detail.supplied_parts.length === 0 ? (
              <EmptyNotice message="No supplied Parts are recorded for this Supplier." compact />
            ) : (
              <div className="supplier-detail-list">
                {detail.supplied_parts.map((part) => (
                  <article className="supplier-detail-row" key={part.part_id}>
                    <EntityIcon type="part" />
                    <div>
                      <strong>{part.part_name}</strong>
                      <span className="detail-id">{part.part_id}</span>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </SupplierEntitySection>
        </div>
      )}
    </section>
  );
}

interface SupplierEntitySectionProps {
  icon: "factory" | "part";
  title: string;
  count: number;
  children: ReactNode;
}

function SupplierEntitySection({
  icon,
  title,
  count,
  children,
}: SupplierEntitySectionProps) {
  return (
    <section className="supplier-detail-section">
      <div className="supplier-detail-section-heading">
        <div className="heading-with-icon">
          <EntityIcon type={icon} />
          <h3>{title}</h3>
        </div>
        <span className="record-count">{count}</span>
      </div>
      {children}
    </section>
  );
}
