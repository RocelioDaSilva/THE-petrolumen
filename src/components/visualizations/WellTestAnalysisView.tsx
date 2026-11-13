import { useState } from "react";
import { Activity, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  analyzeWellTestBuildup,
  analyzeWellTestDrawdown,
  BuildupResult,
  DrawdownResult,
} from "@/lib/api";

type AnalysisMode = "drawdown" | "buildup";
type Result = DrawdownResult | BuildupResult;

const inputClassName = "font-mono";

function parseSeries(value: string, label: string): number[] {
  const parts = value.split(",").map((part) => part.trim());
  const values = parts.map(Number);
  if (
    parts.length < 3
    || parts.some((part) => part.length === 0)
    || values.some((entry) => !Number.isFinite(entry))
  ) {
    throw new Error(`${label} must contain at least three comma-separated numbers.`);
  }
  return values;
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
  return error instanceof Error ? error.message : "Well-test analysis failed.";
}

export default function WellTestAnalysisView() {
  const [mode, setMode] = useState<AnalysisMode>("drawdown");
  const [times, setTimes] = useState("");
  const [pressures, setPressures] = useState("");
  const [rate, setRate] = useState(500);
  const [viscosity, setViscosity] = useState(1);
  const [totalCompressibility, setTotalCompressibility] = useState(0.00001);
  const [porosity, setPorosity] = useState(0.2);
  const [wellboreRadius, setWellboreRadius] = useState(0.35);
  const [netPay, setNetPay] = useState(30);
  const [formationVolumeFactor, setFormationVolumeFactor] = useState(1.2);
  const [initialPressure, setInitialPressure] = useState(3500);
  const [producingTime, setProducingTime] = useState(720);
  const [shutInPressure, setShutInPressure] = useState(2800);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const analyze = async () => {
    setError(null);
    setResult(null);
    setIsLoading(true);
    try {
      const time = parseSeries(times, "Time");
      const pressure = parseSeries(pressures, "Pressure");
      if (time.length !== pressure.length) {
        throw new Error("Time and pressure must contain the same number of values.");
      }

      const common = {
        time,
        pressure,
        rate,
        viscosity,
        total_compressibility: totalCompressibility,
        porosity,
        wellbore_radius: wellboreRadius,
        net_pay: netPay,
        formation_volume_factor: formationVolumeFactor,
      };
      const analysisResult = mode === "drawdown"
        ? await analyzeWellTestDrawdown({ ...common, initial_pressure: initialPressure })
        : await analyzeWellTestBuildup({
            ...common,
            producing_time: producingTime,
            p_wf_at_shutin: shutInPressure,
          });
      setResult(analysisResult);
    } catch (analysisError) {
      setError(getErrorMessage(analysisError));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h2 className="flex items-center gap-2 text-2xl font-bold">
          <Activity className="h-6 w-6 text-primary" />
          Pressure Transient Well-Test Analysis
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Estimate permeability, skin, and flow regimes from measured pressure history.
          Enter elapsed time in hours and pressure in psia.
        </p>
      </header>

      <div role="tablist" aria-label="Well-test analysis type" className="flex gap-2">
        {(["drawdown", "buildup"] as const).map((value) => (
          <Button
            key={value}
            type="button"
            role="tab"
            aria-selected={mode === value}
            variant={mode === value ? "default" : "outline"}
            onClick={() => {
              setMode(value);
              setResult(null);
              setError(null);
            }}
          >
            {value === "drawdown" ? "Drawdown" : "Buildup"}
          </Button>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Test data and reservoir properties</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="well-test-times">Elapsed time (hours, comma-separated)</Label>
            <Input
              id="well-test-times"
              className={inputClassName}
              placeholder="0.1, 0.2, 0.5, 1, 2"
              value={times}
              onChange={(event) => setTimes(event.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="well-test-pressures">Pressure (psia, comma-separated)</Label>
            <Input
              id="well-test-pressures"
              className={inputClassName}
              placeholder="3400, 3320, 3250, 3180, 3120"
              value={pressures}
              onChange={(event) => setPressures(event.target.value)}
            />
          </div>
          <NumberField id="well-test-rate" label="Rate (STB/day)" value={rate} onChange={setRate} />
          <NumberField id="well-test-viscosity" label="Viscosity (cp)" value={viscosity} onChange={setViscosity} />
          <NumberField
            id="well-test-ct"
            label="Total compressibility (1/psi)"
            value={totalCompressibility}
            onChange={setTotalCompressibility}
            step="any"
          />
          <NumberField id="well-test-phi" label="Porosity (fraction)" value={porosity} onChange={setPorosity} step="any" />
          <NumberField id="well-test-radius" label="Wellbore radius (ft)" value={wellboreRadius} onChange={setWellboreRadius} step="any" />
          <NumberField id="well-test-pay" label="Net pay (ft)" value={netPay} onChange={setNetPay} step="any" />
          <NumberField id="well-test-fvf" label="Formation volume factor (RB/STB)" value={formationVolumeFactor} onChange={setFormationVolumeFactor} step="any" />
          {mode === "drawdown" ? (
            <NumberField
              id="well-test-initial-pressure"
              label="Initial pressure (psia)"
              value={initialPressure}
              onChange={setInitialPressure}
            />
          ) : (
            <>
              <NumberField
                id="well-test-producing-time"
                label="Producing time before shut-in (hours)"
                value={producingTime}
                onChange={setProducingTime}
              />
              <NumberField
                id="well-test-shutin-pressure"
                label="Flowing pressure at shut-in (psia)"
                value={shutInPressure}
                onChange={setShutInPressure}
              />
            </>
          )}
          <div className="md:col-span-2">
            <Button type="button" onClick={analyze} disabled={isLoading}>
              {isLoading ? "Analyzing..." : `Analyze ${mode}`}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error && (
        <p role="alert" className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </p>
      )}

      {result && (
        <Card aria-label="Well-test results">
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base">
              Analysis results
              <Badge variant="outline">{mode}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <ResultMetric label="Permeability" value={`${result.permeability_md.toFixed(3)} mD`} />
              <ResultMetric label="Skin" value={result.skin.toFixed(3)} />
              <ResultMetric label="Slope" value={`${result.slope_psi_per_cycle.toFixed(3)} psi/cycle`} />
              <ResultMetric label="P1hr" value={`${result.p1hr_psi.toFixed(2)} psia`} />
              {"radius_of_investigation_ft" in result && (
                <ResultMetric label="Investigation radius" value={`${result.radius_of_investigation_ft.toFixed(2)} ft`} />
              )}
              {"p_star_psi" in result && (
                <ResultMetric label="P*" value={`${result.p_star_psi.toFixed(2)} psia`} />
              )}
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold">Detected flow regimes</h3>
              {result.regimes.notes.length > 0 ? (
                <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                  {result.regimes.notes.map((note) => <li key={note}>{note}</li>)}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">No regime notes were returned.</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function NumberField({
  id,
  label,
  value,
  onChange,
  step,
}: {
  id: string;
  label: string;
  value: number;
  onChange: (value: number) => void;
  step?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type="number"
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </div>
  );
}

function ResultMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/30 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 font-mono text-lg font-semibold">{value}</p>
    </div>
  );
}
