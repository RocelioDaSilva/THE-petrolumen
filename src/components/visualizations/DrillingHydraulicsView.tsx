import React, { useState, useMemo } from "react";
import {
  LineChart,
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
import {
  calculateHydraulics,
  generateLOTCurve,
  HydraulicsInputs,
} from "@/lib/drillingMath";
import {
  Zap,
  Activity,
  Gauge,
  Droplets,
  Layers,
  ArrowRight,
  RefreshCw,
  Sliders,
  CheckCircle,
} from "lucide-react";

export default function DrillingHydraulicsView() {
  // Hydraulics Inputs
  const [mudWeight, setMudWeight] = useState<number>(11.5); // ppg
  const [flowRate, setFlowRate] = useState<number>(550); // gpm
  const [tvd, setTvd] = useState<number>(9500); // ft
  const [nozzle1, setNozzle1] = useState<number>(13); // 32nds
  const [nozzle2, setNozzle2] = useState<number>(13);
  const [nozzle3, setNozzle3] = useState<number>(13);
  const [plasticViscosity, setPlasticViscosity] = useState<number>(18); // cP
  const [yieldPoint, setYieldPoint] = useState<number>(14); // lb/100 ft2
  const [drillPipeOd, setDrillPipeOd] = useState<number>(5.0); // in
  const [holeDiameter, setHoleDiameter] = useState<number>(8.5); // in

  // LOT parameters
  const [shoeTvd, setShoeTvd] = useState<number>(7200); // ft
  const [leakOffPressure, setLeakOffPressure] = useState<number>(1650); // psi

  // Calculations
  const hydraulics = useMemo(() => {
    return calculateHydraulics({
      mudWeight,
      flowRate,
      tvd,
      md: tvd * 1.05,
      nozzleSizes: [nozzle1, nozzle2, nozzle3],
      plasticViscosity,
      yieldPoint,
      drillPipeOd,
      holeDiameter,
    });
  }, [
    mudWeight,
    flowRate,
    tvd,
    nozzle1,
    nozzle2,
    nozzle3,
    plasticViscosity,
    yieldPoint,
    drillPipeOd,
    holeDiameter,
  ]);

  const lotData = useMemo(() => {
    return generateLOTCurve(shoeTvd, mudWeight, leakOffPressure);
  }, [shoeTvd, mudWeight, leakOffPressure]);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Zap className="w-6 h-6 text-amber-500" />
            <h2 className="text-2xl font-bold tracking-tight">
              Hidráulica de Perfuração, ECD & Teste de Absorção (LOT/FIT)
            </h2>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Otimização de jatos na broca (TFA, HHP, JIF), perda de carga anular por Bingham Plastic, densidade equivalente de circulação e integridade de formação.
          </p>
        </div>
        <Badge variant="outline" className="text-xs px-3 py-1 bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400 font-semibold">
          ECD Dinâmico: {hydraulics.ecd} ppg (+{(hydraulics.ecd - mudWeight).toFixed(2)} ppg)
        </Badge>
      </div>

      {/* Primary KPI Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="p-3 bg-amber-500/5 border-amber-500/20">
          <p className="text-[11px] font-medium text-muted-foreground">Área Total Jatos (TFA)</p>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
            {hydraulics.tfa} <span className="text-xs font-normal">pol²</span>
          </p>
          <p className="text-[10px] text-muted-foreground">{nozzle1}-{nozzle2}-{nozzle3} / 32"</p>
        </Card>

        <Card className="p-3 bg-blue-500/5 border-blue-500/20">
          <p className="text-[11px] font-medium text-muted-foreground">Queda Pressão Broca</p>
          <p className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
            {hydraulics.bitPressureDrop} <span className="text-xs font-normal">psi</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Velocidade: {hydraulics.bitVelocity} ft/s</p>
        </Card>

        <Card className="p-3 bg-primary/5 border-primary/20">
          <p className="text-[11px] font-medium text-muted-foreground">Potência Hidráulica (HHP)</p>
          <p className="text-xl font-bold text-primary mt-1 font-mono">
            {hydraulics.bitHydraulicHorsepower} <span className="text-xs font-normal">HP</span>
          </p>
          <p className="text-[10px] text-muted-foreground">{hydraulics.hhpPerSquareInch} HHP/pol² broca</p>
        </Card>

        <Card className="p-3 bg-purple-500/5 border-purple-500/20">
          <p className="text-[11px] font-medium text-muted-foreground">Força de Impacto (JIF)</p>
          <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {hydraulics.jetImpactForce} <span className="text-xs font-normal">lbf</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Limpeza de fundo do poço</p>
        </Card>

        <Card className="p-3 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-[11px] font-medium text-muted-foreground">Limpeza do Poço (CCI)</p>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {hydraulics.carryingCapacityIndex}
          </p>
          <p className="text-[10px] text-muted-foreground">Transporte: {hydraulics.cuttingsTransportRatio}%</p>
        </Card>

        <Card className="p-3 bg-rose-500/5 border-rose-500/20">
          <p className="text-[11px] font-medium text-muted-foreground">LOT Sapata EMW</p>
          <p className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1 font-mono">
            {lotData.lotEmw} <span className="text-xs font-normal">ppg</span>
          </p>
          <p className="text-[10px] text-muted-foreground">P_leak: {leakOffPressure} psi</p>
        </Card>
      </div>

      {/* Main Grid: Parameters vs LOT Test Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Sliders className="w-4 h-4 text-primary" />
              Parâmetros Operacionais de Perfuração
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3.5 text-xs">
            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="hyd-mw">Densidade Lama (ppg)</Label>
                <Input
                  id="hyd-mw"
                  type="number"
                  step="0.1"
                  value={mudWeight}
                  onChange={(e) => setMudWeight(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="hyd-q">Vazão de Bombeio (gpm)</Label>
                <Input
                  id="hyd-q"
                  type="number"
                  step="25"
                  value={flowRate}
                  onChange={(e) => setFlowRate(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="space-y-1">
              <Label>Jatos da Broca (tamanhos em 32 avos de pol)</Label>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <Input
                    type="number"
                    value={nozzle1}
                    onChange={(e) => setNozzle1(Number(e.target.value))}
                  />
                  <span className="text-[10px] text-muted-foreground block text-center mt-0.5">Jato 1</span>
                </div>
                <div>
                  <Input
                    type="number"
                    value={nozzle2}
                    onChange={(e) => setNozzle2(Number(e.target.value))}
                  />
                  <span className="text-[10px] text-muted-foreground block text-center mt-0.5">Jato 2</span>
                </div>
                <div>
                  <Input
                    type="number"
                    value={nozzle3}
                    onChange={(e) => setNozzle3(Number(e.target.value))}
                  />
                  <span className="text-[10px] text-muted-foreground block text-center mt-0.5">Jato 3</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="hyd-pv">Viscosidade Plástica (cP)</Label>
                <Input
                  id="hyd-pv"
                  type="number"
                  value={plasticViscosity}
                  onChange={(e) => setPlasticViscosity(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="hyd-yp">Yield Point (lb/100ft²)</Label>
                <Input
                  id="hyd-yp"
                  type="number"
                  value={yieldPoint}
                  onChange={(e) => setYieldPoint(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div className="space-y-1">
                <Label htmlFor="hyd-hole">Diâmetro Poço (pol)</Label>
                <Input
                  id="hyd-hole"
                  type="number"
                  step="0.125"
                  value={holeDiameter}
                  onChange={(e) => setHoleDiameter(Number(e.target.value))}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="hyd-dp">OD Tubo Perfuração (pol)</Label>
                <Input
                  id="hyd-dp"
                  type="number"
                  step="0.5"
                  value={drillPipeOd}
                  onChange={(e) => setDrillPipeOd(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="pt-2 border-t space-y-2">
              <p className="font-semibold text-muted-foreground uppercase text-[10px]">
                Parâmetros do Teste de Absorção (LOT)
              </p>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label htmlFor="lot-shoe">TVD Sapata (ft)</Label>
                  <Input
                    id="lot-shoe"
                    type="number"
                    value={shoeTvd}
                    onChange={(e) => setShoeTvd(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="lot-leak">P_leak Superfície (psi)</Label>
                  <Input
                    id="lot-leak"
                    type="number"
                    value={leakOffPressure}
                    onChange={(e) => setLeakOffPressure(Number(e.target.value))}
                  />
                </div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setMudWeight(11.5);
                setFlowRate(550);
                setTvd(9500);
                setNozzle1(13);
                setNozzle2(13);
                setNozzle3(13);
                setPlasticViscosity(18);
                setYieldPoint(14);
                setShoeTvd(7200);
                setLeakOffPressure(1650);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Restaurar Parâmetros Base
            </Button>
          </CardContent>
        </Card>

        {/* Charts & Diagnostics Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Leak-off test curve */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-rose-500" />
                  Curva do Teste de Absorção da Sapata (LOT Graph)
                </CardTitle>
                <p className="text-xs text-muted-foreground">
                  Pressão de superfície vs Volume bombeado na determinação do gradiente de fratura.
                </p>
              </div>
              <Badge variant="outline" className="text-xs font-mono">
                EMW Sapata = {lotData.lotEmw} ppg
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="h-[280px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={lotData.points} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="pumpedBbl"
                      label={{ value: "Volume Bombeado (bbl)", position: "insideBottom", offset: -10 }}
                    />
                    <YAxis
                      label={{ value: "Pressão de Superfície (psi)", angle: -90, position: "insideLeft", offset: 0 }}
                    />
                    <Tooltip formatter={(val: any) => [`${val} psi`, "Pressão"]} labelFormatter={(v) => `${v} bbl`} />
                    <Legend verticalAlign="top" height={36} />
                    <Line
                      type="monotone"
                      dataKey="pressure"
                      name="Pressão do Teste LOT (psi)"
                      stroke="#dc2626"
                      strokeWidth={2.5}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="p-3 bg-muted/40 rounded border text-xs text-muted-foreground mt-3 flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-foreground">Interpretação do Teste: </span>
                  O ponto de inflexão elástica (Leak-Off) ocorre aos {leakOffPressure} psi de superfície. A formação abaixo da sapata em {shoeTvd} ft suporta uma densidade equivalente de até <span className="font-bold text-foreground">{lotData.lotEmw} ppg</span> ({((lotData.lotEmw) * 0.052).toFixed(3)} psi/ft). O MAASP seguro operacional com a lama atual é de {lotData.maasp} psi.
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Hydraulics & Cleaning Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Card className="p-4 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                <Droplets className="w-3.5 h-3.5 text-blue-500" />
                Distribuição de Perdas de Carga
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Queda na Broca (ΔPb):</span>
                  <span className="font-mono font-bold text-primary">{hydraulics.bitPressureDrop} psi</span>
                </div>
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Perda de Carga no Anular (ΔPa):</span>
                  <span className="font-mono font-bold text-amber-600">{hydraulics.annularPressureLoss} psi</span>
                </div>
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Densidade Estática da Lama:</span>
                  <span className="font-mono font-bold">{mudWeight} ppg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ECD no Fundo (Dinâmico):</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">{hydraulics.ecd} ppg</span>
                </div>
              </div>
            </Card>

            <Card className="p-4 shadow-sm">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-500" />
                Eficiência de Transporte de Cascalhos
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Carrying Capacity Index (CCI):</span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    {hydraulics.carryingCapacityIndex} {hydraulics.carryingCapacityIndex >= 1 ? "(Excelente)" : "(Atenção)"}
                  </span>
                </div>
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Taxa de Transporte de Sólidos:</span>
                  <span className="font-mono font-bold">{hydraulics.cuttingsTransportRatio}%</span>
                </div>
                <div className="flex justify-between pb-1 border-b">
                  <span className="text-muted-foreground">Velocidade nos Jatos:</span>
                  <span className="font-mono font-bold">{hydraulics.bitVelocity} ft/s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Força de Impacto do Jato:</span>
                  <span className="font-mono font-bold">{hydraulics.jetImpactForce} lbf</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
