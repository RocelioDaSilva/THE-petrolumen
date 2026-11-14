import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldDescription } from "@/components/ui/FieldDescription";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  calculateEos,
  calculateFlash,
  EosComponentInput,
  EosResponse,
  FlashResponse,
} from "@/lib/api";

interface MixtureComponent extends EosComponentInput {
  fraction: number;
}

const initialComponent: MixtureComponent = {
  name: "methane",
  critical_pressure: 4599000,
  critical_temperature: 190.56,
  acentric_factor: 0.011,
  fraction: 1,
};

function errorMessage(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The PVT calculation could not be completed.";
}

export default function PvtEosFlashView() {
  const [pressure, setPressure] = useState(5_000_000);
  const [temperature, setTemperature] = useState(250);
  const [eosType, setEosType] = useState<"PR" | "SRK">("PR");
  const [components, setComponents] = useState<MixtureComponent[]>([{ ...initialComponent }]);
  const [eosResult, setEosResult] = useState<EosResponse | null>(null);
  const [flashResult, setFlashResult] = useState<FlashResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const buildInput = () => {
    if (components.some(({ name }) => !name.trim())) {
      throw new Error("Every mixture component needs a name.");
    }
    if (new Set(components.map(({ name }) => name)).size !== components.length) {
      throw new Error("Component names must be unique.");
    }
    const fractionTotal = components.reduce((total, component) => total + component.fraction, 0);
    if (components.some(({ fraction }) => !Number.isFinite(fraction) || fraction < 0)
      || Math.abs(fractionTotal - 1) > 1e-6) {
      throw new Error("Mole fractions must be non-negative and sum to 1.");
    }
    return {
      pressure,
      temperature,
      eos_type: eosType,
      components: components.map(({ fraction: _fraction, ...component }) => component),
      composition: Object.fromEntries(components.map(({ name, fraction }) => [name, fraction])),
    };
  };

  const calculate = async (mode: "eos" | "flash") => {
    setIsLoading(true);
    setError(null);
    setEosResult(null);
    setFlashResult(null);
    try {
      const input = buildInput();
      if (mode === "eos") setEosResult(await calculateEos(input));
      else setFlashResult(await calculateFlash(input));
    } catch (calculationError) {
      setError(errorMessage(calculationError));
    } finally {
      setIsLoading(false);
    }
  };

  const updateComponent = (index: number, patch: Partial<MixtureComponent>) => {
    setComponents((current) => current.map((component, componentIndex) =>
      componentIndex === index ? { ...component, ...patch } : component,
    ));
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">
        Run the backend Peng-Robinson or SRK equation of state and Wilson-K/Rachford-Rice
        screening flash. Pressure is in Pa and temperature is in K.
      </p>
      <Card>
        <CardHeader><CardTitle className="text-base">Mixture conditions</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="pvt-eos-pressure">Pressure (Pa)</Label>
              <Input id="pvt-eos-pressure" aria-describedby="pvt-eos-pressure-help" type="number" min="0" step="any" value={pressure} onChange={(event) => setPressure(Number(event.target.value))} />
              <FieldDescription id="pvt-eos-pressure-help">Absolute pressure; use pascals to match the component critical pressures.</FieldDescription>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pvt-eos-temperature">Temperature (K)</Label>
              <Input id="pvt-eos-temperature" aria-describedby="pvt-eos-temperature-help" type="number" min="0" step="any" value={temperature} onChange={(event) => setTemperature(Number(event.target.value))} />
              <FieldDescription id="pvt-eos-temperature-help">Absolute temperature in kelvin; use the same basis as critical temperatures.</FieldDescription>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="pvt-eos-type">Equation of state</Label>
              <Select id="pvt-eos-type" aria-describedby="pvt-eos-type-help" value={eosType} onChange={(event) => setEosType(event.target.value as "PR" | "SRK")}>
                <option value="PR">Peng-Robinson (PR)</option>
                <option value="SRK">Soave-Redlich-Kwong (SRK)</option>
              </Select>
              <FieldDescription id="pvt-eos-type-help">Choose the cubic equation used to estimate the vapor-root Z-factor.</FieldDescription>
            </div>
          </div>
          <div className="space-y-3">
            {components.map((component, index) => (
              <Card key={`${index}-${component.name}`}>
                <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
                  {([
                    ["name", "Component name", "text", "Use a unique name; the composition keys must match these names."],
                    ["critical_pressure", "Critical pressure (Pa)", "number", "Pure-component critical pressure in pascals."],
                    ["critical_temperature", "Critical temperature (K)", "number", "Pure-component critical temperature in kelvin."],
                    ["acentric_factor", "Acentric factor", "number", "Dimensionless measure of molecular shape and vapor-pressure behavior; use a value for this component."],
                    ["fraction", "Mole fraction", "number", "Component fraction in the feed; all fractions must sum to 1."],
                  ] as const).map(([field, label, type, hint]) => (
                    <div key={field} className="space-y-1.5">
                      <Label htmlFor={`pvt-component-${index}-${field}`}>{label}</Label>
                      <Input
                        id={`pvt-component-${index}-${field}`}
                        aria-describedby={`pvt-component-${index}-${field}-help`}
                        type={type}
                        step={type === "number" ? "any" : undefined}
                        value={component[field]}
                        onChange={(event) => updateComponent(index, {
                          [field]: type === "number" ? Number(event.target.value) : event.target.value,
                        })}
                      />
                      <FieldDescription id={`pvt-component-${index}-${field}-help`}>
                        {hint}
                      </FieldDescription>
                    </div>
                  ))}
                  {components.length > 1 && (
                    <Button type="button" variant="outline" onClick={() => setComponents((current) => current.filter((_, itemIndex) => itemIndex !== index))}>
                      Remove component
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setComponents((current) => [...current, {
              name: `component-${current.length + 1}`,
              critical_pressure: 4_000_000,
              critical_temperature: 300,
              acentric_factor: 0.1,
              fraction: 0,
            }])}>Add component</Button>
            <Button type="button" disabled={isLoading} aria-busy={isLoading} onClick={() => void calculate("eos")} className="gap-2">
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              {isLoading ? "Calculating..." : "Calculate Z-factor"}
            </Button>
            <Button type="button" variant="secondary" disabled={isLoading} aria-busy={isLoading} onClick={() => void calculate("flash")} className="gap-2">
              {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              {isLoading ? "Calculating..." : "Run flash"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}
      {isLoading && (
        <Card role="status" aria-label="Calculating PVT result" aria-live="polite">
          <CardContent className="space-y-3 p-5">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-16 w-full" />
          </CardContent>
        </Card>
      )}
      {eosResult && (
        <Card aria-label="EOS result">
          <CardHeader><CardTitle className="text-base">Equation-of-state result</CardTitle></CardHeader>
          <CardContent><p className="font-mono text-lg">Z-factor: {eosResult.z_factor.toPrecision(6)}</p></CardContent>
        </Card>
      )}
      {flashResult && (
        <Card aria-label="Flash result">
          <CardHeader><CardTitle className="text-base">Flash result</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <p>Phase: <strong>{flashResult.phase}</strong></p>
            <p>Vapor fraction: <strong>{flashResult.vapor_fraction.toPrecision(5)}</strong></p>
            <p>Liquid composition: <span className="font-mono">{JSON.stringify(flashResult.liquid_composition)}</span></p>
            <p>Vapor composition: <span className="font-mono">{JSON.stringify(flashResult.vapor_composition)}</span></p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
