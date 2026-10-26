import React, { useState, useMemo } from "react";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { calculateEconomics, EconomicsInput } from "@/lib/reservoirMath";
import { DollarSign, TrendingUp, Calculator, ArrowUpRight, ArrowDownRight, RefreshCw } from "lucide-react";

export default function EconomicsView() {
  const [oilPrice, setOilPrice] = useState<number>(75);
  const [opex, setOpex] = useState<number>(18);
  const [capex, setCapex] = useState<number>(2500000);
  const [discountRate, setDiscountRate] = useState<number>(10); // percentage
  const [productionProfileStr, setProductionProfileStr] = useState<string>(
    "120000, 105000, 92000, 80000, 70000, 61000, 53000, 46000, 40000, 35000"
  );

  const results = useMemo(() => {
    const profile = productionProfileStr
      .split(",")
      .map((s) => parseFloat(s.trim()))
      .filter((v) => !isNaN(v) && v > 0);

    return calculateEconomics({
      oilPrice,
      opex,
      capex,
      discountRate: discountRate / 100,
      productionProfile: profile.length ? profile : [100000],
    });
  }, [oilPrice, opex, capex, discountRate, productionProfileStr]);

  const chartData = useMemo(() => {
    return results.cashFlows.map((flow, idx) => ({
      year: idx === 0 ? "Ano 0 (CAPEX)" : `Ano ${idx}`,
      fluxoAnual: flow,
      acumulado: results.cumCashFlows[idx],
    }));
  }, [results]);

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(val);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <DollarSign className="w-6 h-6 text-primary" />
            Avaliação Econômica e Análise de Reservas
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Fluxo de caixa descontado, VPL (NPV), Taxa Interna de Retorno (TIR/IRR), Payback e sensibilidade ao preço do barril.
          </p>
        </div>
        <Badge
          variant="outline"
          className={`text-sm px-3 py-1 font-semibold ${
            results.npv >= 0
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
              : "bg-destructive/10 border-destructive/30 text-destructive"
          }`}
        >
          {results.npv >= 0 ? "Projeto Economicamente Viável" : "VPL Negativo"}
        </Badge>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium text-muted-foreground">Valor Presente Líquido (VPL)</p>
            {results.npv >= 0 ? (
              <ArrowUpRight className="w-4 h-4 text-emerald-500" />
            ) : (
              <ArrowDownRight className="w-4 h-4 text-rose-500" />
            )}
          </div>
          <p className={`text-2xl font-bold mt-1 font-mono ${results.npv >= 0 ? "text-primary" : "text-destructive"}`}>
            {formatCurrency(results.npv)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Taxa de desconto: {discountRate}% a.a.</p>
        </Card>

        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">Taxa Interna de Retorno (TIR / IRR)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {results.irr}%
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Spread sobre hurdle: +{(results.irr - discountRate).toFixed(1)}%</p>
        </Card>

        <Card className="p-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-xs font-medium text-muted-foreground">Tempo de Payback (Retorno)</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
            {results.paybackYears > 0 ? `${results.paybackYears} anos` : "> 10 anos"}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Ponto de equilíbrio acumulado</p>
        </Card>

        <Card className="p-4 bg-purple-500/5 border-purple-500/20">
          <p className="text-xs font-medium text-muted-foreground">Retorno s/ Investimento (ROI)</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {results.roi}%
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">Receita total líquida de custos</p>
        </Card>
      </div>

      {/* Grid Inputs + Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Parâmetros Econômicos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="econ-price">Preço do Barril de Óleo (US$ / bbl)</Label>
              <Input
                id="econ-price"
                type="number"
                value={oilPrice}
                onChange={(e) => setOilPrice(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="econ-opex">Custo Operacional OPEX (US$ / bbl)</Label>
              <Input
                id="econ-opex"
                type="number"
                value={opex}
                onChange={(e) => setOpex(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="econ-capex">Investimento Inicial CAPEX (US$)</Label>
              <Input
                id="econ-capex"
                type="number"
                step="100000"
                value={capex}
                onChange={(e) => setCapex(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="econ-disc">Taxa Mínima de Atratividade - TMA (%)</Label>
              <Input
                id="econ-disc"
                type="number"
                step="0.5"
                value={discountRate}
                onChange={(e) => setDiscountRate(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="econ-prof">Perfil Anual de Produção (bbl/ano, sep por vírgula)</Label>
              <Input
                id="econ-prof"
                value={productionProfileStr}
                onChange={(e) => setProductionProfileStr(e.target.value)}
              />
              <p className="text-[10px] text-muted-foreground">Volume previsto para 10 anos de operação</p>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setOilPrice(75);
                setOpex(18);
                setCapex(2500000);
                setDiscountRate(10);
                setProductionProfileStr("120000, 105000, 92000, 80000, 70000, 61000, 53000, 46000, 40000, 35000");
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Restaurar Parâmetros Base
            </Button>
          </CardContent>
        </Card>

        {/* Composed Cash Flow Chart */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Fluxo de Caixa Líquido e Acumulado</CardTitle>
            <Badge variant="outline" className="text-xs">Valores em USD</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[360px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 15, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="year" />
                  <YAxis
                    tickFormatter={(val) => `$${(val / 1000000).toFixed(1)}M`}
                    label={{ value: "Valor (Milhões USD)", angle: -90, position: "insideLeft", offset: 0 }}
                  />
                  <Tooltip
                    formatter={(val: any, name: any) => [formatCurrency(Number(val)), name]}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Bar dataKey="fluxoAnual" name="Fluxo de Caixa Anual" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Line
                    type="monotone"
                    dataKey="acumulado"
                    name="Fluxo de Caixa Acumulado"
                    stroke="#10b981"
                    strokeWidth={3}
                    dot={{ r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t text-xs text-muted-foreground">
              <div>
                <span className="font-semibold text-foreground">Receita Bruta Total: </span>
                {formatCurrency(results.grossRevenue)}
              </div>
              <div className="text-right">
                <span className="font-semibold text-foreground">OPEX Cumulativo: </span>
                {formatCurrency(results.totalOpex)}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
