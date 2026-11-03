"use client";

import React, { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { generateProductionData } from "../../lib/connectors/databases";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Select, SelectItem, SelectTrigger, SelectValue, SelectContent } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

function fitDeclineCurve(data: any[], model: string, params: any) {
  // Simple mock fit, replace with real math as needed
  return data.map((d, i) => ({
    ...d,
    fit: model === "arps"
      ? params.qi / Math.pow(1 + params.b * params.di * i, 1 / params.b)
      : model === "exponential"
      ? params.qi * Math.exp(-params.di * i)
      : model === "hyperbolic"
      ? params.qi / Math.pow(1 + params.b * params.di * i, 1 / params.b)
      : 0
  }));
}

export default function DeclineCurveAnalysis() {
  const [model, setModel] = useState("arps");
  const [qi, setQi] = useState(1000);
  const [di, setDi] = useState(0.1);
  const [b, setB] = useState(0.5);

  const rawData = useMemo(() => generateProductionData(), []);
  const data = useMemo(() => fitDeclineCurve(rawData, model, { qi, di, b }), [rawData, model, qi, di, b]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Decline Curve Analysis</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4 mb-4">
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="arps">Arps</SelectItem>
              <SelectItem value="exponential">Exponential</SelectItem>
              <SelectItem value="hyperbolic">Hyperbolic</SelectItem>
            </SelectContent>
          </Select>
          <Input type="number" value={qi} onChange={e => setQi(Number(e.target.value))} placeholder="Qi" className="w-24" />
          <Input type="number" value={di} onChange={e => setDi(Number(e.target.value))} placeholder="Di" className="w-24" />
          {model !== "exponential" && (
            <Input type="number" value={b} onChange={e => setB(Number(e.target.value))} placeholder="b" className="w-24" />
          )}
          <Button onClick={() => {}}>Fit</Button>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="oil" stroke="#6366f1" name="Actual" />
            <Line type="monotone" dataKey="fit" stroke="#f59e42" name="Fitted" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
} 