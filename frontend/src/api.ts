export type ImpactStatus =
  | "unaffected"
  | "potentially_affected"
  | "affected";

export type ImpactReasonCode =
  | "toy_unaffected"
  | "toy_potentially_affected"
  | "toy_affected"
  | "part_no_known_sources"
  | "part_no_flagged_sources"
  | "part_all_sources_flagged"
  | "part_mixed_source_flags";

export interface Finisher {
  finisher_id: string;
  finisher_name: string;
  hq_country: string | null;
}

export interface Supplier {
  supplier_id: string;
  supplier_name: string;
  hq_country: string | null;
  child_labor_flagged: boolean;
  flagged_at: string | null;
}

export interface ImpactPath {
  supplier_id: string;
  supplier_name: string;
  supplier_flagged: boolean;
  factory_id: string;
  factory_name: string;
  unit_cost_usd: string | null;
}

export interface PartImpact {
  part_id: string;
  part_name: string;
  quantity: number;
  status: ImpactStatus;
  reason_code: ImpactReasonCode;
  reason: string;
  paths: ImpactPath[];
}

export interface ToySummary {
  finisher_id: string;
  toy_id: string;
  toy_name: string;
  status: ImpactStatus;
  reason_code: ImpactReasonCode;
  reason: string;
}

export interface ToyDetail extends ToySummary {
  parts: PartImpact[];
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = undefined;
    }
    throw new ApiError(
      describeApiError(payload, response.statusText),
      response.status,
    );
  }

  return (await response.json()) as T;
}

function describeApiError(payload: unknown, fallback: string): string {
  if (typeof payload !== "object" || payload === null || !("detail" in payload)) {
    return fallback || "The request failed.";
  }

  const detail = payload.detail;
  return typeof detail === "string"
    ? detail
    : JSON.stringify(detail) || "The request failed.";
}

function toyQuery(finisherId: string): string {
  const params = new URLSearchParams({ finisher_id: finisherId });
  return `/api/toys?${params.toString()}`;
}

export const fairtoyApi = {
  listFinishers(signal?: AbortSignal): Promise<Finisher[]> {
    return request<Finisher[]>("/api/finishers", { signal });
  },

  listSuppliers(signal?: AbortSignal): Promise<Supplier[]> {
    return request<Supplier[]>("/api/suppliers", { signal });
  },

  listToys(finisherId: string, signal?: AbortSignal): Promise<ToySummary[]> {
    return request<ToySummary[]>(toyQuery(finisherId), { signal });
  },

  getToy(
    toyId: string,
    finisherId: string,
    signal?: AbortSignal,
  ): Promise<ToyDetail> {
    const params = new URLSearchParams({ finisher_id: finisherId });
    return request<ToyDetail>(
      `/api/toys/${encodeURIComponent(toyId)}?${params.toString()}`,
      { signal },
    );
  },

  updateSupplierFlag(
    supplierId: string,
    childLaborFlagged: boolean,
    signal?: AbortSignal,
  ): Promise<Supplier> {
    return request<Supplier>(
      `/api/suppliers/${encodeURIComponent(supplierId)}`,
      {
        method: "PATCH",
        body: JSON.stringify({ child_labor_flagged: childLaborFlagged }),
        signal,
      },
    );
  },
};
