import { useCallback, useState } from "react";

import type { Supplier } from "./api";
import { AppNavigation } from "./components/AppNavigation";
import { TraceMark } from "./components/Shared";
import { SupplierWorkspace } from "./components/SupplierWorkspace";
import { ToyInvestigation } from "./components/ToyInvestigation";
import { ToysWorkspace } from "./components/ToysWorkspace";
import { useFairToyData } from "./useFairToyData";
import type { AppPage } from "./view-model";
import "./styles.css";

function AppShell() {
  const [selectedFinisherId, setSelectedFinisherId] = useState("");
  const [selectedToyId, setSelectedToyId] = useState("");
  const [selectedSupplierId, setSelectedSupplierId] = useState("");
  const [activePage, setActivePage] = useState<AppPage>("traceability");
  const fairToyData = useFairToyData(
    selectedFinisherId,
    selectedToyId,
    selectedSupplierId,
  );
  const { suppliers, updateSupplierFlag } = fairToyData;

  const selectedFinisher = fairToyData.finishers.find(
    ({ finisher_id }) => finisher_id === selectedFinisherId,
  );

  const handleFinisherChange = useCallback((finisherId: string) => {
    setSelectedFinisherId(finisherId);
    setSelectedToyId("");
    setSelectedSupplierId("");
    setActivePage("traceability");
  }, []);

  const openInvestigation = useCallback((toyId: string) => {
    setSelectedToyId(toyId);
    setActivePage("traceability");
  }, []);

  const openSupplierDetail = useCallback((supplierId: string) => {
    setSelectedSupplierId(supplierId);
    setSelectedToyId("");
    setActivePage("suppliers");
  }, []);

  const handlePageChange = useCallback((page: AppPage) => {
    setActivePage(page);
    if (page === "traceability") {
      setSelectedSupplierId("");
    } else {
      setSelectedToyId("");
    }
  }, []);

  const returnToSuppliers = useCallback(() => {
    setSelectedSupplierId("");
  }, []);

  const returnToToys = useCallback(() => {
    setSelectedToyId("");
  }, []);

  const confirmSupplierFlag = useCallback(
    async (
      supplierId: string,
      supplierName: string,
      childLaborFlagged: boolean,
    ) => {
      const action = childLaborFlagged ? "flag" : "unflag";
      const selectedSupplier = suppliers.find(
        (supplier) => supplier.supplier_id === supplierId,
      );
      const hasNoCurrentImpact =
        Boolean(selectedFinisherId) &&
        selectedSupplier?.related_toy_count === 0;
      const impactContext = hasNoCurrentImpact
        ? ` It has no current Toy impact for ${selectedFinisher?.finisher_name}.`
        : "";
      const confirmed = window.confirm(
        `This will ${action} ${supplierName} globally.${impactContext} It may change calculated statuses for other Toys and Finishers. Continue?`,
      );
      if (!confirmed) {
        return;
      }

      await updateSupplierFlag(supplierId, childLaborFlagged);
    },
    [selectedFinisher, selectedFinisherId, suppliers, updateSupplierFlag],
  );

  const confirmSupplierObjectFlag = useCallback(
    async (supplier: Supplier, childLaborFlagged: boolean) => {
      await confirmSupplierFlag(
        supplier.supplier_id,
        supplier.supplier_name,
        childLaborFlagged,
      );
    },
    [confirmSupplierFlag],
  );

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">FAIRTOY / TRACEABILITY WORKSPACE</p>
          <h1>Trace every Toy clearly.</h1>
          <p className="intro">
            Trace catalog evidence for a selected Finisher and review global
            Supplier risk in one focused workspace.
          </p>
        </div>
        <div className="header-actions">
          <AppNavigation
            activePage={activePage}
            toyCount={fairToyData.toys.length}
            supplierCount={fairToyData.suppliers.length}
            onPageChange={handlePageChange}
          />
          <div className="header-mark" aria-hidden="true">
            <TraceMark />
          </div>
        </div>
      </header>

      <main className="dashboard">
        <section className="content-panel panel" aria-live="polite">
          {activePage === "suppliers" && (
            <SupplierWorkspace
              suppliers={fairToyData.suppliers}
              selectedFinisher={selectedFinisher}
              selectedSupplierId={selectedSupplierId}
              supplierDetail={fairToyData.supplierDetail}
              supplierDetailLoading={fairToyData.supplierDetailLoading}
              supplierDetailError={fairToyData.supplierDetailError}
              loading={fairToyData.suppliersLoading}
              error={fairToyData.suppliersError}
              mutationError={fairToyData.mutationError}
              updatingSupplierId={fairToyData.updatingSupplierId}
              onSelectSupplier={openSupplierDetail}
              onBack={returnToSuppliers}
              onSupplierFlag={confirmSupplierObjectFlag}
            />
          )}

          {activePage === "traceability" && !selectedToyId && (
            <ToysWorkspace
              finishers={fairToyData.finishers}
              finishersLoading={fairToyData.finishersLoading}
              finishersError={fairToyData.finishersError}
              selectedFinisherId={selectedFinisherId}
              toys={fairToyData.toys}
              relatedSuppliers={fairToyData.suppliers.filter(
                (supplier) => (supplier.related_toy_count ?? 0) > 0,
              )}
              suppliersLoading={fairToyData.suppliersLoading}
              loading={fairToyData.toysLoading}
              error={fairToyData.toysError}
              selectedToyId={selectedToyId}
              onFinisherChange={handleFinisherChange}
              onSelectToy={openInvestigation}
              onSelectSupplier={openSupplierDetail}
            />
          )}

          {selectedFinisherId &&
            activePage === "traceability" &&
            selectedToyId && (
            <ToyInvestigation
              detail={fairToyData.toyDetail}
              loading={fairToyData.detailLoading}
              error={fairToyData.detailError}
              mutationError={fairToyData.mutationError}
              updatingSupplierId={fairToyData.updatingSupplierId}
              onBack={returnToToys}
              onSupplierFlag={confirmSupplierFlag}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default AppShell;
