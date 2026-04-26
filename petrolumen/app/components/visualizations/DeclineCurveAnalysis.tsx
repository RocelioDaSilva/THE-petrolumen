"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { getWellDCA, WellDCAResponse } from "@/lib/backendClient";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Loader2, TrendingDown } from "lucide-react";

interface DeclineCurveAnalysisProps {
  wellName: string;
}

const DeclineCurveAnalysis: React.FC<DeclineCurveAnalysisProps> = ({
  wellName,
}) => {
  const [method, setMethod] = useState<string>("hyperbolic");
  const [data, setData] = useState<WellDCAResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDCA = async () => {
    if (!wellName) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getWellDCA(wellName, method);
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to perform DCA");
      console.error("DCA Error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDCA();
  }, [wellName, method]);

  const chartData = React.useMemo(() => {
    if (!data) return [];

    // Map original data
    const original = data.original_data.map((p) => ({
      date: p.date,
      original_rate: p.rate,
    }));

    // Map forecast data
    const forecast = data.forecast_data.map((p) => ({
      date: p.date,
      forecast_rate: p.rate,
    }));

    // Combine data points by date for Recharts
    const combinedMap = new Map<string, any>();

    original.forEach((p) => combinedMap.set(p.date, { ...p }));
    forecast.forEach((p) => {
      const existing = combinedMap.get(p.date) || {};
      combinedMap.set(p.date, { ...existing, ...p, date: p.date });
    });

    return Array.from(combinedMap.values()).sort(
      (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [data]);

  if (!wellName) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Select a well to view decline curve analysis.
      </div>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5" />
              Decline Curve Analysis: {wellName}
            </CardTitle>
            <CardDescription>
              Arps decline model fitting and EUR prediction
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={method} onValueChange={setMethod}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Method" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="exponential">Exponential</SelectItem>
                <SelectItem value="hyperbolic">Hyperbolic</SelectItem>
                <SelectItem value="harmonic">Harmonic</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchDCA} disabled={loading}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Refresh"
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error ? (
          <div className="flex flex-col items-center justify-center h-64 text-destructive space-y-2">
            <p className="font-medium">Error: {error}</p>
            <Button variant="outline" onClick={fetchDCA}>
              Try Again
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(tick) =>
                      new Date(tick).toLocaleDateString(undefined, {
                        month: "short",
                        year: "2-digit",
                      })
                    }
                    minTickGap={30}
                  />
                  <YAxis label={{ value: 'Rate (bbl/d)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip
                    labelFormatter={(label) =>
                      new Date(label).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="original_rate"
                    name="Actual Rate"
                    stroke="hsl(var(--primary))"
                    strokeWidth={0}
                    dot={{ r: 3, fill: "hsl(var(--primary))" }}
                    activeDot={{ r: 5 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast_rate"
                    name="Arps Fit"
                    stroke="hsl(var(--destructive))"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {data && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">qi</p>
                  <p className="text-2xl font-bold">
                    {data.fitted_params.qi.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Di</p>
                  <p className="text-2xl font-bold">
                    {data.fitted_params.Di.toFixed(4)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">b</p>
                  <p className="text-2xl font-bold">
                    {data.fitted_params.b.toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">EUR</p>
                  <p className="text-2xl font-bold text-primary">
                    {(data.eur / 1e6).toFixed(2)} MMbbl
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeclineCurveAnalysis;
