import { Plus, Trash2 } from "lucide-react";

export interface PVTComponent {
  name: string;
  molecularWeight: number;
  criticalPressure: number;
  criticalTemperature: number;
  acentricFactor: number;
  criticalVolume: number;
  parachor: number;
  moleFraction: number;
}

interface FluidCompositionEditorProps {
  composition: PVTComponent[];
  onChange: (composition: PVTComponent[]) => void;
  onSave: () => void;
}

const numericFields: Array<{
  key: Exclude<keyof PVTComponent, "name">;
  label: string;
}> = [
  { key: "moleFraction", label: "Mole fraction" },
  { key: "molecularWeight", label: "Molecular weight" },
  { key: "criticalTemperature", label: "Critical temperature (°R)" },
  { key: "criticalPressure", label: "Critical pressure (psia)" },
  { key: "acentricFactor", label: "Acentric factor" },
  { key: "criticalVolume", label: "Critical volume" },
  { key: "parachor", label: "Parachor" },
];

export function FluidCompositionEditor({
  composition,
  onChange,
  onSave,
}: FluidCompositionEditorProps) {
  const totalMoleFraction = composition.reduce(
    (total, component) => total + component.moleFraction,
    0,
  );
  const validTotal = Math.abs(totalMoleFraction - 1) <= 1e-4;

  const updateComponent = (
    index: number,
    field: keyof PVTComponent,
    value: string,
  ) => {
    onChange(
      composition.map((component, componentIndex) => {
        if (componentIndex !== index) return component;
        if (field === "name") return { ...component, name: value };
        const numericValue = Number(value);
        return {
          ...component,
          [field]: Number.isFinite(numericValue) ? numericValue : 0,
        };
      }),
    );
  };

  const addComponent = () => {
    onChange([
      ...composition,
      {
        name: `Comp${composition.length + 1}`,
        molecularWeight: 0,
        criticalPressure: 0,
        criticalTemperature: 0,
        acentricFactor: 0,
        criticalVolume: 0,
        parachor: 0,
        moleFraction: 0,
      },
    ]);
  };

  const normalize = () => {
    if (totalMoleFraction <= 0) return;
    const normalized = composition.map((component) => ({
      ...component,
      moleFraction: Number(
        (component.moleFraction / totalMoleFraction).toFixed(5),
      ),
    }));
    onChange(normalized);
  };

  return (
    <section aria-labelledby="fluid-composition-title" className="space-y-4">
      <header className="flex items-center justify-between gap-3">
        <h3 id="fluid-composition-title" className="text-lg font-semibold">
          Fluid composition
        </h3>
        <button
          type="button"
          onClick={addComponent}
          className="inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm"
        >
          <Plus aria-hidden="true" size={16} />
          Add component
        </button>
      </header>

      <div className="space-y-3">
        {composition.map((component, index) => (
          <fieldset
            key={`${component.name}-${index}`}
            className="grid grid-cols-1 gap-3 rounded-lg border p-3 sm:grid-cols-2 lg:grid-cols-4"
          >
            <legend className="px-1 text-sm font-medium">{component.name}</legend>
            <label className="space-y-1 text-sm">
              <span>Component name</span>
              <input
                aria-label={`Component name ${index + 1}`}
                value={component.name}
                onChange={(event) =>
                  updateComponent(index, "name", event.target.value)
                }
                className="w-full rounded-md border px-2 py-1.5"
              />
            </label>
            {numericFields.map(({ key, label }) => (
              <label key={key} className="space-y-1 text-sm">
                <span>{label}</span>
                <input
                  type="number"
                  step="any"
                  aria-label={`${label} ${index + 1}`}
                  value={component[key]}
                  onChange={(event) =>
                    updateComponent(index, key, event.target.value)
                  }
                  className="w-full rounded-md border px-2 py-1.5"
                />
              </label>
            ))}
            <button
              type="button"
              aria-label={`Remove ${component.name}`}
              onClick={() =>
                onChange(composition.filter((_, itemIndex) => itemIndex !== index))
              }
              className="inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm text-red-700"
            >
              <Trash2 aria-hidden="true" size={16} />
              Remove
            </button>
          </fieldset>
        ))}
        {composition.length === 0 && (
          <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
            No components added.
          </p>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
        <p aria-live="polite" className="text-sm">
          Total mole fraction:{" "}
          <strong className={validTotal ? "text-emerald-700" : "text-amber-700"}>
            {totalMoleFraction.toFixed(4)}
          </strong>
          {!validTotal && totalMoleFraction > 0 && (
            <button
              type="button"
              onClick={normalize}
              className="ml-2 text-primary underline"
            >
              Normalize
            </button>
          )}
        </p>
        <button
          type="button"
          onClick={onSave}
          disabled={composition.length === 0 || !validTotal}
          className="rounded-md bg-primary px-4 py-2 text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
        >
          Save composition
        </button>
      </div>
    </section>
  );
}
