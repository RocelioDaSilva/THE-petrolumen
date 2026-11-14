import type { CSSProperties } from "react";
import { ArrowLeft, GitCompare, Gauge } from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SavedSimulation } from "@/lib/api";
import {
  buildPressureComparisonData,
  buildScenarioComparisonMetrics,
} from "@/lib/scenarioComparison";

interface ScenarioComparisonViewProps {
  runs: [SavedSimulation, SavedSimulation] | null;
  onReturnToSavedRuns: () => void;
}

const axisColor = "hsl(var(--muted-foreground))";
const gridColor = "hsl(var(--border))";
const tooltipStyle: CSSProperties = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.75rem",
  color: "hsl(var(--popover-foreground))",
};

function formatInputValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    return Number.isFinite(value)
      ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 }).format(value)
      : "—";
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value;
  return JSON.stringify(value) ?? String(value);
}

function formatKey(key: string): string {
  return key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]/g, " ")
    .replace(/^./, (character) => character.toUpperCase());
}

function formatNumber(value: number | null): string {
  return value === null
    ? "Not available"
    : new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}

export default function ScenarioComparisonView({
  runs,
  onReturnToSavedRuns,
}: ScenarioComparisonViewProps) {
  if (!runs) {
    return (
      <Card>
        <CardContent className="flex flex-col items-start gap-4 p-6">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <GitCompare className="h-5 w-5 text-primary" />
              Scenario Comparison
            </CardTitle>
            <p className="mt-2 text-sm text-muted-foreground">
              Select exactly two saved reservoir simulations from My Saved Runs to compare them.
            </p>
          </div>
          <Button variant="outline" onClick={onReturnToSavedRuns} className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Return to Saved Runs
          </Button>
        </CardContent>
      </Card>
    );
  }

  const [runA, runB] = runs;
  const assumptionKeys = [...new Set([
    ...Object.keys(runA.input_data),
    ...Object.keys(runB.input_data),
  ])].sort((left, right) => left.localeCompare(right));
  const pressureData = buildPressureComparisonData(runA, runB);
  const metrics = buildScenarioComparisonMetrics(runA, runB);

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">
            <GitCompare className="h-4 w-4" />
            Engineering scenarios
          </div>
          <h1 className="text-xl font-semibold tracking-tight sm:text-2xl">Scenario Comparison</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Compare saved model assumptions, pressure response, and derived results.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={onReturnToSavedRuns} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Saved Runs
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {[runA, runB].map((run, index) => (
          <Card key={run.id}>
            <CardHeader className="flex flex-row items-center justify-between gap-3 px-5 py-4">
              <div className="min-w-0">
                <CardTitle className="truncate text-sm">{run.name}</CardTitle>
                <p className="mt-1 text-xs text-muted-foreground">
                  Saved {new Date(run.created_at).toLocaleString()}
                </p>
              </div>
              <Badge
                variant="outline"
                className={index === 0 ? "shrink-0 border-teal-500/40 text-teal-600" : "shrink-0 border-amber-500/40 text-amber-600"}
              >
                Scenario {index === 0 ? "A" : "B"}
              </Badge>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-sm">Input assumptions</CardTitle>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          {assumptionKeys.length === 0 ? (
            <p className="text-sm text-muted-foreground">No saved input assumptions are available.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th scope="col" className="py-2 pr-4 font-medium">Assumption</th>
                    <th scope="col" className="px-3 py-2 font-medium text-teal-600">{runA.name}</th>
                    <th scope="col" className="px-3 py-2 font-medium text-amber-600">{runB.name}</th>
                  </tr>
                </thead>
                <tbody>
                  {assumptionKeys.map((key) => (
                    <tr key={key} className="border-b border-border/60 last:border-0">
                      <th scope="row" className="py-2.5 pr-4 font-medium text-foreground">
                        {formatKey(key)}
                      </th>
                      <td className="px-3 py-2.5 font-mono tabular-nums text-foreground">
                        {formatInputValue(runA.input_data[key])}
                      </td>
                      <td className="px-3 py-2.5 font-mono tabular-nums text-foreground">
                        {formatInputValue(runB.input_data[key])}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="px-5 py-4">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Gauge className="h-4 w-4 text-primary" />
            Pressure vs. time
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Saved wellbore pressure histories, aligned by elapsed time.
          </p>
        </CardHeader>
        <CardContent className="px-3 pb-5 sm:px-5">
          {pressureData.length === 0 ? (
            <p role="status" className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
              No saved pressure history is available for these runs.
            </p>
          ) : (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={pressureData} margin={{ top: 8, right: 16, left: 4, bottom: 8 }}>
                  <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="time"
                    domain={["dataMin", "dataMax"]}
                    tick={{ fill: axisColor, fontSize: 11 }}
                    tickLine={{ stroke: gridColor }}
                    axisLine={{ stroke: gridColor }}
                    label={{ value: "Time (days)", position: "insideBottom", offset: -4, fill: axisColor, fontSize: 11 }}
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    tick={{ fill: axisColor, fontSize: 11 }}
                    tickLine={{ stroke: gridColor }}
                    axisLine={{ stroke: gridColor }}
                    label={{ value: "Pressure (psia)", angle: -90, position: "insideLeft", fill: axisColor, fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    formatter={(value, name) => [`${value ?? "—"} psia`, name]}
                    labelFormatter={(time) => `Day ${time}`}
                  />
                  <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 11 }} />
                  <Line
                    type="monotone"
                    dataKey="runA"
                    name={runA.name}
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2.5}
                    dot={false}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="runB"
                    name={runB.name}
                    stroke="hsl(var(--chart-4))"
                    strokeWidth={2.5}
                    dot={false}
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="px-5 py-4">
          <CardTitle className="text-sm">Key result deltas</CardTitle>
          <p className="text-xs text-muted-foreground">
            Delta is Scenario B minus Scenario A; percentage is relative to Scenario A.
          </p>
        </CardHeader>
        <CardContent className="px-5 pb-5">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead>
                <tr className="border-b border-border text-muted-foreground">
                  <th scope="col" className="py-2 pr-4 font-medium">Result</th>
                  <th scope="col" className="px-3 py-2 font-medium text-teal-600">Scenario A</th>
                  <th scope="col" className="px-3 py-2 font-medium text-amber-600">Scenario B</th>
                  <th scope="col" className="px-3 py-2 font-medium">Δ (B − A)</th>
                  <th scope="col" className="px-3 py-2 font-medium">Δ %</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((item) => (
                  <tr key={item.id} className="border-b border-border/60 last:border-0">
                    <th scope="row" className="py-2.5 pr-4 font-medium text-foreground">
                      {item.label}
                      <span className="ml-1 text-muted-foreground">({item.unit})</span>
                    </th>
                    <td className="px-3 py-2.5 font-mono tabular-nums">{formatNumber(item.valueA)}</td>
                    <td className="px-3 py-2.5 font-mono tabular-nums">{formatNumber(item.valueB)}</td>
                    <td className="px-3 py-2.5 font-mono tabular-nums">
                      {formatNumber(item.delta)}
                    </td>
                    <td className="px-3 py-2.5 font-mono tabular-nums">
                      {item.percentDelta === null
                        ? "N/A"
                        : `${item.percentDelta > 0 ? "+" : ""}${formatNumber(item.percentDelta)}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[11px] text-muted-foreground">
            Implied cumulative production is calculated as the absolute specified rate multiplied by the saved simulation horizon; it assumes a constant rate.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
