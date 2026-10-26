'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  BarChart,
} from 'recharts';
import {
  DollarSign,
  TrendingUp,
  Calculator,
  AlertCircle,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  BarChart3,
  Percent,
  Clock,
} from 'lucide-react';
import {
  evaluateEconomicsAdvanced,
  runEconomicsSensitivity,
  EconomicsEvaluateResponse,
  SensitivityResponse,
} from '@/lib/backendClient';

export function EconomicsDashboard() {
  // Input parameters state
  const [oilPrice, setOilPrice] = useState<number>(70);
  const [gasPrice, setGasPrice] = useState<number>(3.5);
  const [opexFixed, setOpexFixed] = useState<number>(1000);
  const [opexVarOil, setOpexVarOil] = useState<number>(5.0);
  const [capex, setCapex] = useState<number>(2000000);
  const [royaltyRate, setRoyaltyRate] = useState<number>(12.5); // %
  const [taxRate, setTaxRate] = useState<number>(21); // %
  const [discountRate, setDiscountRate] = useState<number>(10); // %
  const [productionProfileStr, setProductionProfileStr] = useState<string>(
    '10000, 9000, 8100, 7290, 6561, 5905, 5314, 4783, 4305, 3874, 3486, 3138'
  );

  // Status & Data states
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<EconomicsEvaluateResponse | null>(null);
  const [sensitivityData, setSensitivityData] = useState<SensitivityResponse | null>(null);
  const [activeTab, setActiveTab] = useState<string>('cashflow');

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = productionProfileStr
        .split(',')
        .map((s) => parseFloat(s.trim()))
        .filter((val) => !isNaN(val));

      if (profile.length === 0) {
        throw new Error('Please enter a valid non-empty production sequence.');
      }

      const evalReq = {
        forecast: {
          time: Array.from({ length: profile.length }, (_, i) => i + 1),
          oil_rate: profile,
          rates_are_daily: true,
        },
        capex: Number(capex),
        oil_price: Number(oilPrice),
        gas_price: Number(gasPrice),
        opex_fixed_monthly: Number(opexFixed),
        opex_var_oil: Number(opexVarOil),
        royalty_rate: Number(royaltyRate) / 100,
        income_tax_rate: Number(taxRate) / 100,
        discount_rate: Number(discountRate) / 100,
        period_frequency: 'monthly',
      };

      const evalRes = await evaluateEconomicsAdvanced(evalReq);
      setResults(evalRes);

      // Run Tornado Sensitivity
      try {
        const sensRes = await runEconomicsSensitivity({
          evaluate_request: evalReq,
          sensitivity_type: 'tornado',
          tornado_variation_pct: 20.0,
        });
        setSensitivityData(sensRes);
      } catch (sensErr) {
        console.warn('Sensitivity analysis failed:', sensErr);
      }
    } catch (err: any) {
      console.error('Economic Evaluation Error:', err);
      if (err?.message?.includes('Not authenticated') || err?.status === 401) {
        setError(null);
      } else {
        setError(err.message || 'Failed to evaluate economics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runEvaluation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const chartData = results
    ? results.cash_flow_periods.map((p) => ({
        period: p.period === 0 ? 'Month 0 (CAPEX)' : `M${p.period}`,
        netCashFlow: p.net_cash_flow,
        cumCashFlow: p.cumulative_net_cash_flow,
        cumDiscountedCF: p.cumulative_discounted_cash_flow,
      }))
    : [];

  const tornadoChartData = sensitivityData?.tornado_data
    ? sensitivityData.tornado_data.map((item) => ({
        parameter: item.label,
        lowNPV: item.low_npv,
        highNPV: item.high_npv,
        swing: item.swing,
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
    <div className="space-y-8 w-full">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Calculator className="w-8 h-8 text-primary" />
            Economics & Decision Analysis Engine
          </h1>
          <p className="text-muted-foreground mt-1">
            Perform Net Present Value (NPV), Internal Rate of Return (IRR), Payout, and Sensitivity Analyses for PetroLúmen development assets.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Economic Parameter Controls Form */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-primary" />
              Economic Parameters
            </CardTitle>
            <CardDescription>Input CAPEX, OPEX, Price Deck, and Discount assumptions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
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
                <Label htmlFor="gasPrice">Gas Price ($/Mcf)</Label>
                <Input
                  id="gasPrice"
                  type="number"
                  value={gasPrice}
                  onChange={(e) => setGasPrice(parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="capex">Initial CAPEX ($)</Label>
              <Input
                id="capex"
                type="number"
                value={capex}
                onChange={(e) => setCapex(parseFloat(e.target.value) || 0)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="opexFixed">Fixed OPEX ($/mo)</Label>
                <Input
                  id="opexFixed"
                  type="number"
                  value={opexFixed}
                  onChange={(e) => setOpexFixed(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="opexVar">Var. OPEX ($/bbl)</Label>
                <Input
                  id="opexVar"
                  type="number"
                  value={opexVarOil}
                  onChange={(e) => setOpexVarOil(parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-2">
                <Label htmlFor="royalty">Royalty (%)</Label>
                <Input
                  id="royalty"
                  type="number"
                  value={royaltyRate}
                  onChange={(e) => setRoyaltyRate(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="taxRate">Tax (%)</Label>
                <Input
                  id="taxRate"
                  type="number"
                  value={taxRate}
                  onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="discount">Discount (%)</Label>
                <Input
                  id="discount"
                  type="number"
                  value={discountRate}
                  onChange={(e) => setDiscountRate(parseFloat(e.target.value) || 0)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="productionProfile">Oil Production Profile (bbl/day)</Label>
              <Input
                id="productionProfile"
                value={productionProfileStr}
                onChange={(e) => setProductionProfileStr(e.target.value)}
                placeholder="10000, 9000, 8100..."
              />
              <p className="text-xs text-muted-foreground">Comma-separated rates per period/month.</p>
            </div>

            <Button onClick={runEvaluation} disabled={loading} className="w-full mt-4 flex items-center justify-center gap-2">
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Calculator className="w-4 h-4" />}
              {loading ? 'Evaluating...' : 'Run Economic Evaluation'}
            </Button>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
                <Button onClick={runEvaluation} size="sm" variant="outline" className="mt-2 text-xs">
                  Try Again
                </Button>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Results Metrics & Interactive Visualizations */}
        <div className="lg:col-span-2 space-y-6">
          {/* Key Indicators Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {/* NPV */}
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground">Net Present Value</p>
                {results && results.npv >= 0 ? (
                  <ArrowUpRight className="w-4 h-4 text-emerald-500" />
                ) : (
                  <ArrowDownRight className="w-4 h-4 text-rose-500" />
                )}
              </div>
              <div className="mt-2">
                {loading ? (
                  <Skeleton className="h-8 w-28" />
                ) : results ? (
                  <p
                    className={`text-2xl font-extrabold ${
                      results.npv >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                    }`}
                  >
                    {formatCurrency(results.npv)}
                  </p>
                ) : (
                  <p className="text-2xl font-extrabold text-muted-foreground">$0</p>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">@ {discountRate}% annual discount</p>
            </Card>

            {/* IRR */}
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground">Internal Rate of Return</p>
                <TrendingUp className="w-4 h-4 text-primary" />
              </div>
              <div className="mt-2">
                {loading ? (
                  <Skeleton className="h-8 w-24" />
                ) : results ? (
                  <p className="text-2xl font-extrabold text-primary">{formatPercent(results.irr)}</p>
                ) : (
                  <p className="text-2xl font-extrabold text-muted-foreground">0.00%</p>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Breakeven discount rate</p>
            </Card>

            {/* Payout Time */}
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground">Payout Time</p>
                <Clock className="w-4 h-4 text-amber-500" />
              </div>
              <div className="mt-2">
                {loading ? (
                  <Skeleton className="h-8 w-24" />
                ) : results ? (
                  <p className="text-2xl font-extrabold text-foreground">
                    {results.payout_months >= 0 ? `${results.payout_months.toFixed(1)} mo` : 'N/A'}
                  </p>
                ) : (
                  <p className="text-2xl font-extrabold text-muted-foreground">-</p>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">
                {results && results.payout_years >= 0 ? `(~${results.payout_years.toFixed(2)} yrs)` : 'Never pays out'}
              </p>
            </Card>

            {/* Profitability Index */}
            <Card className="p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-muted-foreground">Profitability Index</p>
                <Percent className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="mt-2">
                {loading ? (
                  <Skeleton className="h-8 w-20" />
                ) : results ? (
                  <p className="text-2xl font-extrabold text-indigo-600 dark:text-indigo-400">
                    {results.profitability_index.toFixed(2)}
                  </p>
                ) : (
                  <p className="text-2xl font-extrabold text-muted-foreground">0.00</p>
                )}
              </div>
              <p className="text-[10px] text-muted-foreground mt-1">Value created per CAPEX $</p>
            </Card>
          </div>

          {/* Tabbed Interactive Visualizations */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <CardTitle className="text-lg font-bold">Economic Forecast Visualizations</CardTitle>
                  <TabsList>
                    <TabsTrigger value="cashflow" className="flex items-center gap-1">
                      <BarChart3 className="w-4 h-4" />
                      Cash Flow Profile
                    </TabsTrigger>
                    <TabsTrigger value="sensitivity" className="flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      Tornado Sensitivity
                    </TabsTrigger>
                  </TabsList>
                </div>
              </Tabs>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsContent value="cashflow" className="space-y-4">
                  {loading ? (
                    <Skeleton className="h-80 w-full" />
                  ) : results ? (
                    <div className="h-80 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                          <XAxis dataKey="period" />
                          <YAxis
                            tickFormatter={(val) =>
                              `$${val >= 1e6 ? `${(val / 1e6).toFixed(1)}M` : `${(val / 1e3).toFixed(0)}k`}`
                            }
                          />
                          <Tooltip
                            formatter={(value: any) => [formatCurrency(Number(value)), '']}
                            contentStyle={{
                              backgroundColor: 'rgba(15, 23, 42, 0.9)',
                              color: '#fff',
                              borderRadius: '8px',
                            }}
                          />
                          <Legend />
                          <Bar dataKey="netCashFlow" name="Net Cash Flow ($)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                          <Line
                            type="monotone"
                            dataKey="cumDiscountedCF"
                            name="Cum. Discounted Cash Flow ($)"
                            stroke="#10b981"
                            strokeWidth={3}
                            dot={{ r: 4 }}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="h-80 flex items-center justify-center text-muted-foreground">
                      No economic evaluation results available.
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="sensitivity" className="space-y-4">
                  {loading ? (
                    <Skeleton className="h-80 w-full" />
                  ) : tornadoChartData.length > 0 ? (
                    <div className="space-y-4">
                      <p className="text-xs text-muted-foreground">
                        NPV Sensitivity to ±20% variation in key economic inputs. Longest bars represent the highest economic risk/leverage variables.
                      </p>
                      <div className="h-80 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={tornadoChartData} layout="vertical" margin={{ top: 10, right: 30, left: 40, bottom: 20 }}>
                            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                            <XAxis
                              type="number"
                              tickFormatter={(val) =>
                                `$${val >= 1e6 ? `${(val / 1e6).toFixed(1)}M` : `${(val / 1e3).toFixed(0)}k`}`
                              }
                            />
                            <YAxis type="category" dataKey="parameter" />
                            <Tooltip formatter={(val: any) => [formatCurrency(Number(val)), 'NPV Impact']} />
                            <Legend />
                            <Bar dataKey="lowNPV" name="-20% Parameter Shift NPV ($)" fill="#ef4444" />
                            <Bar dataKey="highNPV" name="+20% Parameter Shift NPV ($)" fill="#10b981" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  ) : (
                    <div className="h-80 flex items-center justify-center text-muted-foreground">
                      No sensitivity data available.
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
