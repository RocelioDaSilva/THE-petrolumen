'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AIPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trainModel = async () => {
    setLoading(true);
    setError(null);
    try {
      // Mock data for training
      const records = Array.from({ length: 50 }, (_, i) => ({
        time: i,
        cum_prod: i * 100,
        pressure: 3000 - i * 10,
        oil_rate: 1000 - i * 5 + Math.random() * 10
      }));

      const res = await axios.post(`${API_URL}/api/v1/gaia/ai/train`, {
        records,
        target: 'oil_rate',
        features: ['time', 'cum_prod', 'pressure']
      });
      setData(res.data);
    } catch (err: any) {
      setError(err.message || 'Training failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8">
      <h1 className="text-3xl font-bold">AI Production Prediction</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <Card>
          <CardHeader><CardTitle>Model Training</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">Train XGBoost and SVR models on historical data.</p>
            <Button onClick={trainModel} disabled={loading} className="w-full">
              {loading ? 'Training Models...' : 'Train Models'}
            </Button>
            {error && (
              <Alert variant="destructive">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error} <Button variant="link" onClick={trainModel} className="p-0 h-auto">Retry</Button></AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-2 min-h-[400px]">
          <CardHeader><CardTitle>Training Results</CardTitle></CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-[90%]" />
                <Skeleton className="h-20 w-full" />
              </div>
            ) : data ? (
              <div className="space-y-6">
                <div className="p-4 bg-primary/10 rounded-lg">
                  <p className="text-sm font-medium">Best Model</p>
                  <p className="text-2xl font-bold uppercase">{data.best_model}</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 border rounded">
                    <p className="text-sm text-muted-foreground">R² Score</p>
                    <p className="text-xl font-bold">{data.metrics.r2.toFixed(4)}</p>
                  </div>
                  <div className="p-4 border rounded">
                    <p className="text-sm text-muted-foreground">RMSE</p>
                    <p className="text-xl font-bold">{data.metrics.rmse.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-2">
                <p>No model trained yet.</p>
                <p className="text-sm">Click &quot;Train Models&quot; to start the process.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
