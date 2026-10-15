import type { AppPage } from "../view-model";

interface AppNavigationProps {
  activePage: AppPage;
  toyCount: number;
  supplierCount: number;
  onPageChange: (page: AppPage) => void;
}

export function AppNavigation({
  activePage,
  toyCount,
  supplierCount,
  onPageChange,
}: AppNavigationProps) {
  return (
    <nav className="primary-navigation" aria-label="Primary pages">
      <button
        className={activePage === "traceability" ? "is-active" : ""}
        type="button"
        onClick={() => onPageChange("traceability")}
      >
        <span>Traceability</span>
        <strong className="record-count navigation-count">{toyCount}</strong>
      </button>
      <button
        className={activePage === "suppliers" ? "is-active" : ""}
        type="button"
        onClick={() => onPageChange("suppliers")}
      >
        <span>Suppliers</span>
        <strong className="record-count navigation-count">
          {supplierCount}
        </strong>
      </button>
    </nav>
  );
}
