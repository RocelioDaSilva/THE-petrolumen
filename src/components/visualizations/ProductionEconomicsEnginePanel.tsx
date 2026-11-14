import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldDescription } from "@/components/ui/FieldDescription";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  calculateProductionEconomics,
  ProductionEconomicsResponse,
} from "@/lib/api";

function parseVolumes(value: string, label: string): number[] {
  const parsed = value.split(",").map((part) => Number(part.trim()));
  if (!parsed.length || parsed.some((amount) => !Number.isFinite(amount) || amount < 0)) {
    throw new Error(`${label} must contain finite, non-negative annual volumes.`);
  }
  return parsed;
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
  return error instanceof Error ? error.message : "The economics calculation failed.";
}

export default function ProductionEconomicsEnginePanel() {
  const [oilPrice, setOilPrice] = useState(70);
  const [gasPrice, setGasPrice] = useState(3);
  const [discountRate, setDiscountRate] = useState(10);
  const [capex, setCapex] = useState(1_500_000);
  const [annualOpex, setAnnualOpex] = useState(75_000);
  const [taxRate, setTaxRate] = useState(0.34);
  const [waterDisposalCost, setWaterDisposalCost] = useState(1.5);
  const [oilProduction, setOilProduction] = useState("100000, 80000, 60000");
  const [gasProduction, setGasProduction] = useState("500000, 400000, 300000");
  const [waterProduction, setWaterProduction] = useState("20000, 30000, 40000");
  const [result, setResult] = useState<ProductionEconomicsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const run = async () => {
    setError(null);
    setResult(null);
    setIsLoading(true);
    try {
      const oil = parseVolumes(oilProduction, "Oil production");
      const gas = parseVolumes(gasProduction, "Gas production");
      const water = parseVolumes(waterProduction, "Water production");
      if (gas.length !== oil.length || water.length !== oil.length) {
        throw new Error("Oil, gas, and water profiles must have the same number of annual volumes.");
      }
      setResult(await calculateProductionEconomics({
        oil_price: oilPrice,
        gas_price: gasPrice,
        discount_rate: discountRate,
        project_life: oil.length,
        capex: { initial_capex: capex },
        opex: { annual_opex: annualOpex },
        tax_rate: taxRate,
        water_disposal_cost_per_bbl: waterDisposalCost,
        oil_production: oil,
        gas_production: gas,
        water_production: water,
      }));
    } catch (calculationError) {
      setError(getErrorMessage(calculationError));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Backend production economics</CardTitle>
        <p className="text-sm text-muted-foreground">
          Annual production volumes are bbl/year for oil and water, and Mscf/year
          for gas. The backend applies taxes, depreciation, and water-disposal costs.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {([
            ["econ-api-oil-price", "Oil price ($/bbl)", oilPrice, setOilPrice, "Price applied to each annual oil volume."],
            ["econ-api-gas-price", "Gas price ($/Mscf)", gasPrice, setGasPrice, "Price applied to each annual gas volume in Mscf."],
            ["econ-api-discount", "Discount rate (%)", discountRate, setDiscountRate, "Annual discount rate entered as a percentage."],
            ["econ-api-capex", "Initial CAPEX ($)", capex, setCapex, "One-time project investment charged at year zero."],
            ["econ-api-opex", "Annual OPEX ($)", annualOpex, setAnnualOpex, "Recurring operating cost applied in each project year."],
            ["econ-api-tax", "Tax rate (fraction)", taxRate, setTaxRate, "Enter a fraction from 0 to 1 (for example, 0.34 for 34%)."],
            ["econ-api-water-cost", "Water disposal ($/bbl)", waterDisposalCost, setWaterDisposalCost, "Disposal cost multiplied by annual produced-water volume."],
          ] as const).map(([id, label, value, setValue, hint]) => (
            <div key={id} className="space-y-1.5">
              <Label htmlFor={id}>{label}</Label>
              <Input
                id={id}
                aria-describedby={`${id}-help`}
                type="number"
                min="0"
                step="any"
                value={value}
                onChange={(event) => setValue(Number(event.target.value))}
              />
              <FieldDescription id={`${id}-help`}>{hint}</FieldDescription>
            </div>
          ))}
          {([
            ["econ-api-oil-profile", "Oil volumes (bbl/year)", oilProduction, setOilProduction],
            ["econ-api-gas-profile", "Gas volumes (Mscf/year)", gasProduction, setGasProduction],
            ["econ-api-water-profile", "Water volumes (bbl/year)", waterProduction, setWaterProduction],
          ] as const).map(([id, label, value, setValue]) => (
            <div key={id} className="space-y-1.5 lg:col-span-2">
              <Label htmlFor={id}>{label}</Label>
              <Input id={id} aria-describedby={`${id}-help`} value={value} onChange={(event) => setValue(event.target.value)} />
              <FieldDescription id={`${id}-help`}>
                Enter one annual volume per year, comma-separated; all three profiles must have equal lengths.
              </FieldDescription>
            </div>
          ))}
        </div>
        <Button type="button" onClick={() => void run()} disabled={isLoading} aria-busy={isLoading} className="gap-2">
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
          {isLoading ? "Calculating..." : "Run backend economics"}
        </Button>
        {error && <p role="alert" className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</p>}
        {isLoading && (
          <div role="status" aria-label="Calculating production economics" aria-live="polite" className="grid gap-3 rounded-md border p-3 sm:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <Skeleton key={index} className="h-14 w-full" />
            ))}
          </div>
        )}
        {result && (
          <div role="status" className="grid gap-3 rounded-md border bg-muted/30 p-3 sm:grid-cols-4">
            <p>NPV: <strong>{result.npv.toLocaleString(undefined, { maximumFractionDigits: 2 })}</strong></p>
            <p>IRR: <strong>{result.irr === null ? "N/A" : `${result.irr.toFixed(2)}%`}</strong></p>
            <p>Payout: <strong>{result.payout === null ? "N/A" : `${result.payout.toFixed(2)} years`}</strong></p>
            <p>ROI: <strong>{result.roi === null ? "N/A" : `${result.roi.toFixed(2)}%`}</strong></p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
