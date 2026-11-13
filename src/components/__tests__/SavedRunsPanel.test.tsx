import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  fetchSavedSimulation: vi.fn(),
  fetchSavedSimulations: vi.fn(),
  removeSavedSimulation: vi.fn(),
  authState: {
    user: {
      id: 4,
      username: "engineer",
      email: "engineer@example.com",
      full_name: null,
      role: "user",
      is_active: true,
    } as null | {
      id: number;
      username: string;
      email: string;
      full_name: string | null;
      role: string;
      is_active: boolean;
    },
    openAuthDialog: vi.fn(),
  },
}));

vi.mock("@/lib/api", () => ({
  fetchSavedSimulation: mocks.fetchSavedSimulation,
  fetchSavedSimulations: mocks.fetchSavedSimulations,
  removeSavedSimulation: mocks.removeSavedSimulation,
}));

vi.mock("@/lib/authContext", () => ({
  useAuth: () => ({
    user: mocks.authState.user,
    openAuthDialog: mocks.authState.openAuthDialog,
  }),
}));

import SavedRunsPanel from "../SavedRunsPanel";

const summary = {
  id: 12,
  name: "Volve base run",
  simulation_type: "reservoir-simulation",
  created_at: "2026-11-12T10:00:00Z",
};

const run = {
  ...summary,
  input_data: { nx: 10 },
  result_data: { finalPressure: 2800 },
};

describe("SavedRunsPanel", () => {
  beforeEach(() => {
    mocks.authState.user = {
      id: 4,
      username: "engineer",
      email: "engineer@example.com",
      full_name: null,
      role: "user",
      is_active: true,
    };
    mocks.fetchSavedSimulations.mockReset().mockResolvedValue([summary]);
    mocks.fetchSavedSimulation.mockReset().mockResolvedValue(run);
    mocks.removeSavedSimulation.mockReset().mockResolvedValue(undefined);
    mocks.authState.openAuthDialog.mockReset();
  });

  it("loads the full saved run for the selected item", async () => {
    const onLoad = vi.fn().mockReturnValue(true);
    render(<SavedRunsPanel onLoad={onLoad} />);

    fireEvent.click(await screen.findByRole("button", { name: "Load" }));

    await waitFor(() => expect(onLoad).toHaveBeenCalledWith(run));
    expect(mocks.fetchSavedSimulation).toHaveBeenCalledWith(12);
  });

  it("compares exactly two selected reservoir runs", async () => {
    const secondSummary = { ...summary, id: 13, name: "Volve low case" };
    const thirdSummary = { ...summary, id: 14, name: "Volve high case" };
    const secondRun = { ...run, ...secondSummary };
    const thirdRun = { ...run, ...thirdSummary };
    mocks.fetchSavedSimulations.mockResolvedValue([summary, secondSummary, thirdSummary]);
    mocks.fetchSavedSimulation.mockImplementation((id: number) =>
      Promise.resolve(id === 13 ? secondRun : id === 14 ? thirdRun : run),
    );
    const onCompare = vi.fn();
    render(<SavedRunsPanel onLoad={vi.fn()} onCompare={onCompare} />);

    fireEvent.click(await screen.findByRole("checkbox", { name: "Select Volve base run for comparison" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Select Volve low case for comparison" }));

    expect(screen.getByRole("checkbox", { name: "Select Volve high case for comparison" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Compare selected" }));

    await waitFor(() => expect(onCompare).toHaveBeenCalledWith([run, secondRun]));
    expect(mocks.fetchSavedSimulation).toHaveBeenCalledWith(12);
    expect(mocks.fetchSavedSimulation).toHaveBeenCalledWith(13);
    expect(mocks.fetchSavedSimulation).not.toHaveBeenCalledWith(14);
  });

  it("deletes a saved run and removes it from the list", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<SavedRunsPanel onLoad={vi.fn()} />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete Volve base run" }));

    await waitFor(() => expect(mocks.removeSavedSimulation).toHaveBeenCalledWith(12));
    expect(screen.queryByText("Volve base run")).not.toBeInTheDocument();
    vi.restoreAllMocks();
  });

  it("prompts signed-out users to authenticate", () => {
    mocks.authState.user = null;
    render(<SavedRunsPanel onLoad={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(mocks.authState.openAuthDialog).toHaveBeenCalledOnce();
    expect(mocks.fetchSavedSimulations).not.toHaveBeenCalled();
  });
});
