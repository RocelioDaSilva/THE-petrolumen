import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  vogel: vi.fn(),
  vogelCurve: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  vogel: mocks.vogel,
  vogelCurve: mocks.vogelCurve,
}));

vi.mock("recharts", () => ({
  CartesianGrid: () => null,
  Legend: () => null,
  Line: () => null,
  LineChart: () => null,
  ResponsiveContainer: () => null,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));

import NodalAnalysisView from "../NodalAnalysisView";

describe("NodalAnalysisView", () => {
  beforeEach(() => {
    mocks.vogel.mockReset().mockResolvedValue({ q: 900 });
    mocks.vogelCurve.mockReset().mockRejectedValue(new Error("API unavailable"));
  });

  it("labels the local fallback when the backend IPR request fails", async () => {
    render(<NodalAnalysisView />);

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        "Backend unavailable. Displaying a local Vogel fallback.",
      );
    });
  });
});
