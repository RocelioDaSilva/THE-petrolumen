import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
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
import { Activity, CalendarClock, RefreshCw, Upload, Waves } from "lucide-react";
import { useAuth } from "@/lib/authContext";
import {
  fetchProductionOverview,
  fetchProductionWells,
  ProductionOverview as ProductionOverviewData,
  ProductionWell,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface ProductionOverviewProps {
  onNavigate: (moduleId: string) => void;
}

const numberFormatter = new Intl.NumberFormat(undefined, {
  maximumFractionDigits: 2,
});

function formatRate(value: number | null | undefined): string {
  return value == null ? "—" : numberFormatter.format(value);
}

function formatDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function formatImportDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "detail" in error) {
    return String(error.detail);
  }
  return error instanceof Error ? error.message : "Could not load production data.";
}

export default function ProductionOverview({ onNavigate }: ProductionOverviewProps) {
  const { user, openAuthDialog } = useAuth();
  const requestId = useRef(0);
  const [wells, setWells] = useState<ProductionWell[]>([]);
  const [overview, setOverview] = useState<ProductionOverviewData | null>(null);
  const [loading, setLoading] = useState(Boolean(user));
  const [error, setError] = useState<string | null>(null);

  const loadProduction = useCallback(async () => {
    if (!user) return;
    const currentRequestId = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const [wellData, productionData] = await Promise.all([
        fetchProductionWells(),
        fetchProductionOverview(),
      ]);
      if (currentRequestId === requestId.current) {
        setWells(wellData);
        setOverview(productionData);
      }
    } catch (loadError) {
      if (currentRequestId === requestId.current) {
        setError(getErrorMessage(loadError));
      }
    } finally {
      if (currentRequestId === requestId.current) {
        setLoading(false);
      }
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      requestId.current += 1;
      setWells([]);
      setOverview(null);
      setLoading(false);
      setError(null);
      return;
    }
    void loadProduction();
    return () => {
      requestId.current += 1;
    };
  }, [loadProduction, user]);

  const latestRatesByWell = useMemo(
    () => new Map(overview?.latest_well_rates.map((item) => [item.well_id, item]) ?? []),
    [overview],
  );
  const currentRates = useMemo(
    () =>
      (overview?.latest_well_rates ?? []).reduce(
        (totals, well) => ({
          oil: totals.oil + (well.oil_rate ?? 0),
          gas: totals.gas + (well.gas_rate ?? 0),
          water: totals.water + (well.water_rate ?? 0),
        }),
        { oil: 0, gas: 0, water: 0 },
      ),
    [overview],
  );

  return (
    <section className="space-y-4" aria-labelledby="production-overview-title">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 id="production-overview-title" className="text-xl font-semibold tracking-tight">
            Production Overview
          </h2>
          <p className="text-sm text-muted-foreground">
            Live summary of production data imported to your account.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {user ? (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => void loadProduction()}
              disabled={loading}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          ) : null}
          <Button
            type="button"
            size="sm"
            onClick={() =>
              user ? onNavigate("production-data-import") : openAuthDialog()
            }
          >
            {user ? <Upload className="mr-2 h-4 w-4" /> : null}
            {user ? "Import production CSV" : "Sign in to view production"}
          </Button>
        </div>
      </div>

      {!user ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center">
            <Activity className="h-8 w-8 text-muted-foreground" />
            <p className="font-medium">Sign in to view your production dashboard.</p>
            <p className="text-sm text-muted-foreground">
              Imported wells and production data are private to your account.
            </p>
          </CardContent>
        </Card>
      ) : loading ? (
        <div className="space-y-4" role="status" aria-label="Loading production overview">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <Card key={index}>
                <CardContent className="space-y-3 p-5">
                  <Skeleton className="h-4 w-28" />
                  <Skeleton className="h-8 w-32" />
                </CardContent>
              </Card>
            ))}
          </div>
          <Card>
            <CardContent className="space-y-3 p-5">
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        </div>
      ) : error ? (
        <Card role="alert" className="border-destructive/40">
          <CardContent className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="font-medium">Production data could not be loaded.</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <Button type="button" size="sm" variant="outline" onClick={() => void loadProduction()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : wells.length === 0 || !overview?.series.length ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Waves className="h-9 w-9 text-muted-foreground" />
            <div>
              <p className="font-medium">No production data yet.</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Import a CSV to get started. Your wells and production history will appear here.
              </p>
            </div>
            <Button type="button" onClick={() => onNavigate("production-data-import")}>
              <Upload className="mr-2 h-4 w-4" />
              Import CSV now
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Total Wells" value={numberFormatter.format(wells.length)} icon={<Activity className="h-4 w-4" />} />
            <MetricCard label="Total Oil Rate" value={formatRate(currentRates.oil)} />
            <MetricCard label="Total Gas Rate" value={formatRate(currentRates.gas)} />
            <MetricCard label="Total Water Rate" value={formatRate(currentRates.water)} />
          </div>
          <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
            <Card className="min-w-0">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Waves className="h-4 w-4 text-primary" />
                  Aggregated Production Rates
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Daily rates summed across your wells; values use the units in the source CSV.
                </p>
              </CardHeader>
              <CardContent>
                <div className="h-[300px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={overview.series} margin={{ top: 8, right: 12, left: 12, bottom: 24 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                      <XAxis
                        dataKey="date"
                        tickFormatter={formatDate}
                        minTickGap={24}
                        tick={{ fontSize: 11 }}
                        label={{ value: "Production date", position: "insideBottom", offset: -4 }}
                      />
                      <YAxis
                        tick={{ fontSize: 11 }}
                        width={60}
                        label={{ value: "Rate (source CSV units)", angle: -90, position: "insideLeft" }}
                      />
                      <Tooltip
                        labelFormatter={(label) => formatDate(String(label))}
                        formatter={(value, name) => [`${formatRate(Number(value))} (source units)`, name]}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="oil_rate" name="Oil" stroke="hsl(var(--chart-1))" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="gas_rate" name="Gas" stroke="hsl(var(--chart-2))" dot={false} strokeWidth={2} />
                      <Line type="monotone" dataKey="water_rate" name="Water" stroke="hsl(var(--chart-3))" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <CalendarClock className="h-4 w-4 text-primary" />
                  Latest Import Date
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-lg font-semibold">
                  {formatImportDate(overview.latest_import_at)}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Timestamp of the latest production record added to your account.
                </p>
                <p className="mt-4 border-t pt-3 text-xs text-muted-foreground">
                  Production rates retain the units used in each CSV; unit provenance is not yet stored.
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Legacy records may not have a recorded import timestamp.
                </p>
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Wells and Latest Rates</CardTitle>
              <p className="text-xs text-muted-foreground">
                Latest available production record for each owned well.
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs text-muted-foreground">
                      <th scope="col" className="pb-2 pr-4 font-medium">Well</th>
                      <th scope="col" className="pb-2 pr-4 font-medium">Latest date</th>
                      <th scope="col" className="pb-2 pr-4 text-right font-medium">Oil</th>
                      <th scope="col" className="pb-2 pr-4 text-right font-medium">Gas</th>
                      <th scope="col" className="pb-2 text-right font-medium">Water</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {wells.map((well) => {
                      const latest = latestRatesByWell.get(well.id);
                      return (
                        <tr key={well.id} className="hover:bg-muted/30">
                          <th scope="row" className="py-3 pr-4 text-left font-medium">{well.name}</th>
                          <td className="py-3 pr-4 text-muted-foreground">
                            {latest ? formatDate(latest.date) : "—"}
                          </td>
                          <td className="py-3 pr-4 text-right font-mono">{formatRate(latest?.oil_rate)}</td>
                          <td className="py-3 pr-4 text-right font-mono">{formatRate(latest?.gas_rate)}</td>
                          <td className="py-3 text-right font-mono">{formatRate(latest?.water_rate)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Rates are displayed in their source CSV units.
              </p>
            </CardContent>
          </Card>
        </>
      )}
    </section>
  );
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon?: ReactNode;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="flex items-center gap-2 text-sm text-muted-foreground">
          {icon}
          {label}
        </p>
        <p className="mt-2 font-mono text-2xl font-semibold tabular-nums">{value}</p>
      </CardContent>
    </Card>
  );
}
