import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const finisher = {
  finisher_id: "FIN-1",
  finisher_name: "Northstar Finisher",
  hq_country: "Denmark",
};

const unaffectedToy = {
  finisher_id: "FIN-1",
  toy_id: "TOY-1",
  toy_name: "Copper Camp",
  status: "unaffected" as const,
  reason_code: "toy_unaffected" as const,
  reason: "No required part is affected or potentially affected.",
};

const attentionToy = {
  finisher_id: "FIN-1",
  toy_id: "TOY-2",
  toy_name: "Affected Camp",
  status: "affected" as const,
  reason_code: "toy_affected" as const,
  reason: "At least one required Part is affected.",
};

const potentiallyAffectedToy = {
  finisher_id: "FIN-1",
  toy_id: "TOY-3",
  toy_name: "Potential Camp",
  status: "potentially_affected" as const,
  reason_code: "toy_potentially_affected" as const,
  reason: "At least one required Part is potentially affected.",
};

const inventoryToys = [
  attentionToy,
  potentiallyAffectedToy,
  unaffectedToy,
  ...Array.from({ length: 9 }, (_, index) => ({
    ...unaffectedToy,
    toy_id: `TOY-${index + 4}`,
    toy_name: `Inventory Camp ${index + 1}`,
  })),
];

function detail(flagged: boolean) {
  return {
    ...attentionToy,
    parts: [
      {
        part_id: "PRT-1",
        part_name: "Canvas tent",
        quantity: 2,
        status: flagged ? ("affected" as const) : ("unaffected" as const),
        reason_code: flagged
          ? ("part_all_sources_flagged" as const)
          : ("part_no_flagged_sources" as const),
        reason: flagged
          ? "All known possible sources are flagged."
          : "No possible source is flagged.",
        paths: [
          {
            supplier_id: "SUP-1",
            supplier_name: "Supplier One",
            supplier_flagged: flagged,
            factory_id: "FAC-1",
            factory_name: "Factory One",
            unit_cost_usd: "4.50",
          },
        ],
      },
    ],
  };
}

function supplier(flagged: boolean) {
  return {
    supplier_id: "SUP-1",
    supplier_name: "Supplier One",
    hq_country: null,
    child_labor_flagged: flagged,
    flagged_at: flagged ? "2026-10-15T12:00:00Z" : null,
    related_toy_count: 2,
  };
}

function jsonResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("FairToy dashboard", () => {
  it("uses one Toys list with status filtering and client pagination", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input) => {
        const path = String(input);
        if (path === "/api/finishers") {
          return jsonResponse([finisher]);
        }
        if (path === "/api/toys?finisher_id=FIN-1") {
          return jsonResponse(inventoryToys);
        }
        if (path === "/api/suppliers") {
          return jsonResponse([supplier(false)]);
        }
        if (path === "/api/suppliers?finisher_id=FIN-1") {
          return jsonResponse([supplier(false)]);
        }
        throw new Error(`Unexpected request: ${path}`);
      });

    render(<App />);

    expect(
      screen.getByRole("heading", { name: "Choose a Finisher" }),
    ).toBeTruthy();
    fireEvent.change(await screen.findByLabelText("Finisher"), {
      target: { value: "FIN-1" },
    });

    expect(
      await screen.findByRole("heading", { name: "Toys" }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: /Affected Camp/ })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: /Potential Camp/ }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: /Copper Camp/ })).toBeTruthy();
    expect(
      screen.queryByRole("option", { name: "Needs attention" }),
    ).toBeNull();
    expect(screen.getByText("Showing 1–10 of 12")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "affected" },
    });
    expect(await screen.findByRole("button", { name: /Affected Camp/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Potential Camp/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Copper Camp/ })).toBeNull();

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "all" },
    });
    expect(await screen.findByRole("button", { name: /Copper Camp/ })).toBeTruthy();
    expect(screen.getByText("Showing 1–10 of 12")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("Page 2 of 2")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Inventory Camp 9/ })).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Search Toys"), {
      target: { value: "Copper" },
    });
    expect(await screen.findByRole("button", { name: /Copper Camp/ })).toBeTruthy();
    expect(screen.getByText("Showing 1–1 of 1")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/suppliers?finisher_id=FIN-1",
      expect.objectContaining({ headers: expect.any(Headers) }),
    );
  });

  it("opens global Supplier Review without a Finisher and confirms mutations", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(async (input) => {
        const path = String(input);
        if (path === "/api/finishers") {
          return jsonResponse([finisher]);
        }
        if (path === "/api/suppliers") {
          return jsonResponse([supplier(false)]);
        }
        throw new Error(`Unexpected request: ${path}`);
      });
    const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(false);

    render(<App />);
    fireEvent.click(
      await screen.findByRole("button", { name: /^Suppliers/ }),
    );

    expect(
      await screen.findByRole("heading", { name: "Supplier Review" }),
    ).toBeTruthy();
    expect(
      screen.queryByRole("heading", { name: "Choose a Finisher to begin." }),
    ).toBeNull();
    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === "SPAN" &&
          element.textContent?.includes("Global Supplier") === true,
      ),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Flag supplier" }));

    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining("flag Supplier One globally"),
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("explains when a flagged Supplier has no current impact for the Finisher", async () => {
    const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(false);

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const path = String(input);
      if (path === "/api/finishers") {
        return jsonResponse([finisher]);
      }
      if (path === "/api/toys?finisher_id=FIN-1") {
        return jsonResponse([]);
      }
      if (path === "/api/suppliers") {
        return jsonResponse([supplier(true)]);
      }
      if (path === "/api/suppliers?finisher_id=FIN-1") {
        return jsonResponse([]);
      }
      throw new Error(`Unexpected request: ${path}`);
    });

    render(<App />);
    fireEvent.change(await screen.findByLabelText("Finisher"), {
      target: { value: "FIN-1" },
    });
    fireEvent.click(
      await screen.findByRole("button", { name: /^Suppliers/ }),
    );

    expect(
      await screen.findByText(/no current Toy impact for this Finisher/),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Unflag supplier" }));

    expect(confirmMock).toHaveBeenCalledWith(
      expect.stringContaining("no current Toy impact for Northstar Finisher"),
    );
  });

  it("loads a Toy detail and refreshes it after flagging a Supplier", async () => {
    let flagged = false;
    let patchBody: unknown;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === "/api/finishers") {
        return jsonResponse([finisher]);
      }
      if (path === "/api/toys?finisher_id=FIN-1") {
        return jsonResponse([attentionToy]);
      }
      if (path === "/api/suppliers") {
        return jsonResponse([supplier(flagged)]);
      }
      if (path === "/api/suppliers?finisher_id=FIN-1") {
        return jsonResponse([supplier(flagged)]);
      }
      if (path === "/api/toys/TOY-2?finisher_id=FIN-1") {
        return jsonResponse(detail(flagged));
      }
      if (path === "/api/suppliers/SUP-1" && init?.method === "PATCH") {
        patchBody = JSON.parse(String(init.body));
        flagged = true;
        return jsonResponse(supplier(true));
      }
      throw new Error(`Unexpected request: ${path}`);
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<App />);
    fireEvent.change(await screen.findByLabelText("Finisher"), {
      target: { value: "FIN-1" },
    });
    fireEvent.click(
      await screen.findByRole("button", { name: /Affected Camp/ }),
    );

    expect(
      await screen.findByRole("heading", { name: "Trace the evidence path" }),
    ).toBeTruthy();
    expect(screen.getByText("Supplier One")).toBeTruthy();
    expect(screen.queryByText("toy_affected")).toBeNull();

    fireEvent.click(await screen.findByRole("button", { name: "Flag supplier" }));

    expect(
      await screen.findByRole("button", { name: "Unflag supplier" }),
    ).toBeTruthy();
    expect(patchBody).toEqual({ child_labor_flagged: true });
    expect(screen.getByText("Flagged for child labor")).toBeTruthy();
  });
});
