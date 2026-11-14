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
  calculateMaterialBalance,
  MaterialBalanceInput,
  MaterialBalanceResponse,
} from "@/lib/api";

function parseValues(value: string, label: string, required: true): number[];
function parseValues(value: string, label: string, required: false): Array<number | null>;
function parseValues(
  value: string,
  label: string,
  required: boolean,
): Array<number | null> {
  if (!value.trim()) {
    if (required) throw new Error(`${label} is required.`);
    return [];
  }
  const parsed = value.split(",").map((part) => {
    if (!part.trim()) return null;
    const number = Number(part.trim());
    if (!Number.isFinite(number) || number < 0) {
      throw new Error(`${label} values must be finite and non-negative.`);
    }
    return number;
  });
  if (parsed.some((entry) => entry === null) && required) {
    throw new Error(`${label} cannot contain empty values.`);
  }
  return required ? parsed.filter((entry): entry is number => entry !== null) : parsed;
}

function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The material-balance calculation failed.";
}

export default function MaterialBalanceEnginePanel() {
  const [reservoirType, setReservoirType] = useState<"oil" | "gas">("gas");
  const [pressureHistory, setPressureHistory] = useState("4000, 3200");
  const [oilProduction, setOilProduction] = useState("");
  const [gasProduction, setGasProduction] = useState("5000000");
  const [waterProduction, setWaterProduction] = useState("100");
  const [result, setResult] = useState<MaterialBalanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const run = async () => {
    setError(null);
    setResult(null);
    setIsLoading(true);
    try {
      const pressures = parseValues(pressureHistory, "Pressure history", true);
      if (pressures.length < 2) {
        throw new Error("Pressure history needs at least two values.");
      }
      const oil = parseValues(oilProduction, "Oil production", false);
      const gas = parseValues(gasProduction, "Gas production", false);
      const water = parseValues(waterProduction, "Water production", false);
      const count = Math.max(oil.length, gas.length, water.length);
      if (count < 1) throw new Error("Enter at least one production-history value.");

      const productionHistory: MaterialBalanceInput["production_history"] =
        Array.from({ length: count }, (_, index) => {
          const point: MaterialBalanceInput["production_history"][number] = {};
          if (oil[index] !== undefined && oil[index] !== null) point.oil_prod = oil[index];
          if (gas[index] !== undefined && gas[index] !== null) point.gas_prod = gas[index];
          if (water[index] !== undefined && water[index] !== null) point.water_prod = water[index];
          return point;
        });
      const input: MaterialBalanceInput = {
        reservoir_type: reservoirType,
        pressure_history: pressures,
        production_history: productionHistory,
      };
      setResult(await calculateMaterialBalance(input));
    } catch (calculationError) {
      setError(getErrorMessage(calculationError));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Backend Havlena–Odeh material balance</CardTitle>
        <p className="text-sm text-muted-foreground">
          This is the backend solver, separate from the local gas FMB illustration above.
          Production values use STB for oil/water and Mscf for gas; pressure uses psia.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs">
          No PVT table is sent by this form; the API uses its documented default PVT points.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="mbal-reservoir-type">Reservoir type</Label>
            <Select id="mbal-reservoir-type" aria-describedby="mbal-reservoir-type-help" value={reservoirType} onChange={(event) => setReservoirType(event.target.value as "oil" | "gas")}>
              <option value="gas">Gas</option>
              <option value="oil">Oil</option>
            </Select>
            <FieldDescription id="mbal-reservoir-type-help">Choose the reservoir fluid system for the material-balance calculation.</FieldDescription>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mbal-pressure-history">Pressure history (psia, comma-separated)</Label>
            <Input id="mbal-pressure-history" aria-describedby="mbal-pressure-history-help" value={pressureHistory} onChange={(event) => setPressureHistory(event.target.value)} />
            <FieldDescription id="mbal-pressure-history-help">Enter at least two measured reservoir pressures in chronological order.</FieldDescription>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mbal-oil-production">Oil production (STB, comma-separated)</Label>
            <Input id="mbal-oil-production" aria-describedby="mbal-oil-production-help" value={oilProduction} onChange={(event) => setOilProduction(event.target.value)} />
            <FieldDescription id="mbal-oil-production-help">Cumulative oil volume per pressure observation; leave blank if unavailable.</FieldDescription>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mbal-gas-production">Gas production (Mscf, comma-separated)</Label>
            <Input id="mbal-gas-production" aria-describedby="mbal-gas-production-help" value={gasProduction} onChange={(event) => setGasProduction(event.target.value)} />
            <FieldDescription id="mbal-gas-production-help">Cumulative gas volume per pressure observation; leave blank for unavailable entries.</FieldDescription>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="mbal-water-production">Water production (STB, comma-separated)</Label>
            <Input id="mbal-water-production" aria-describedby="mbal-water-production-help" value={waterProduction} onChange={(event) => setWaterProduction(event.target.value)} />
            <FieldDescription id="mbal-water-production-help">Cumulative water volume per pressure observation; leave blank if unavailable.</FieldDescription>
          </div>
        </div>
        <Button type="button" onClick={() => void run()} disabled={isLoading} aria-busy={isLoading} className="gap-2">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
          {isLoading ? "Calculating..." : "Run Havlena–Odeh"}
        </Button>
        {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}
        {isLoading && (
          <div role="status" aria-label="Calculating material balance" aria-live="polite" className="space-y-3 rounded-md border p-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}
        {result && (
          <div role="status" className="rounded-md border bg-muted/30 p-3">
            <p className="text-sm font-semibold">
              {result.reservoir_type === "gas" ? "OGIP" : "OOIP"}: {result.ooip_or_ogip.toPrecision(6)}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">{result.note}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
