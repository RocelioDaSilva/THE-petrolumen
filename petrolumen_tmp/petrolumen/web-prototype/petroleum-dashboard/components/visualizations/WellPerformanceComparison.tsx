"use client";
import React, { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { generateProductionData } from "../../lib/connectors/databases";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Select, SelectItem, SelectTrigger, SelectValue, SelectContent } from "@/components/ui/select";

const allWells = ["Well-1", "Well-2", "Well-3", "Well-4", "Well-5"];

export default function WellPerformanceComparison() {
  const [selectedWells, setSelectedWells] = useState<string[]>([allWells[0], allWells[1]]);
  const allData = useMemo(() => {
    // Simulate per-well data
    return allWells.reduce((acc, well) => {
      acc[well] = generateProductionData().map((d: any) => ({
        ...d,
        oil: d.oil * (0.8 + Math.random() * 0.4),
        gas: d.gas * (0.8 + Math.random() * 0.4),
        water: d.water * (0.8 + Math.random() * 0.4),
      }));
      return acc;
    }, {} as Record<string, any[]>);
  }, []);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Well Performance Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 mb-4">
          <Select
            value={selectedWells[0]}
            onValueChange={v => setSelectedWells([v, selectedWells[1]])}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {allWells.map(well => (
                <SelectItem key={well} value={well}>{well}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={selectedWells[1]}
            onValueChange={v => setSelectedWells([selectedWells[0], v])}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {allWells.map(well => (
                <SelectItem key={well} value={well}>{well}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            {selectedWells.map((well, idx) => (
              <Line
                key={well}
                data={allData[well]}
                dataKey="oil"
                stroke={idx === 0 ? "#6366f1" : "#f59e42"}
                name={`${well} Oil`}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
} 