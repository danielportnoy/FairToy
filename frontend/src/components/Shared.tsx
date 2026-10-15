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
      <span className="selection-icon" aria-hidden="true">
        FT
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
