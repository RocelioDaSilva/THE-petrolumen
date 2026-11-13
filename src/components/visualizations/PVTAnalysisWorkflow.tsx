import { useEffect, useState } from "react";
import { FluidCompositionEditor } from "./pvt/FluidCompositionEditor";
import { ModelManager } from "./pvt/ModelManager";
import PVTCalculator from "./PVTCalculator";
import PvtEosFlashView from "./PvtEosFlashView";
import {
  deletePVTModel,
  getSavedPVTModels,
  savePVTModel,
} from "@/lib/pvt/service";
import type {
  PVTComponent,
  PVTModelSummary,
  PVTModelType,
  SavedPVTModel,
} from "@/lib/pvt/types";

type WorkflowTab = "calculation" | "eos-flash" | "composition" | "models";

const tabs: Array<{ id: WorkflowTab; label: string }> = [
  { id: "calculation", label: "Calculation" },
  { id: "eos-flash", label: "EOS & Flash" },
  { id: "composition", label: "Composition" },
  { id: "models", label: "Models" },
];

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export default function PVTAnalysisWorkflow() {
  const [activeTab, setActiveTab] = useState<WorkflowTab>("calculation");
  const [models, setModels] = useState<SavedPVTModel[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>();
  const [composition, setComposition] = useState<PVTComponent[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    try {
      const savedModels = getSavedPVTModels();
      setModels(savedModels);
      setSelectedModelId(savedModels[0]?.id);
      setComposition(savedModels[0]?.components ?? []);
    } catch (loadError) {
      setError(errorMessage(loadError));
    }
  }, []);

  const selectedModel = models.find((model) => model.id === selectedModelId);

  const createModel = (name: string, type: PVTModelType) => {
    try {
      const model: SavedPVTModel = {
        id: crypto.randomUUID(),
        name,
        type,
        createdAt: new Date().toISOString(),
        components: [],
      };
      setModels(savePVTModel(model));
      setSelectedModelId(model.id);
      setComposition(model.components);
      setError(undefined);
    } catch (saveError) {
      setError(errorMessage(saveError));
    }
  };

  const selectModel = (model: PVTModelSummary) => {
    const savedModel = models.find((candidate) => candidate.id === model.id);
    if (!savedModel) {
      setError(`PVT model "${model.name}" is no longer available.`);
      return;
    }
    setSelectedModelId(savedModel.id);
    setComposition(savedModel.components);
    setError(undefined);
  };

  const removeModel = (modelId: string) => {
    try {
      if (!deletePVTModel(modelId)) {
        throw new Error(`PVT model "${modelId}" is no longer available.`);
      }
      const remaining = getSavedPVTModels();
      setModels(remaining);
      if (selectedModelId === modelId) {
        setSelectedModelId(remaining[0]?.id);
        setComposition(remaining[0]?.components ?? []);
      }
      setError(undefined);
    } catch (deleteError) {
      setError(errorMessage(deleteError));
    }
  };

  const saveComposition = () => {
    if (!selectedModel) {
      setError("Create or select a model before saving its composition.");
      return;
    }
    if (selectedModel.type !== "compositional") {
      setError("Fluid composition can only be saved to a compositional model.");
      return;
    }
    try {
      setModels(savePVTModel({ ...selectedModel, components: composition }));
      setError(undefined);
    } catch (saveError) {
      setError(errorMessage(saveError));
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">PVT Analysis</h1>
        <p className="text-sm text-muted-foreground">
          Calculate fluid properties, edit compositions, and manage saved models.
        </p>
      </header>

      <div role="tablist" aria-label="PVT analysis workflow" className="flex gap-2 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`pvt-tab-${tab.id}`}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls="pvt-workflow-panel"
            onClick={() => setActiveTab(tab.id)}
            className="border-b-2 px-4 py-2 text-sm aria-selected:border-primary aria-selected:font-semibold"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}

      <section
        id="pvt-workflow-panel"
        role="tabpanel"
        aria-labelledby={`pvt-tab-${activeTab}`}
      >
        {activeTab === "calculation" && <PVTCalculator />}
        {activeTab === "eos-flash" && <PvtEosFlashView />}
        {activeTab === "composition" && (
          <div className="space-y-4">
            {!selectedModel && (
              <p className="text-sm text-muted-foreground">
                Create a compositional model on the Models tab to save a fluid composition.
              </p>
            )}
            {selectedModel && selectedModel.type !== "compositional" && (
              <p className="text-sm text-muted-foreground">
                Select a compositional model to edit its fluid composition.
              </p>
            )}
            <FluidCompositionEditor
              composition={composition}
              onChange={setComposition}
              onSave={saveComposition}
            />
          </div>
        )}
        {activeTab === "models" && (
          <ModelManager
            models={models}
            selectedModelId={selectedModelId}
            onCreate={createModel}
            onSelect={selectModel}
            onDelete={removeModel}
          />
        )}
      </section>
    </div>
  );
}
