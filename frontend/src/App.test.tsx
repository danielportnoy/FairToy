import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const finisher = {
  finisher_id: "FIN-1",
  finisher_name: "Northstar Finisher",
  hq_country: "Denmark",
};

const toy = {
  finisher_id: "FIN-1",
  toy_id: "TOY-1",
  toy_name: "Copper Camp",
  status: "unaffected" as const,
  reason_code: "toy_unaffected" as const,
  reason: "No required part is affected or potentially affected.",
};

function detail(flagged: boolean) {
  return {
    ...toy,
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
  it("loads a Toy detail and refreshes it after flagging a Supplier", async () => {
    let flagged = false;
    let patchBody: unknown;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const path = String(input);
      if (path === "/api/finishers") {
        return jsonResponse([finisher]);
      }
      if (path === "/api/toys?finisher_id=FIN-1") {
        return jsonResponse([toy]);
      }
      if (path === "/api/toys/TOY-1?finisher_id=FIN-1") {
        return jsonResponse(detail(flagged));
      }
      if (path === "/api/suppliers/SUP-1" && init?.method === "PATCH") {
        patchBody = JSON.parse(String(init.body));
        flagged = true;
        return jsonResponse({
          supplier_id: "SUP-1",
          supplier_name: "Supplier One",
          hq_country: null,
          child_labor_flagged: true,
          flagged_at: "2026-10-15T12:00:00Z",
        });
      }
      throw new Error(`Unexpected request: ${path}`);
    });

    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", { name: /Copper Camp/ }),
    );
    expect(await screen.findByRole("heading", { name: "Copper Camp" })).toBeTruthy();
    expect(screen.getByText("Supplier One")).toBeTruthy();

    fireEvent.click(await screen.findByRole("button", { name: "Flag supplier" }));

    expect(
      await screen.findByRole("button", { name: "Unflag supplier" }),
    ).toBeTruthy();
    expect(patchBody).toEqual({ child_labor_flagged: true });
    expect(screen.getByText("Flagged for child labor")).toBeTruthy();
  });
});
