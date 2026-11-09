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
import {
  PVTInputForm,
  type PVTFormValues,
} from "../pvt/PVTInputForm";
import {
  formatPVTResultsCsv,
  PVTResults,
  type PVTTableRow,
} from "../pvt/PVTResults";
import {
  deletePVTModel,
  getSavedPVTModels,
  PVT_MODELS_STORAGE_KEY,
  savePVTModel,
} from "@/lib/pvt/service";
import type { SavedPVTModel } from "@/lib/pvt/types";
import PVTAnalysisWorkflow from "../PVTAnalysisWorkflow";

vi.mock("../PVTCalculator", () => ({
  default: () => <div>Current PVT calculation view</div>,
}));

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

  it("test_pvt_input_form_workflow validates and submits table ranges", () => {
    const values: PVTFormValues = {
      pressure: 3200,
      temperature: 180,
      gasGravity: 0.72,
      apiGravity: 34.5,
      gor: 650,
    };
    const onChange = vi.fn();
    const onGenerateTable = vi.fn();
    render(
      <PVTInputForm
        values={values}
        pressureUnit="psia"
        temperatureUnit="°F"
        canGenerateTable
        generatedRowCount={0}
        onChange={onChange}
        onGenerateTable={onGenerateTable}
      />,
    );

    fireEvent.change(screen.getByLabelText("Gas specific gravity (air = 1.0)"), {
      target: { value: "0.8" },
    });
    expect(onChange).toHaveBeenCalledWith("gasGravity", 0.8);

    fireEvent.change(screen.getByLabelText("Pressure step"), {
      target: { value: "0" },
    });
    expect(
      screen.getByRole("button", { name: "Generate 0 table points" }),
    ).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Pressure step"), {
      target: { value: "500" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Generate 12 table points" }),
    );
    expect(onGenerateTable).toHaveBeenCalledWith({
      start: 500,
      end: 6000,
      step: 500,
    });
  });

  it("test_pvt_results_export renders rows and exports property values", () => {
    const rows: PVTTableRow[] = [
      {
        pressure: 1000,
        temperature: 180,
        results: {
          zFactor: 0.9,
          bg: 0.01,
          bo: 1.2,
          rs: 300,
          pb: 2500,
          oilViscosity: 2.5,
          gasViscosity: 0.02,
          oilDensity: 50,
        },
      },
    ];
    const onExportCsv = vi.fn();

    render(<PVTResults rows={rows} onExportCsv={onExportCsv} />);
    expect(screen.getByText("1000.00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Export CSV" }));

    const csv = formatPVTResultsCsv(rows);
    expect(onExportCsv).toHaveBeenCalledWith(csv);
    expect(csv).toContain("Pressure (psia),Temperature (°F),Z-factor");
    expect(csv).toContain("1000.000000,180.0000000,0.9000000000");
  });

  it("test_pvt_service_calls persists, updates, and deletes models", () => {
    const model: SavedPVTModel = {
      id: "model-1",
      name: "Reservoir fluid",
      type: "compositional",
      createdAt: "2026-01-01T00:00:00.000Z",
      components: [methane],
    };

    expect(savePVTModel(model)).toEqual([model]);
    expect(getSavedPVTModels()).toEqual([model]);
    expect(
      savePVTModel({ ...model, name: "Updated fluid" }),
    ).toEqual([{ ...model, name: "Updated fluid" }]);
    expect(deletePVTModel(model.id)).toBe(true);
    expect(deletePVTModel(model.id)).toBe(false);
    expect(getSavedPVTModels()).toEqual([]);
  });

  it("test_pvt_service_rejects_malformed_storage", () => {
    window.localStorage.setItem(PVT_MODELS_STORAGE_KEY, "{");

    expect(() => getSavedPVTModels()).toThrow(
      "Saved PVT models contain invalid JSON.",
    );
  });

  it("test_pvt_analysis_workflow joins calculation, models, and composition", () => {
    window.localStorage.clear();
    render(<PVTAnalysisWorkflow />);
    expect(screen.getByText("Current PVT calculation view")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Models" }));
    fireEvent.change(screen.getByLabelText("Model name"), {
      target: { value: "Reservoir fluid" },
    });
    fireEvent.change(screen.getByLabelText("Model type"), {
      target: { value: "compositional" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create model" }));
    expect(screen.getByText("Reservoir fluid")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Composition" }));
    fireEvent.click(screen.getByRole("button", { name: "Add component" }));
    fireEvent.change(screen.getByLabelText("Mole fraction 1"), {
      target: { value: "1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save composition" }));

    expect(getSavedPVTModels()[0].components[0].moleFraction).toBe(1);
  });
});
