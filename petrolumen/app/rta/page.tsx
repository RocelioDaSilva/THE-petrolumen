'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function RTAPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runRTA = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/v1/gaia/rta/fmb-gas`, {
        pwf: [3000, 2800, 2600, 2400, 2200],
        gp: [0, 100, 250, 450, 700],
        pi: 3200,
        tf: 160,
        gamma_g: 0.65
      });
      setData(response.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data ? data.data.Gp.map((gp: number, i: number) => ({
    gp,
    pz: data.data.pz[i]
  })) : [];

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Rate Transient Analysis (FMB Gas)</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>RTA Inputs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Using sample historical production and pressure data.</p>
            <Button onClick={runRTA} disabled={loading} className="w-full">
              {loading ? 'Analyzing...' : 'Run FMB Gas'}
            </Button>
            {error && <p className="text-red-500 text-sm">{error}</p>}
          </CardContent>
        </Card>

        <Card className="md:col-span-2 h-[500px]">
          <CardHeader>
            <CardTitle>Flowing Material Balance Plot</CardTitle>
          </CardHeader>
          <CardContent className="h-full pb-12">
            {data ? (
              <div className="h-full space-y-4">
                <div className="p-4 bg-secondary rounded-lg inline-block">
                  <p className="text-sm font-medium">Estimated OGIP</p>
                  <p className="text-2xl font-bold">{data.ogip.toLocaleString()} MMscf</p>
                </div>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="gp" label={{ value: 'Gp (MMscf)', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'P/Z (psia)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="pz" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Click &quot;Run FMB Gas&quot; to perform analysis
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
