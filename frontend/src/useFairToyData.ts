import { useCallback, useEffect, useState } from "react";

import {
  fairtoyApi,
  type Finisher,
  type Supplier,
  type ToyDetail,
  type ToySummary,
} from "./api";
import { mergeSupplierRelevance } from "./view-model";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export interface FairToyData {
  finishers: Finisher[];
  finishersLoading: boolean;
  finishersError: string | null;
  toys: ToySummary[];
  toysLoading: boolean;
  toysError: string | null;
  suppliers: Supplier[];
  suppliersLoading: boolean;
  suppliersError: string | null;
  toyDetail: ToyDetail | null;
  detailLoading: boolean;
  detailError: string | null;
  updatingSupplierId: string | null;
  mutationError: string | null;
  updateSupplierFlag: (
    supplierId: string,
    childLaborFlagged: boolean,
  ) => Promise<void>;
}

export function useFairToyData(
  selectedFinisherId: string,
  selectedToyId: string,
): FairToyData {
  const [finishers, setFinishers] = useState<Finisher[]>([]);
  const [finishersLoading, setFinishersLoading] = useState(true);
  const [finishersError, setFinishersError] = useState<string | null>(null);

  const [toys, setToys] = useState<ToySummary[]>([]);
  const [toysLoading, setToysLoading] = useState(false);
  const [toysError, setToysError] = useState<string | null>(null);

  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [suppliersLoading, setSuppliersLoading] = useState(false);
  const [suppliersError, setSuppliersError] = useState<string | null>(null);

  const [toyDetail, setToyDetail] = useState<ToyDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [updatingSupplierId, setUpdatingSupplierId] = useState<string | null>(
    null,
  );
  const [mutationError, setMutationError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadFinishers() {
      setFinishersLoading(true);
      setFinishersError(null);
      try {
        const nextFinishers = await fairtoyApi.listFinishers(controller.signal);
        if (!controller.signal.aborted) {
          setFinishers(nextFinishers);
        }
      } catch (error) {
        if (!controller.signal.aborted && !isAbortError(error)) {
          setFinishersError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setFinishersLoading(false);
        }
      }
    }

    void loadFinishers();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setToys([]);
    setToysError(null);

    if (!selectedFinisherId) {
      setToysLoading(false);
      return () => controller.abort();
    }

    async function loadToys() {
      setToysLoading(true);
      try {
        const nextToys = await fairtoyApi.listToys(
          selectedFinisherId,
          controller.signal,
        );
        if (!controller.signal.aborted) {
          setToys(nextToys);
        }
      } catch (error) {
        if (!controller.signal.aborted && !isAbortError(error)) {
          setToysError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setToysLoading(false);
        }
      }
    }

    void loadToys();
    return () => controller.abort();
  }, [selectedFinisherId]);

  useEffect(() => {
    const controller = new AbortController();
    setSuppliers([]);
    setSuppliersError(null);

    async function loadSuppliers() {
      setSuppliersLoading(true);
      try {
        const globalSuppliers = await fairtoyApi.listSuppliers(
          undefined,
          controller.signal,
        );
        if (controller.signal.aborted) {
          return;
        }
        const relevantSuppliers = selectedFinisherId
          ? await fairtoyApi.listSuppliers(
              selectedFinisherId,
              controller.signal,
            )
          : null;
        if (!controller.signal.aborted) {
          setSuppliers(
            mergeSupplierRelevance(globalSuppliers, relevantSuppliers),
          );
        }
      } catch (error) {
        if (!controller.signal.aborted && !isAbortError(error)) {
          setSuppliersError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setSuppliersLoading(false);
        }
      }
    }

    void loadSuppliers();
    return () => controller.abort();
  }, [selectedFinisherId]);

  useEffect(() => {
    setMutationError(null);
  }, [selectedFinisherId, selectedToyId]);

  useEffect(() => {
    const controller = new AbortController();
    setToyDetail(null);
    setDetailError(null);

    if (!selectedFinisherId || !selectedToyId) {
      setDetailLoading(false);
      return () => controller.abort();
    }

    async function loadToyDetail() {
      setDetailLoading(true);
      try {
        const nextDetail = await fairtoyApi.getToy(
          selectedToyId,
          selectedFinisherId,
          controller.signal,
        );
        if (!controller.signal.aborted) {
          setToyDetail(nextDetail);
        }
      } catch (error) {
        if (!controller.signal.aborted && !isAbortError(error)) {
          setDetailError(errorMessage(error));
        }
      } finally {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      }
    }

    void loadToyDetail();
    return () => controller.abort();
  }, [selectedFinisherId, selectedToyId]);

  const updateSupplierFlag = useCallback(
    async (supplierId: string, childLaborFlagged: boolean) => {
      setUpdatingSupplierId(supplierId);
      setMutationError(null);
      try {
        await fairtoyApi.updateSupplierFlag(supplierId, childLaborFlagged);
        const [
          nextToys,
          nextDetail,
          globalSuppliers,
          relevantSuppliers,
        ] = await Promise.all([
          selectedFinisherId
            ? fairtoyApi.listToys(selectedFinisherId)
            : Promise.resolve<ToySummary[]>([]),
          selectedFinisherId && selectedToyId
            ? fairtoyApi.getToy(selectedToyId, selectedFinisherId)
            : Promise.resolve<ToyDetail | null>(null),
          fairtoyApi.listSuppliers(),
          selectedFinisherId
            ? fairtoyApi.listSuppliers(selectedFinisherId)
            : Promise.resolve<Supplier[] | null>(null),
        ]);
        setToys(nextToys);
        setToyDetail(nextDetail);
        setSuppliers(mergeSupplierRelevance(globalSuppliers, relevantSuppliers));
      } catch (error) {
        setMutationError(errorMessage(error));
      } finally {
        setUpdatingSupplierId(null);
      }
    },
    [selectedFinisherId, selectedToyId],
  );

  return {
    finishers,
    finishersLoading,
    finishersError,
    toys,
    toysLoading,
    toysError,
    suppliers,
    suppliersLoading,
    suppliersError,
    toyDetail,
    detailLoading,
    detailError,
    updatingSupplierId,
    mutationError,
    updateSupplierFlag,
  };
}
