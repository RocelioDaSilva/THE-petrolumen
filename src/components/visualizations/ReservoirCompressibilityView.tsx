import { useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  calculateGasCompressibility,
  calculateRockCompressibility,
  calculateTotalCompressibility,
  type ApiError,
  type GasCompressibilityResponse,
  type RockCompressibilityResponse,
  type RockType,
  type TotalCompressibilityResponse,
} from "@/lib/api";

type CalculationResult =
  | { kind: "rock"; value: RockCompressibilityResponse }
  | { kind: "gas"; value: GasCompressibilityResponse }
  | { kind: "total"; value: TotalCompressibilityResponse };

function errorMessage(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof (error as ApiError).detail === "string"
  ) {
    return (error as ApiError).detail;
  }
  return error instanceof Error ? error.message : "The calculation could not be completed.";
}

function NumberField({
  id,
  label,
  value,
  onChange,
  min,
  max,
  step = "any",
}: {
  id: string;
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number | "any";
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}

function CompressibilityValue({ value }: { value: number }) {
  return <span className="font-mono">{value.toExponential(4)} 1/psi</span>;
}

function RangeStatus({ inRange }: { inRange: boolean }) {
  return inRange ? (
    <span className="inline-flex items-center gap-1 text-emerald-700 dark:text-emerald-400">
      <CheckCircle2 className="h-4 w-4" /> Within published range
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-amber-700 dark:text-amber-400">
      <AlertTriangle className="h-4 w-4" /> Outside published range
    </span>
  );
}

export default function ReservoirCompressibilityView() {
  const [phi, setPhi] = useState(0.2);
  const [rockType, setRockType] = useState<RockType>("sandstone");
  const [strict, setStrict] = useState(false);
  const [pressure, setPressure] = useState(2500);
  const [temperature, setTemperature] = useState(150);
  const [gasSg, setGasSg] = useState(0.9);
  const [oilCompressibility, setOilCompressibility] = useState(1e-5);
  const [waterCompressibility, setWaterCompressibility] = useState(3e-6);
  const [gasSaturation, setGasSaturation] = useState(0.1);
  const [oilSaturation, setOilSaturation] = useState(0.7);
  const [waterSaturation, setWaterSaturation] = useState(0.2);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function runCalculation(
    calculate: () => Promise<CalculationResult>,
  ) {
    setPending(true);
    setError("");
    setResult(null);
    try {
      setResult(await calculate());
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setPending(false);
    }
  }

  const gasInput = {
    p_psia: pressure,
    temperature_f: temperature,
    gas_sg: gasSg,
  };
  const saturationSum = gasSaturation + oilSaturation + waterSaturation;

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-primary" />
          <h2 className="text-2xl font-bold">Reservoir Compressibility</h2>
        </div>
        <p className="max-w-3xl text-sm text-muted-foreground">
          Calculate rock pore-volume, gas isothermal, and phase-weighted total
          compressibility. Inputs use field units; porosity and saturations are
          fractions.
        </p>
      </header>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Calculation inputs</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="total">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="rock">Rock</TabsTrigger>
                <TabsTrigger value="gas">Gas</TabsTrigger>
                <TabsTrigger value="total">Total</TabsTrigger>
              </TabsList>

              <TabsContent value="rock" className="space-y-4 pt-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <NumberField
                    id="rock-phi"
                    label="Porosity fraction"
                    value={phi}
                    onChange={setPhi}
                    min={0.000001}
                    max={0.999999}
                  />
                  <div className="space-y-1.5">
                    <Label htmlFor="rock-type">Rock type</Label>
                    <select
                      id="rock-type"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={rockType}
                      onChange={(event) => setRockType(event.target.value as RockType)}
                    >
                      <option value="sandstone">Sandstone</option>
                      <option value="limestone">Limestone</option>
                    </select>
                  </div>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={strict}
                    onChange={(event) => setStrict(event.target.checked)}
                  />
                  Enforce published porosity range
                </label>
                <Button
                  type="button"
                  disabled={pending}
                  onClick={() => runCalculation(async () => ({
                    kind: "rock",
                    value: await calculateRockCompressibility({
                      phi,
                      rock_type: rockType,
                      strict,
                    }),
                  }))}
                >
                  {pending ? "Calculating…" : "Calculate rock compressibility"}
                </Button>
              </TabsContent>

              <TabsContent value="gas" className="space-y-4 pt-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <NumberField
                    id="gas-pressure"
                    label="Pressure (psia)"
                    value={pressure}
                    onChange={setPressure}
                    min={0.000001}
                  />
                  <NumberField
                    id="gas-temperature"
                    label="Temperature (°F)"
                    value={temperature}
                    onChange={setTemperature}
                    min={-459.66}
                  />
                  <NumberField
                    id="gas-gravity"
                    label="Gas SG (air = 1)"
                    value={gasSg}
                    onChange={setGasSg}
                    min={0.000001}
                    max={1.999999}
                  />
                </div>
                <Button
                  type="button"
                  disabled={pending}
                  onClick={() => runCalculation(async () => ({
                    kind: "gas",
                    value: await calculateGasCompressibility(gasInput),
                  }))}
                >
                  {pending ? "Calculating…" : "Calculate gas compressibility"}
                </Button>
              </TabsContent>

              <TabsContent value="total" className="space-y-4 pt-4">
                <div className="grid gap-4 sm:grid-cols-3">
                  <NumberField
                    id="total-pressure"
                    label="Pressure (psia)"
                    value={pressure}
                    onChange={setPressure}
                    min={0.000001}
                  />
                  <NumberField
                    id="total-temperature"
                    label="Temperature (°F)"
                    value={temperature}
                    onChange={setTemperature}
                    min={-459.66}
                  />
                  <NumberField
                    id="total-gas-gravity"
                    label="Gas SG (air = 1)"
                    value={gasSg}
                    onChange={setGasSg}
                    min={0.000001}
                    max={1.999999}
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <NumberField
                    id="total-phi"
                    label="Porosity fraction"
                    value={phi}
                    onChange={setPhi}
                    min={0.000001}
                    max={0.999999}
                  />
                  <div className="space-y-1.5">
                    <Label htmlFor="total-rock-type">Rock type</Label>
                    <select
                      id="total-rock-type"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={rockType}
                      onChange={(event) => setRockType(event.target.value as RockType)}
                    >
                      <option value="sandstone">Sandstone</option>
                      <option value="limestone">Limestone</option>
                    </select>
                  </div>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <NumberField
                    id="oil-compressibility"
                    label="Oil compressibility (1/psi)"
                    value={oilCompressibility}
                    onChange={setOilCompressibility}
                    min={0}
                  />
                  <NumberField
                    id="water-compressibility"
                    label="Water compressibility (1/psi)"
                    value={waterCompressibility}
                    onChange={setWaterCompressibility}
                    min={0}
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                  <NumberField
                    id="gas-saturation"
                    label="Gas saturation"
                    value={gasSaturation}
                    onChange={setGasSaturation}
                    min={0}
                    max={1}
                  />
                  <NumberField
                    id="oil-saturation"
                    label="Oil saturation"
                    value={oilSaturation}
                    onChange={setOilSaturation}
                    min={0}
                    max={1}
                  />
                  <NumberField
                    id="water-saturation"
                    label="Water saturation"
                    value={waterSaturation}
                    onChange={setWaterSaturation}
                    min={0}
                    max={1}
                  />
                </div>
                <p className={`text-xs ${Math.abs(saturationSum - 1) > 1e-6 ? "text-amber-700 dark:text-amber-400" : "text-muted-foreground"}`}>
                  Saturation sum: {saturationSum.toFixed(6)} (must equal 1)
                </p>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={strict}
                    onChange={(event) => setStrict(event.target.checked)}
                  />
                  Enforce published rock porosity range
                </label>
                <Button
                  type="button"
                  disabled={pending || Math.abs(saturationSum - 1) > 1e-6}
                  onClick={() => runCalculation(async () => ({
                    kind: "total",
                    value: await calculateTotalCompressibility({
                      ...gasInput,
                      phi,
                      rock_type: rockType,
                      strict_rock_range: strict,
                      co_psi_inv: oilCompressibility,
                      cw_psi_inv: waterCompressibility,
                      sg: gasSaturation,
                      so: oilSaturation,
                      sw: waterSaturation,
                    }),
                  }))}
                >
                  {pending ? "Calculating…" : "Calculate total compressibility"}
                </Button>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Result &amp; method</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
            {!result && !error && (
              <div className="flex gap-2 rounded-md border p-3 text-sm text-muted-foreground">
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
                Run a calculation to see the engineering result and its range status.
              </div>
            )}
            {result?.kind === "rock" && (
              <div className="space-y-3">
                <Metric label="Pore-volume compressibility">
                  <CompressibilityValue value={result.value.cf_psi_inv} />
                </Metric>
                <Metric label="Lithology">{result.value.rock_type}</Metric>
                <Metric label="Correlation range">
                  <RangeStatus inRange={result.value.in_validity_range} />
                </Metric>
                <p className="text-xs text-muted-foreground">
                  Newman's correlation estimates consolidated sandstone or
                  limestone compressibility from porosity; it is not a
                  measurement of your core sample.
                </p>
              </div>
            )}
            {result?.kind === "gas" && (
              <div className="space-y-3">
                <Metric label="Gas isothermal compressibility">
                  <CompressibilityValue value={result.value.cg_psi_inv} />
                </Metric>
                <Metric label="Z-factor">{result.value.z_at_p.toFixed(6)}</Metric>
                <Metric label="dZ/dP">
                  <CompressibilityValue value={result.value.dz_dp_psi_inv} />
                </Metric>
                <Metric label="Difference">{result.value.method}, h = {result.value.h_psi} psi</Metric>
                <Metric label="Z correlation">{result.value.z_correlation}</Metric>
              </div>
            )}
            {result?.kind === "total" && (
              <div className="space-y-3">
                <Metric label="Total compressibility">
                  <CompressibilityValue value={result.value.ct_psi_inv} />
                </Metric>
                <Metric label="Gas contribution input">
                  <CompressibilityValue value={result.value.cg_psi_inv} />
                </Metric>
                <Metric label="Rock contribution">
                  <CompressibilityValue value={result.value.cf_psi_inv} />
                </Metric>
                <Metric label="Rock correlation range">
                  <RangeStatus inRange={result.value.in_rock_validity_range} />
                </Metric>
                <Metric label="Z correlation">{result.value.z_correlation}</Metric>
              </div>
            )}
            <div className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
              <p className="font-medium text-foreground">Engineering limits</p>
              <p className="mt-1">
                Gas compressibility uses the project&apos;s Hall-Yarborough Z
                correlation with Sutton pseudocritical properties, not the
                document&apos;s DAK worked-example curve. Confirm field-critical
                inputs and results with appropriate lab data and engineering
                review.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Metric({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1 border-b pb-2 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{children}</span>
    </div>
  );
}
