import { Plus, Trash2 } from "lucide-react";

export type PVTModelType = "black_oil" | "compositional";

export interface PVTModelSummary {
  id: string;
  name: string;
  type: PVTModelType;
  createdAt: string;
}

interface ModelManagerProps {
  models: PVTModelSummary[];
  selectedModelId?: string;
  onCreate: (name: string, type: PVTModelType) => void;
  onSelect: (model: PVTModelSummary) => void;
  onDelete: (modelId: string) => void;
}

export function ModelManager({
  models,
  selectedModelId,
  onCreate,
  onSelect,
  onDelete,
}: ModelManagerProps) {
  const createModel = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const name = String(form.get("model-name") ?? "").trim();
    const type = form.get("model-type");
    if (!name || (type !== "black_oil" && type !== "compositional")) return;
    onCreate(name, type);
    event.currentTarget.reset();
  };

  return (
    <section aria-labelledby="pvt-models-title" className="space-y-4">
      <h3 id="pvt-models-title" className="text-lg font-semibold">
        PVT models
      </h3>
      <form onSubmit={createModel} className="flex flex-wrap items-end gap-3">
        <label className="min-w-48 flex-1 space-y-1 text-sm">
          <span>Model name</span>
          <input
            name="model-name"
            required
            maxLength={80}
            className="w-full rounded-md border px-3 py-2"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span>Model type</span>
          <select name="model-type" defaultValue="black_oil" className="block rounded-md border px-3 py-2">
            <option value="black_oil">Black oil</option>
            <option value="compositional">Compositional</option>
          </select>
        </label>
        <button
          type="submit"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-primary-foreground"
        >
          <Plus aria-hidden="true" size={16} />
          Create model
        </button>
      </form>

      <ul className="divide-y rounded-md border">
        {models.map((model) => (
          <li key={model.id} className="flex flex-wrap items-center gap-3 p-3">
            <button
              type="button"
              aria-label={`Select ${model.name}`}
              aria-pressed={model.id === selectedModelId}
              onClick={() => onSelect(model)}
              className="min-w-0 flex-1 text-left"
            >
              <span className="block truncate font-medium">{model.name}</span>
              <span className="text-sm text-muted-foreground">
                {model.type === "black_oil" ? "Black oil" : "Compositional"} ·{" "}
                {new Date(model.createdAt).toLocaleDateString()}
              </span>
            </button>
            <button
              type="button"
              aria-label={`Delete ${model.name}`}
              onClick={() => onDelete(model.id)}
              className="rounded-md border p-2 text-red-700"
            >
              <Trash2 aria-hidden="true" size={16} />
            </button>
          </li>
        ))}
        {models.length === 0 && (
          <li className="p-4 text-center text-sm text-muted-foreground">
            No saved PVT models.
          </li>
        )}
      </ul>
    </section>
  );
}
