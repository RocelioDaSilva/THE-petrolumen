'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { useUnitStore } from '@/stores/unitStore';
import { convert } from '@/lib/units';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PVTPage() {
  const { unitSystem } = useUnitStore();
  const [pressure, setPressure] = useState(3000);
  const [temp, setTemp] = useState(160);
  const [gammaG, setGammaG] = useState(0.65);
  const [zFactor, setZFactor] = useState<number | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);

  const displayPressure = unitSystem === 'metric' ? convert(pressure, 'psi', 'kPa') : pressure;
  const pressureLabel = unitSystem === 'metric' ? 'kPa' : 'psia';

  const calculate = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/gaia/pvt/z-factor`, {
        pressure: Number(pressure),
        temperature: Number(temp),
        gamma_g: Number(gammaG)
      });
      setZFactor(res.data.z_factor);

      const sweep = [];
      for (let p = 500; p <= 5000; p += 500) {
        const sweepRes = await axios.post(`${API_URL}/api/v1/gaia/pvt/z-factor`, {
          pressure: p,
          temperature: Number(temp),
          gamma_g: Number(gammaG)
        });
        sweep.push({
          p: unitSystem === 'metric' ? convert(p, 'psi', 'kPa') : p,
          z: sweepRes.data.z_factor
        });
      }
      setChartData(sweep);
    } catch (e) { console.error(e); }
  };

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">PVT Calculator ({unitSystem})</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader><CardTitle>Parameters</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Label>Pressure ({pressureLabel})</Label>
            <Input type="number" value={displayPressure.toFixed(0)} readOnly className="bg-muted" />
            <p className="text-xs text-muted-foreground italic">Input is always stored in field units internally.</p>
            <Label>Raw Pressure (psia)</Label>
            <Input type="number" value={pressure} onChange={e => setPressure(Number(e.target.value))} />

            <Label>Temperature (°F)</Label>
            <Input type="number" value={temp} onChange={e => setTemp(Number(e.target.value))} />
            <Label>Gas Gravity</Label>
            <Input type="number" step="0.01" value={gammaG} onChange={e => setGammaG(Number(e.target.value))} />
            <Button onClick={calculate} className="w-full">Calculate</Button>
            {zFactor && <div className="mt-4 p-4 bg-primary/10 rounded text-center font-bold text-xl">Z = {zFactor.toFixed(4)}</div>}
          </CardContent>
        </Card>
        <Card className="md:col-span-2 min-h-[400px]">
          <CardHeader><CardTitle>Z-Factor vs Pressure ({pressureLabel})</CardTitle></CardHeader>
          <CardContent className="h-full pb-12">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="p" label={{ value: pressureLabel, position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Z-factor', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="monotone" dataKey="z" stroke="#8884d8" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
