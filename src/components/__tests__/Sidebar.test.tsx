import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/i18n", () => ({
  useI18n: () => ({
    t: {
      categories: {},
      modulesTitle: "Modules",
      searchModules: "Search modules",
      noModulesFound: "No modules found",
      activeScenario: "Active scenario",
    },
    isPt: false,
  }),
}));

vi.mock("@/lib/sessionRegistry", () => ({
  useSessionRegistry: () => ({ activeScenario: { name: "Base case" } }),
}));

import Sidebar from "../Sidebar";

describe("Sidebar navigation groups", () => {
  it("collapses module groups and opens the selected module's group", () => {
    const onSelectModule = vi.fn();
    const { rerender } = render(
      <Sidebar
        activeModule="dashboard"
        onSelectModule={onSelectModule}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );

    const reservoirGroup = screen.getByRole("button", {
      name: "Engenharia de Reservatório",
    });
    expect(reservoirGroup).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("button", { name: "Análise de Teste de Poço" })).not.toBeInTheDocument();

    fireEvent.click(reservoirGroup);
    expect(reservoirGroup).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("button", { name: "Análise de Teste de Poço" })).toBeInTheDocument();

    onSelectModule("economics");
    rerender(
      <Sidebar
        activeModule="economics"
        onSelectModule={onSelectModule}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Economia e Decisão" })).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("shows matches from collapsed groups while searching", () => {
    render(
      <Sidebar
        activeModule="dashboard"
        onSelectModule={vi.fn()}
        collapsed={false}
        onToggleCollapse={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByPlaceholderText("Search modules"), {
      target: { value: "PVT" },
    });
    expect(screen.getByRole("button", { name: "Cálculos PVT & Fases" })).toBeInTheDocument();
  });
});
