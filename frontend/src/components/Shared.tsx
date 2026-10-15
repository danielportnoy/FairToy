export function TraceMark() {
  return (
    <svg
      className="trace-mark"
      viewBox="0 0 48 48"
      role="img"
      aria-label="FairToy traceability"
    >
      <path
        className="trace-mark-line"
        d="M11 12 34 18 17 35 11 12M17 35l21 1-4-18"
      />
      <circle className="trace-mark-node" cx="11" cy="12" r="4" />
      <circle className="trace-mark-node" cx="34" cy="18" r="4" />
      <circle className="trace-mark-node" cx="17" cy="35" r="4" />
      <circle className="trace-mark-node" cx="38" cy="36" r="4" />
    </svg>
  );
}

export type EntityType =
  | "finisher"
  | "supplier"
  | "toy"
  | "part"
  | "factory";

export function EntityIcon({ type }: { type: EntityType }) {
  return (
    <span className={`entity-icon entity-icon-${type}`} aria-hidden="true">
      <svg viewBox="0 0 24 24">
        {type === "finisher" && (
          <path d="M4 20h16M6 20V9h12v11M4 9l8-5 8 5M9 13h2m2 0h2m-6 3h2m2 0h2" />
        )}
        {type === "supplier" && (
          <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Zm-8 4.5 8 4.5 8-4.5M12 12v9" />
        )}
        {type === "toy" && (
          <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Zm-8 4.5 8 4.5 8-4.5M12 12v9" />
        )}
        {type === "part" && (
          <path d="m12 3 1.7 2.3 2.9-.2.9 2.8 2.7 1.2-1.1 2.7 1.1 2.8-2.7 1.2-.9 2.8-2.9-.2L12 21l-1.7-2.3-2.9.2-.9-2.8-2.7-1.2 1.1-2.8-1.1-2.7 2.7-1.2.9-2.8 2.9.2L12 3Z" />
        )}
        {type === "part" && <circle cx="12" cy="12" r="2.5" />}
        {type === "factory" && (
          <path d="M3 20h18M5 20V11l5 3V9l5 3V7l4 2v11M8 17h1m3 0h1m3 0h1" />
        )}
      </svg>
    </span>
  );
}

interface NoticeProps {
  message: string;
  compact?: boolean;
}

export function EmptyNotice({ message, compact = false }: NoticeProps) {
  return (
    <p className={`notice notice-empty ${compact ? "is-compact" : ""}`}>
      {message}
    </p>
  );
}

export function ErrorNotice({ message }: NoticeProps) {
  return (
    <p className="notice notice-error" role="alert">
      {message}
    </p>
  );
}

interface SelectionRequiredProps {
  loading: boolean;
  error: string | null;
}

export function SelectionRequired({
  loading,
  error,
}: SelectionRequiredProps) {
  return (
    <div className="selection-required">
      <span className="selection-icon">
        <TraceMark />
      </span>
      <p className="eyebrow">FINISHER CONTEXT REQUIRED</p>
      <h2>Choose a Finisher to begin.</h2>
      {loading && <p className="muted">Loading available Finishers…</p>}
      {error && <ErrorNotice message={error} />}
      {!loading && !error && (
        <p>
          FairToy keeps catalog context explicit so risk findings are never
          shown for the wrong organization.
        </p>
      )}
    </div>
  );
}
