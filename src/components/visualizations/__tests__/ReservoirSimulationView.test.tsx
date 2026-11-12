import type { ComponentProps, ReactNode } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SessionRegistryProvider } from "@/lib/sessionRegistry";
import ReservoirSimulationView from "../ReservoirSimulationView";
import { I18nProvider } from "@/lib/i18n";

const mocks = vi.hoisted(() => ({
  createSavedSimulation: vi.fn(),
  auth: {
    user: null as null | { id: number; username: string },
    openAuthDialog: vi.fn(),
  },
}));

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  };
});

vi.mock("@/lib/api", () => ({
  createSavedSimulation: mocks.createSavedSimulation,
}));

vi.mock("@/lib/authContext", () => ({
  useAuth: () => mocks.auth,
}));

function renderSimulation(savedRun?: ComponentProps<typeof ReservoirSimulationView>["savedRun"]) {
  return render(
    <I18nProvider>
      <SessionRegistryProvider>
        <ReservoirSimulationView savedRun={savedRun} />
      </SessionRegistryProvider>
    </I18nProvider>,
  );
}

describe("ReservoirSimulationView workspace", () => {
  afterEach(() => {
    vi.useRealTimers();
    mocks.auth.user = null;
    mocks.createSavedSimulation.mockReset().mockResolvedValue({});
  });

  it("starts with an empty result state and collapsed advanced parameters", () => {
    renderSimulation();

    expect(screen.getByText("Resultados aguardando simulação")).toBeInTheDocument();
    expect(screen.getByText("Parâmetros avançados").closest("details")?.open).toBe(false);
  });

  it("shows a loading state then displays the simulation results", async () => {
    vi.useFakeTimers();
    renderSimulation();

    fireEvent.click(screen.getByRole("button", { name: "Executar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Calculando a resposta do reservatório");

    await act(async () => {
      vi.advanceTimersByTime(350);
    });

    expect(screen.getByText("Evolução de pressão")).toBeInTheDocument();
    expect(screen.getByText("Perfil espacial de pressão")).toBeInTheDocument();
  });

  it("loads saved model inputs into the simulation controls", () => {
    renderSimulation({
      id: 33,
      name: "Saved case",
      simulation_type: "reservoir-simulation",
      created_at: "2026-11-12T10:00:00Z",
      input_data: {
        nx: 14,
        dx: 160,
        permeability: 90,
        porosity: 0.18,
        viscosity: 2,
        pi: 4200,
        dt: 5,
        nSteps: 30,
        wellRate: -800,
      },
      result_data: {},
    });

    expect(screen.getByLabelText("Blocos (nx)")).toHaveValue(14);
    expect(screen.getByLabelText("Permeabilidade (mD)")).toHaveValue(90);
    expect(screen.getByText("Loaded saved run: Saved case")).toBeInTheDocument();
    expect(screen.getByText("Evolução de pressão")).toBeInTheDocument();
  });

  it("saves a completed run to the authenticated account", async () => {
    vi.useFakeTimers();
    mocks.auth.user = { id: 3, username: "engineer" };
    mocks.createSavedSimulation.mockResolvedValue({
      id: 41,
      name: "Saved simulation",
      simulation_type: "reservoir-simulation",
      created_at: "2026-11-12T10:00:00Z",
      input_data: {},
      result_data: {},
    });
    renderSimulation();

    fireEvent.click(screen.getByRole("button", { name: "Executar" }));
    await act(async () => {
      vi.advanceTimersByTime(350);
    });
    fireEvent.click(screen.getByRole("button", { name: "Save run" }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(mocks.createSavedSimulation).toHaveBeenCalledWith(
      expect.objectContaining({ simulation_type: "reservoir-simulation" }),
    );
    expect(screen.getByRole("status")).toHaveTextContent("Run saved.");
  });
});
