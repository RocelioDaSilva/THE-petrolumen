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
  getWellDataPreview,
  WellDataPreview,
} from "@/lib/backendClient";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { Loader2, Activity } from "lucide-react";

interface ProductionChartsProps {
  wellName: string;
}

const ProductionCharts: React.FC<ProductionChartsProps> = ({ wellName }) => {
  const [data, setData] = useState<WellDataPreview[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!wellName) return;
      setLoading(true);
      setError(null);
      try {
        // Fetch more rows for a better chart, e.g., 1000
        const result = await getWellDataPreview(wellName, 1000);
        setData(result.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()));
      } catch (err: any) {
        setError(err.message || "Failed to load production data");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [wellName]);

  if (!wellName) return null;

  return (
    <div className="space-y-6">
      <Card className="w-full">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-500" />
            <CardTitle>Production History: {wellName}</CardTitle>
          </div>
          <CardDescription>
            Oil, Gas, and Water production rates over time
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex justify-center items-center h-64 text-destructive">
              {error}
            </div>
          ) : data.length === 0 ? (
            <div className="flex justify-center items-center h-64 text-muted-foreground">
              No production data available for this well.
            </div>
          ) : (
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorOil" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorGas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.5} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(tick) => new Date(tick).toLocaleDateString(undefined, { month: 'short', year: '2-digit' })}
                    minTickGap={40}
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Legend verticalAlign="top" height={36}/>
                  <Area
                    type="monotone"
                    dataKey="oil_rate"
                    name="Oil Rate (bbl/d)"
                    stroke="#2563eb"
                    fillOpacity={1}
                    fill="url(#colorOil)"
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="gas_rate"
                    name="Gas Rate (mcf/d)"
                    stroke="#10b981"
                    fillOpacity={1}
                    fill="url(#colorGas)"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="water_rate"
                    name="Water Rate (bbl/d)"
                    stroke="#f43f5e"
                    strokeWidth={2}
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProductionCharts;
