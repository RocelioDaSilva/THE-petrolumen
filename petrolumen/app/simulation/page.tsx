'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function SimulationPage() {
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runSim = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/api/v1/gaia/simulation/run-oil-water`, {
        nx: 10, ny: 1, dx: 100, dy: 100, dz: 20, dt: 10.0, n_steps: 20,
        wells: [{ cell_index: 0, q_total: -500, type: 'rate' }] // Producer at block 0
      });
      setResults(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const chartData = results ? results.time.map((t: number, i: number) => ({
    time: t,
    pressure: results.pressure[i][5] // Middle of reservoir
  })) : [];

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Reservoir Simulation</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader><CardTitle>1D IMPES Model</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">10 blocks, 200 days simulation, 500 bbl/d production.</p>
            <Button onClick={runSim} disabled={loading}>{loading ? 'Running...' : 'Run Simulation'}</Button>
          </CardContent>
        </Card>
        <Card className="md:col-span-2 min-h-[400px]">
          <CardHeader><CardTitle>Pressure at Block 5</CardTitle></CardHeader>
          <CardContent className="h-full pb-12">
            {results ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" label={{ value: 'Time (days)', position: 'insideBottom', offset: -5 }} />
                  <YAxis domain={['auto', 'auto']} label={{ value: 'Pressure (psia)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="pressure" stroke="#2563eb" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : <div className="flex items-center justify-center h-full text-muted-foreground">Run simulation to see results</div>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
