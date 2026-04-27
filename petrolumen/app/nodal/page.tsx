'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function NodalPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runNodal = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/v1/gaia/nodal/solve`, {
        p_res: 3000,
        q_max: 1500,
        p_wh: 500,
        depth: 8000
      });
      setData(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data ? data.curves.q.map((q: number, i: number) => ({
    q,
    p_ipr: data.curves.p_ipr[i],
    p_vlp: data.curves.p_vlp[i]
  })) : [];

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Nodal Analysis</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>System Parameters</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Reservoir Pressure: 3000 psia</p>
            <p className="text-sm text-muted-foreground">Wellhead Pressure: 500 psia</p>
            <Button onClick={runNodal} disabled={loading} className="w-full">
              {loading ? 'Solving...' : 'Solve Operating Point'}
            </Button>
            {error && <p className="text-red-500 text-sm">{error}</p>}
          </CardContent>
        </Card>

        <Card className="md:col-span-2 h-[500px]">
          <CardHeader>
            <CardTitle>IPR vs VLP Curves</CardTitle>
          </CardHeader>
          <CardContent className="h-full pb-12">
            {data ? (
              <div className="h-full space-y-4">
                <div className="p-4 bg-secondary rounded-lg inline-block">
                  <p className="text-sm font-medium">Operating Point</p>
                  <p className="text-2xl font-bold">
                    {data.operating_point.q.toFixed(1)} STB/d @ {data.operating_point.p.toFixed(1)} psia
                  </p>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="q" label={{ value: 'Rate (STB/d)', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Pressure (psia)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="p_ipr" name="IPR" stroke="#16a34a" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="p_vlp" name="VLP" stroke="#dc2626" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Solve system to visualize curves
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
