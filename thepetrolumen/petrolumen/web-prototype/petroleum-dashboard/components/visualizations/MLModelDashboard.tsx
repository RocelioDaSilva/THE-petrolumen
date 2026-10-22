"use client";
import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from "recharts";

// Mock data
const mlMetrics = { accuracy: 0.96, r2: 0.94, rmse: 125 };
const clusteringData = [
  { x: 1, y: 2, cluster: 1 }, { x: 2, y: 3, cluster: 1 },
  { x: 5, y: 7, cluster: 2 }, { x: 6, y: 8, cluster: 2 },
  { x: 9, y: 1, cluster: 3 }
];
const heatmapData = [
  { property: "Porosity", Permeability: 0.8, Pressure: 0.5, GOR: 0.2 },
  { property: "Permeability", Porosity: 0.8, Pressure: 0.6, GOR: 0.3 },
  { property: "Pressure", Porosity: 0.5, Permeability: 0.6, GOR: 0.7 },
  { property: "GOR", Porosity: 0.2, Permeability: 0.3, Pressure: 0.7 }
];
const forecastData = Array.from({ length: 24 }, (_, i) => ({
  month: i + 1,
  value: 1000 - i * 30 + (Math.random() - 0.5) * 50,
  lower: 1000 - i * 30 - 60,
  upper: 1000 - i * 30 + 60
}));
const anomalyData = forecastData.map((d, i) => ({
  ...d,
  anomaly: i === 10 || i === 18
}));

export default function MLModelDashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>ML Model Metrics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div>
              <div className="text-2xl font-bold text-blue-600">{(mlMetrics.accuracy * 100).toFixed(1)}%</div>
              <div className="text-xs text-slate-500">Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">{mlMetrics.r2}</div>
              <div className="text-xs text-slate-500">R²</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-cyan-600">{mlMetrics.rmse}</div>
              <div className="text-xs text-slate-500">RMSE</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Well Clustering (DBSCAN)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <ScatterChart>
              <XAxis dataKey="x" />
              <YAxis dataKey="y" />
              <Tooltip />
              <Legend />
              <Scatter data={clusteringData.filter(d => d.cluster === 1)} fill="#6366f1" name="Cluster 1" />
              <Scatter data={clusteringData.filter(d => d.cluster === 2)} fill="#f59e42" name="Cluster 2" />
              <Scatter data={clusteringData.filter(d => d.cluster === 3)} fill="#3b82f6" name="Cluster 3" />
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Correlation Heatmap</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="min-w-full text-xs">
              <thead>
                <tr>
                  <th></th>
                  {heatmapData.map((row) => (
                    <th key={row.property}>{row.property}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmapData.map((row) => (
                  <tr key={row.property}>
                    <td className="font-bold">{row.property}</td>
                    {heatmapData.map((col) => (
                      <td key={col.property}>
                        <div
                          className="w-8 h-8 flex items-center justify-center rounded"
                          style={{
                            background: `rgba(99,102,241,${Math.abs(Number(row[col.property as keyof typeof row] ?? 0))})`
                          }}
                        >
                          {typeof row[col.property as keyof typeof row] === "number"
                            ? (row[col.property as keyof typeof row] as number).toFixed(2)
                            : "-"}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Forecasting & Anomaly Detection</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={anomalyData}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#6366f1" name="Forecast" />
              <Line type="monotone" dataKey="lower" stroke="#f59e42" name="Lower" dot={false} strokeDasharray="3 3" />
              <Line type="monotone" dataKey="upper" stroke="#f59e42" name="Upper" dot={false} strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="anomaly"
                stroke="#ef4444"
                name="Anomaly"
                dot={(props) =>
                  props.payload.anomaly ? <circle r={6} fill="#ef4444" /> : null
                }
                activeDot={false}
                strokeOpacity={0}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
} 