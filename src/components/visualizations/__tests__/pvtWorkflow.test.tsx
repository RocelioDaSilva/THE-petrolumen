import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterAll, describe, expect, it, vi } from "vitest";
import {
  FluidCompositionEditor,
  type PVTComponent,
} from "../pvt/FluidCompositionEditor";
import {
  ModelManager,
  type PVTModelSummary,
} from "../pvt/ModelManager";
import {
  PhaseEnvelope,
  type PhaseEnvelopePoint,
} from "../pvt/PhaseEnvelope";

vi.stubGlobal(
  "ResizeObserver",
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
  },
);

afterAll(() => vi.unstubAllGlobals());

const methane: PVTComponent = {
  name: "Methane",
  molecularWeight: 16.04,
  criticalPressure: 667.8,
  criticalTemperature: 343,
  acentricFactor: 0.011,
  criticalVolume: 0.099,
  parachor: 77,
  moleFraction: 0.5,
};

describe("PVT workflow", () => {
  it("test_pvt_fluid_composition_editor adds, normalizes, and saves valid components", () => {
    const onSave = vi.fn();
    function StatefulEditor() {
      const [composition, setComposition] = useState([
        { ...methane, moleFraction: 0.25 },
      ]);
      return (
        <FluidCompositionEditor
          composition={composition}
          onChange={setComposition}
          onSave={onSave}
        />
      );
    }

    render(
      <StatefulEditor />,
    );

    expect(screen.getByRole("button", { name: "Save composition" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Add component" }));
    fireEvent.change(screen.getByLabelText("Mole fraction 2"), {
      target: { value: "0.25" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Normalize" }));
    expect(screen.getByLabelText("Mole fraction 1")).toHaveValue(0.5);
    expect(screen.getByLabelText("Mole fraction 2")).toHaveValue(0.5);
    fireEvent.click(screen.getByRole("button", { name: "Save composition" }));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("test_pvt_model_manager creates, selects, and deletes models", () => {
    const model: PVTModelSummary = {
      id: "model-1",
      name: "Reservoir fluid",
      type: "black_oil",
      createdAt: "2026-01-01T00:00:00.000Z",
    };
    const onCreate = vi.fn();
    const onSelect = vi.fn();
    const onDelete = vi.fn();
    render(
      <ModelManager
        models={[model]}
        selectedModelId={model.id}
        onCreate={onCreate}
        onSelect={onSelect}
        onDelete={onDelete}
      />,
    );

    fireEvent.change(screen.getByLabelText("Model name"), {
      target: { value: "New model" },
    });
    fireEvent.change(screen.getByLabelText("Model type"), {
      target: { value: "compositional" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create model" }));
    expect(onCreate).toHaveBeenCalledWith("New model", "compositional");

    fireEvent.click(
      screen.getByRole("button", { name: "Select Reservoir fluid" }),
    );
    expect(onSelect).toHaveBeenCalledWith(model);
    fireEvent.click(screen.getByRole("button", { name: "Delete Reservoir fluid" }));
    expect(onDelete).toHaveBeenCalledWith(model.id);
  });

  it("test_pvt_phase_envelope identifies critical and limiting points", () => {
    const points: PhaseEnvelopePoint[] = [
      { temperature: 100, pressure: 900, type: "bubble" },
      { temperature: 200, pressure: 1200, type: "bubble" },
      { temperature: 250, pressure: 1100, type: "dew" },
      { temperature: 220, pressure: 1150, type: "critical" },
    ];

    render(
      <PhaseEnvelope
        points={points}
        temperatureUnit="°F"
        pressureUnit="psia"
      />,
    );

    expect(screen.getByText("Cricondentherm")).toBeInTheDocument();
    expect(screen.getByText("250.0 °F")).toBeInTheDocument();
    expect(screen.getByText("Cricondenbar")).toBeInTheDocument();
    expect(screen.getByText("1200.0 psia")).toBeInTheDocument();
    expect(screen.getByText("220.0 °F, 1150.0 psia")).toBeInTheDocument();
  });
});
