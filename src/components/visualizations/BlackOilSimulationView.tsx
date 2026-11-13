import { useState } from "react";
import { Activity, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  BlackOilSimulationInput,
  BlackOilSimulationResponse,
  runBlackOilSimulation,
} from "@/lib/api";

function parseCellValues(value: string, label: string, count: number): number[] {
  const cells = value.split(",").map((part) => Number(part.trim()));
  if (
    cells.length !== count
    || cells.some((cell) => !Number.isFinite(cell))
  ) {
    throw new Error(`${label} must contain exactly ${count} finite comma-separated values.`);
  }
  return cells;
}

function errorMessage(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The simulation could not be completed.";
}

export default function BlackOilSimulationView() {
  const [nx, setNx] = useState(2);
  const [porosity, setPorosity] = useState("0.2, 0.2");
  const [permeability, setPermeability] = useState("100, 100");
  const [waterSaturation, setWaterSaturation] = useState("0.2, 0.2");
  const [gasSaturation, setGasSaturation] = useState("0, 0");
  const [initialPressure, setInitialPressure] = useState(3000);
  const [timestep, setTimestep] = useState(1);
  const [waterViscosity, setWaterViscosity] = useState(1);
  const [oilViscosity, setOilViscosity] = useState(2);
  const [gasViscosity, setGasViscosity] = useState(0.02);
  const [includeWell, setIncludeWell] = useState(false);
  const [wellType, setWellType] = useState<"producer" | "injector">("producer");
  const [control, setControl] = useState<"bhp" | "water_rate" | "gas_rate">("bhp");
  const [controlValue, setControlValue] = useState(2800);
  const [result, setResult] = useState<BlackOilSimulationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const run = async () => {
    setError(null);
    setResult(null);
    setIsLoading(true);
    try {
      if (!Number.isInteger(nx) || nx < 1 || nx > 512) {
        throw new Error("Cell count must be an integer between 1 and 512.");
      }

      const input: BlackOilSimulationInput = {
        grid: { nx, ny: 1, nz: 1, dx: 50, dy: 50, dz: 10 },
        porosity: parseCellValues(porosity, "Porosity", nx),
        permeability: parseCellValues(permeability, "Permeability", nx),
        rock_compressibility: 0,
        fluid_properties: {
          water_viscosity: waterViscosity,
          oil_viscosity: oilViscosity,
          gas_viscosity: gasViscosity,
        },
        initial_pressure: initialPressure,
        initial_water_saturation: parseCellValues(waterSaturation, "Initial water saturation", nx),
        initial_gas_saturation: parseCellValues(gasSaturation, "Initial gas saturation", nx),
        timesteps: [timestep],
      };
      if (includeWell) {
        input.wells = [{
          name: "Well 1",
          i: 0,
          j: 0,
          perforation_layers: [0],
          well_type: wellType,
          controls: { [control]: controlValue },
        }];
      }
      setResult(await runBlackOilSimulation(input));
    } catch (simulationError) {
      setError(errorMessage(simulationError));
    } finally {
      setIsLoading(false);
    }
  };

  const cellFields = [
    { id: "black-oil-porosity", label: "Porosity per cell", value: porosity, setValue: setPorosity },
    { id: "black-oil-permeability", label: "Permeability per cell (mD)", value: permeability, setValue: setPermeability },
    { id: "black-oil-sw", label: "Initial water saturation per cell", value: waterSaturation, setValue: setWaterSaturation },
    { id: "black-oil-sg", label: "Initial gas saturation per cell", value: gasSaturation, setValue: setGasSaturation },
  ];

  return (
    <div className="space-y-5">
      <header>
        <h3 className="flex items-center gap-2 text-xl font-semibold">
          <Activity className="h-5 w-5 text-primary" />
          Backend Black-Oil Simulation
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure a 1D grid and run the existing backend solver. Cell arrays use
          comma-separated values in cell order.
        </p>
      </header>

      <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
        Engineering limitation: this backend solver is documented as simplified and
        non-conservative. Treat results as experimental, not design-grade predictions.
      </p>

      <Card>
        <CardHeader><CardTitle className="text-base">Grid and initial state</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-nx">Cells (nx)</Label>
              <Input id="black-oil-nx" type="number" min="1" max="512" value={nx} onChange={(event) => {
                const nextCount = Number(event.target.value);
                setNx(nextCount);
                const defaults = Array.from({ length: Math.max(0, Math.min(nextCount, 512)) }, () => "0.2");
                setPorosity(defaults.join(", "));
                setPermeability(defaults.map(() => "100").join(", "));
                setWaterSaturation(defaults.join(", "));
                setGasSaturation(defaults.map(() => "0").join(", "));
              }} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-pressure">Initial pressure (psia)</Label>
              <Input id="black-oil-pressure" type="number" value={initialPressure} onChange={(event) => setInitialPressure(Number(event.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-timestep">Timestep (days)</Label>
              <Input id="black-oil-timestep" type="number" min="0.001" step="any" value={timestep} onChange={(event) => setTimestep(Number(event.target.value))} />
            </div>
            {cellFields.map(({ id, label, value, setValue }) => (
              <div key={id} className="space-y-1.5 sm:col-span-2 lg:col-span-3">
                <Label htmlFor={id}>{label}</Label>
                <Input id={id} value={value} onChange={(event) => setValue(event.target.value)} />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Fluid properties and controls</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-mu-water">Water viscosity (cP)</Label>
              <Input id="black-oil-mu-water" type="number" min="0.001" step="any" value={waterViscosity} onChange={(event) => setWaterViscosity(Number(event.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-mu-oil">Oil viscosity (cP)</Label>
              <Input id="black-oil-mu-oil" type="number" min="0.001" step="any" value={oilViscosity} onChange={(event) => setOilViscosity(Number(event.target.value))} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="black-oil-mu-gas">Gas viscosity (cP)</Label>
              <Input id="black-oil-mu-gas" type="number" min="0.001" step="any" value={gasViscosity} onChange={(event) => setGasViscosity(Number(event.target.value))} />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={includeWell} onChange={(event) => setIncludeWell(event.target.checked)} />
            Include a well in the first cell
          </label>
          {includeWell && (
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="black-oil-well-type">Well type</Label>
                <select id="black-oil-well-type" className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={wellType} onChange={(event) => setWellType(event.target.value as "producer" | "injector")}>
                  <option value="producer">Producer</option>
                  <option value="injector">Injector</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="black-oil-control">Control</Label>
                <select id="black-oil-control" className="h-10 w-full rounded-md border bg-background px-3 text-sm" value={control} onChange={(event) => setControl(event.target.value as "bhp" | "water_rate" | "gas_rate")}>
                  <option value="bhp">Bottom-hole pressure (psia)</option>
                  <option value="water_rate">Water rate</option>
                  <option value="gas_rate">Gas rate</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="black-oil-control-value">Control value</Label>
                <Input id="black-oil-control-value" type="number" min="0" step="any" value={controlValue} onChange={(event) => setControlValue(Number(event.target.value))} />
              </div>
            </div>
          )}
          <Button type="button" onClick={() => void run()} disabled={isLoading} className="gap-2">
            <Play className="h-4 w-4" />
            {isLoading ? "Running..." : "Run black-oil solver"}
          </Button>
        </CardContent>
      </Card>

      {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}

      {result && (
        <Card aria-label="Black-oil simulation results">
          <CardHeader><CardTitle className="text-base">Final state by cell</CardTitle></CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[36rem] text-left text-sm">
              <thead><tr className="border-b text-muted-foreground">
                <th className="p-2">Cell</th><th className="p-2">Pressure (psia)</th>
                <th className="p-2">Water saturation</th><th className="p-2">Gas saturation</th>
              </tr></thead>
              <tbody>
                {result.pressure.map((pressure, index) => (
                  <tr key={index} className="border-b last:border-0">
                    <td className="p-2">{index + 1}</td>
                    <td className="p-2 font-mono">{pressure.toPrecision(6)}</td>
                    <td className="p-2 font-mono">{result.saturations.water?.[index]?.toPrecision(5) ?? "—"}</td>
                    <td className="p-2 font-mono">{result.saturations.gas?.[index]?.toPrecision(5) ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-xs text-muted-foreground">
              {result.wells.length} well result{result.wells.length === 1 ? "" : "s"} returned.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
