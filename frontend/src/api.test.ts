import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, fairtoyApi } from "./api";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("fairtoyApi", () => {
  it("encodes Finisher filters and returns Toy summaries", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await expect(fairtoyApi.listToys("FIN 001")).resolves.toEqual([]);

    const [input, init] = fetchMock.mock.calls[0] ?? [];
    expect(input).toBe("/api/toys?finisher_id=FIN+001");
    expect(new Headers(init?.headers).get("Accept")).toBe("application/json");
  });

  it("encodes Finisher filters for Supplier review", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await expect(fairtoyApi.listSuppliers("FIN 001")).resolves.toEqual([]);

    const [input] = fetchMock.mock.calls[0] ?? [];
    expect(input).toBe("/api/suppliers?finisher_id=FIN+001");
  });

  it("uses the global Supplier collection without a Finisher", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse([]));

    await expect(fairtoyApi.listSuppliers()).resolves.toEqual([]);

    const [input] = fetchMock.mock.calls[0] ?? [];
    expect(input).toBe("/api/suppliers");
  });

  it("loads focused Supplier detail", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({}));

    await expect(fairtoyApi.getSupplier("SUP/1")).resolves.toEqual({});

    const [input] = fetchMock.mock.calls[0] ?? [];
    expect(input).toBe("/api/suppliers/SUP%2F1");
  });

  it("sends an explicit Supplier flag state", async () => {
    const supplier = {
      supplier_id: "SUP/1",
      supplier_name: "Supplier One",
      hq_country: null,
      child_labor_flagged: true,
      flagged_at: "2026-10-15T12:00:00Z",
    };
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(supplier));

    await expect(
      fairtoyApi.updateSupplierFlag("SUP/1", true),
    ).resolves.toEqual(supplier);

    const [input, init] = fetchMock.mock.calls[0] ?? [];
    expect(input).toBe("/api/suppliers/SUP%2F1");
    expect(init?.method).toBe("PATCH");
    expect(init?.body).toBe(JSON.stringify({ child_labor_flagged: true }));
    expect(new Headers(init?.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });

  it("maps API error details to ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "Finisher not found" }, 404),
    );

    await expect(fairtoyApi.listFinishers()).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      message: "Finisher not found",
    } satisfies Partial<ApiError>);
  });
});
