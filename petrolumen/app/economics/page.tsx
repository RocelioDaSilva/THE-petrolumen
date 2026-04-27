'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function EconomicsPage() {
  const [data, setData] = useState<any>(null);

  const runEcon = async () => {
    try {
      const res = await axios.post(`${API_URL}/api/v1/gaia/economics/run`, {
        forecast_time: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        forecast_rate: [1000, 980, 960, 940, 920, 900, 880, 860, 840, 820, 800, 780, 760],
        oil_price: 75,
        capex: 1000000,
        opex_fixed: 5000,
        opex_var: 5,
        discount_rate: 0.1
      });
      setData(res.data);
    } catch (e) { console.error(e); }
  };

  const chartData = data ? data.cum_cash_flow.map((val: number, i: number) => ({
    month: i,
    cumCF: val
  })) : [];

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">Economic Analysis</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader><CardTitle>Project Economics</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={runEcon}>Calculate Project NPV/IRR</Button>
            {data && (
              <div className="mt-4 space-y-2">
                <p className="font-bold">NPV: ${data.npv.toLocaleString(undefined, {maximumFractionDigits:0})}</p>
                <p className="font-bold">IRR: {(data.irr*100).toFixed(1)}%</p>
                <p className="font-bold">Payout: {data.payout_month} months</p>
              </div>
            )}
          </CardContent>
        </Card>
        <Card className="md:col-span-2">
          <CardHeader><CardTitle>Cumulative Cash Flow</CardTitle></CardHeader>
          <CardContent className="h-[300px] pb-8">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Cash Flow ($)', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line type="stepAfter" dataKey="cumCF" stroke="#16a34a" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
