"use client";
import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from "recharts";
import { generateProductionData } from "../../lib/connectors/databases";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "../ui/button";

export default function ProductionCharts() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    let interval: NodeJS.Timeout;
    try {
      setData(generateProductionData());
      setLoading(false);
      interval = setInterval(() => {
        setData(generateProductionData());
      }, 5000);
    } catch (e) {
      setError("Failed to load production data.");
      setLoading(false);
    }
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="skeleton h-80 w-full rounded-lg" />;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Production Decline (All Wells)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data}>
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="oil" stroke="#6366f1" name="Oil" />
              <Line type="monotone" dataKey="gas" stroke="#f59e42" name="Gas" />
              <Line type="monotone" dataKey="water" stroke="#3b82f6" name="Water" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Watercut & GOR Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data}>
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="watercut" stroke="#06b6d4" name="Watercut" />
              <Line yAxisId="right" type="monotone" dataKey="gor" stroke="#f43f5e" name="GOR" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>EUR Forecast (Oil)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data}>
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="eur" fill="#a21caf" name="EUR" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Production Dashboard</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-blue-600">{data[data.length-1]?.oil ?? 0} bbl/d</div>
              <div className="text-xs text-slate-500">Oil Rate</div>
            </div>
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-purple-600">{data[data.length-1]?.gas ?? 0} Mscf/d</div>
              <div className="text-xs text-slate-500">Gas Rate</div>
            </div>
            <div className="flex-1 text-center">
              <div className="text-2xl font-bold text-cyan-600">{data[data.length-1]?.water ?? 0} bbl/d</div>
              <div className="text-xs text-slate-500">Water Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 