import { useCallback, useState } from "react";

import type { Supplier } from "./api";
import { FinisherSidebar } from "./components/FinisherSidebar";
import { SelectionRequired } from "./components/Shared";
import { SupplierWorkspace } from "./components/SupplierWorkspace";
import { ToyInvestigation } from "./components/ToyInvestigation";
import { ToysWorkspace } from "./components/ToysWorkspace";
import { useFairToyData } from "./useFairToyData";
import type { Workspace } from "./view-model";
import "./styles.css";

function AppShell() {
  const [selectedFinisherId, setSelectedFinisherId] = useState("");
  const [selectedToyId, setSelectedToyId] = useState("");
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace>("toys");
  const fairToyData = useFairToyData(selectedFinisherId, selectedToyId);
  const { suppliers, updateSupplierFlag } = fairToyData;

  const selectedFinisher = fairToyData.finishers.find(
    ({ finisher_id }) => finisher_id === selectedFinisherId,
  );

  const handleFinisherChange = useCallback((finisherId: string) => {
    setSelectedFinisherId(finisherId);
    setSelectedToyId("");
    setActiveWorkspace("toys");
  }, []);

  const openInvestigation = useCallback((toyId: string) => {
    setSelectedToyId(toyId);
    setActiveWorkspace("investigation");
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

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">FAIRTOY / TRACEABILITY WORKSPACE</p>
          <h1>Trace every Toy clearly.</h1>
          <p className="intro">
            Search the selected Finisher&apos;s catalog, filter current impact
            status, and open a Toy investigation for the evidence path.
          </p>
        </div>
        <div className="header-mark" aria-hidden="true">
          <span>FT</span>
        </div>
      </header>

      <main className="dashboard">
        <FinisherSidebar
          finishers={fairToyData.finishers}
          finishersLoading={fairToyData.finishersLoading}
          finishersError={fairToyData.finishersError}
          selectedFinisherId={selectedFinisherId}
          selectedFinisher={selectedFinisher}
          activeWorkspace={activeWorkspace}
          toyCount={fairToyData.toys.length}
          supplierCount={fairToyData.suppliers.length}
          onFinisherChange={handleFinisherChange}
          onWorkspaceChange={setActiveWorkspace}
        />

        <section className="content-panel panel" aria-live="polite">
          {activeWorkspace === "suppliers" && (
            <SupplierWorkspace
              suppliers={fairToyData.suppliers}
              selectedFinisher={selectedFinisher}
              loading={fairToyData.suppliersLoading}
              error={fairToyData.suppliersError}
              mutationError={fairToyData.mutationError}
              updatingSupplierId={fairToyData.updatingSupplierId}
              onSupplierFlag={(supplier: Supplier, desired) =>
                void confirmSupplierFlag(
                  supplier.supplier_id,
                  supplier.supplier_name,
                  desired,
                )
              }
            />
          )}

          {!selectedFinisherId && activeWorkspace !== "suppliers" && (
            <SelectionRequired
              loading={fairToyData.finishersLoading}
              error={fairToyData.finishersError}
            />
          )}

          {selectedFinisherId && activeWorkspace === "toys" && (
            <ToysWorkspace
              finisherId={selectedFinisherId}
              toys={fairToyData.toys}
              loading={fairToyData.toysLoading}
              error={fairToyData.toysError}
              selectedToyId={selectedToyId}
              onSelectToy={openInvestigation}
            />
          )}

          {selectedFinisherId && activeWorkspace === "investigation" && (
            <ToyInvestigation
              detail={fairToyData.toyDetail}
              loading={fairToyData.detailLoading}
              error={fairToyData.detailError}
              mutationError={fairToyData.mutationError}
              updatingSupplierId={fairToyData.updatingSupplierId}
              onBack={() => setActiveWorkspace("toys")}
              onSupplierFlag={confirmSupplierFlag}
            />
          )}
        </section>
      </main>
    </div>
  );
}

export default AppShell;
