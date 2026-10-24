'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { analyzeEconomics, EconomicsAnalyzeResponse } from '@/lib/backendClient';
import { DollarSign, TrendingUp, Calculator, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function EconomicsPage() {
  const [oilPrice, setOilPrice] = useState<number>(70);
  const [opex, setOpex] = useState<number>(20);
  const [capex, setCapex] = useState<number>(2000000);
  const [discountRate, setDiscountRate] = useState<number>(10); // percentage
  const [productionProfileStr, setProductionProfileStr] = useState<string>(
    '10000, 9000, 8100, 7290, 6561, 5905, 5314, 4783, 4305, 3874'
  );

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<EconomicsAnalyzeResponse | null>(null);

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = productionProfileStr
        .split(',')
        .map((s) => parseFloat(s.trim()))
        .filter((val) => !isNaN(val));

      if (profile.length === 0) {
        throw new Error('Please enter a valid production profile sequence.');
      }

      const res = await analyzeEconomics({
        production_profile: profile,
        oil_price: Number(oilPrice),
        opex: Number(opex),
        capex: Number(capex),
        discount_rate: Number(discountRate) / 100,
      });

      setResults(res);
    } catch (err: any) {
      console.error('Economics evaluation error:', err);
      if (err?.message?.includes('Not authenticated') || err?.status === 401) {
        setError(null);
      } else {
        setError(err.message || 'Failed to calculate economics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const chartData = results
    ? results.cumulative_cash_flow.map((cum, idx) => ({
        year: idx === 0 ? 'Year 0 (CAPEX)' : `Year ${idx}`,
        cashFlow: results.cash_flows[idx],
        cumulativeCashFlow: cum,
      }))
    : [];

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(val);

  const formatPercent = (val: number) => `${(val * 100).toFixed(2)}%`;

  return (
    <div className="container mx-auto py-8 px-4 space-y-8">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Calculator className="w-8 h-8 text-primary" />
            Economics Evaluation Engine
          </h1>
          <p className="text-muted-foreground mt-1">
            Perform Net Present Value (NPV), Internal Rate of Return (IRR), and Cash Flow Analysis for reservoir development decisions.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form Inputs */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-primary" />
              Economic Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="oilPrice">Oil Price ($/bbl)</Label>
              <Input
                id="oilPrice"
                type="number"
                value={oilPrice}
                onChange={(e) => setOilPrice(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="opex">OPEX ($/bbl)</Label>
              <Input
                id="opex"
                type="number"
                value={opex}
                onChange={(e) => setOpex(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="capex">CAPEX ($)</Label>
              <Input
                id="capex"
                type="number"
                value={capex}
                onChange={(e) => setCapex(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="discountRate">Discount Rate (%)</Label>
              <Input
                id="discountRate"
                type="number"
                value={discountRate}
                onChange={(e) => setDiscountRate(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="productionProfile">Production Profile (bbl / period)</Label>
              <Input
                id="productionProfile"
                value={productionProfileStr}
                onChange={(e) => setProductionProfileStr(e.target.value)}
                placeholder="10000, 9000, 8100..."
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated volumes for each period/year.
              </p>
            </div>

            <Button onClick={runAnalysis} disabled={loading} className="w-full mt-4">
              {loading ? 'Evaluating...' : 'Run Economic Analysis'}
            </Button>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results & Visualizations */}
        <div className="lg:col-span-2 space-y-8">
          {/* Key Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Net Present Value (NPV)</p>
                {results && results.npv >= 0 ? (
                  <ArrowUpRight className="w-5 h-5 text-emerald-500" />
                ) : (
                  <ArrowDownRight className="w-5 h-5 text-rose-500" />
                )}
              </div>
              <div className="mt-3">
                {loading ? (
                  <Skeleton className="h-9 w-36" />
                ) : results ? (
                  <p
                    className={`text-3xl font-extrabold ${
                      results.npv >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {formatCurrency(results.npv)}
                  </p>
                ) : (
                  <p className="text-3xl font-extrabold text-muted-foreground">$0</p>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Discounted at {discountRate}% annual rate
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">Internal Rate of Return (IRR)</p>
                <TrendingUp className="w-5 h-5 text-primary" />
              </div>
              <div className="mt-3">
                {loading ? (
                  <Skeleton className="h-9 w-28" />
                ) : results ? (
                  <p className="text-3xl font-extrabold text-primary">
                    {formatPercent(results.irr)}
                  </p>
                ) : (
                  <p className="text-3xl font-extrabold text-muted-foreground">0.00%</p>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Break-even return rate on CAPEX
              </p>
            </Card>
          </div>

          {/* Cash Flow Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-semibold">
                Cash Flow Profile & Cumulative Cash Flow
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-80 w-full" />
              ) : results ? (
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="year" />
                      <YAxis
                        tickFormatter={(val) =>
                          `$${val >= 1e6 ? `${(val / 1e6).toFixed(1)}M` : `${(val / 1e3).toFixed(0)}k`}`
                        }
                      />
                      <Tooltip
                        formatter={(value: any) => [formatCurrency(Number(value)), '']}
                        contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', color: '#fff', borderRadius: '8px' }}
                      />
                      <Legend />
                      <Bar dataKey="cashFlow" name="Net Period Cash Flow ($)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Line
                        type="monotone"
                        dataKey="cumulativeCashFlow"
                        name="Cumulative Cash Flow ($)"
                        stroke="#10b981"
                        strokeWidth={3}
                        dot={{ r: 4 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-80 flex items-center justify-center text-muted-foreground">
                  No evaluation results available.
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
