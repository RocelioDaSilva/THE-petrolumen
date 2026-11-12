import type { ReactNode } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SessionRegistryProvider } from "@/lib/sessionRegistry";
import ReservoirSimulationView from "../ReservoirSimulationView";

vi.mock("recharts", async (importOriginal) => {
  const actual = await importOriginal<typeof import("recharts")>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  };
});

function renderSimulation() {
  return render(
    <SessionRegistryProvider>
      <ReservoirSimulationView />
    </SessionRegistryProvider>,
  );
}

describe("ReservoirSimulationView workspace", () => {
  afterEach(() => {
    vi.useRealTimers();
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
});
