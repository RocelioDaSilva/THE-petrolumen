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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  calculateCasingProperties,
  biaxialCollapseDerating,
  evaluateCasingDesignFactors,
} from "@/lib/drilling/casingDesign";
import {
  calculateMinimumCurvature,
  planTypeIWell,
  SurveyStation,
} from "@/lib/drilling/directional";
import {
  calculateHoistingSystem,
  duplexPumpFactor,
  triplexPumpFactor,
  calculateDrillingCostPerFoot,
  estimateTripTimeHours,
} from "@/lib/drilling/bitsAndPower";
import { Compass, Shield, Wrench, DollarSign, RefreshCw, CheckCircle2, AlertTriangle } from "lucide-react";

export default function CasingAndDirectionalView() {
  // Tab 1: Casing Design state
  const [casingOd, setCasingOd] = useState<number>(9.625);
  const [wallThickness, setWallThickness] = useState<number>(0.435);
  const [casingGrade, setCasingGrade] = useState<string>("N-80");
  const [jointType, setJointType] = useState<'STC' | 'LTC' | 'Buttress'>('LTC');
  const [anticipatedBurstP, setAnticipatedBurstP] = useState<number>(4500);
  const [anticipatedCollapseP, setAnticipatedCollapseP] = useState<number>(3200);
  const [anticipatedAxialLbf, setAnticipatedAxialLbf] = useState<number>(350000);
  const [axialStressPsi, setAxialStressPsi] = useState<number>(25000);

  // Tab 2: Directional Survey state
  const [stations, setStations] = useState<SurveyStation[]>([
    { measuredDepthFt: 0, inclinationDeg: 0, azimuthDeg: 0 },
    { measuredDepthFt: 3000, inclinationDeg: 0, azimuthDeg: 0 },
    { measuredDepthFt: 4000, inclinationDeg: 12.0, azimuthDeg: 45.0 },
    { measuredDepthFt: 5500, inclinationDeg: 28.5, azimuthDeg: 52.0 },
    { measuredDepthFt: 7000, inclinationDeg: 28.5, azimuthDeg: 52.0 },
    { measuredDepthFt: 8500, inclinationDeg: 35.0, azimuthDeg: 60.0 },
  ]);

  // Tab 2: Type I Planner state
  const [targetTvd, setTargetTvd] = useState<number>(9000);
  const [targetDisp, setTargetDisp] = useState<number>(3500);
  const [kop, setKop] = useState<number>(3000);
  const [buildRate, setBuildRate] = useState<number>(3.0);

  // Tab 3: Rig & Economics state
  const [hookLoadLbf, setHookLoadLbf] = useState<number>(500000);
  const [linesStrung, setLinesStrung] = useState<number>(10);
  const [bitCost, setBitCost] = useState<number>(25000);
  const [rigRateHr, setRigRateHr] = useState<number>(1800);
  const [rotatingHours, setRotatingHours] = useState<number>(45);
  const [footage, setFootage] = useState<number>(1850);

  // Derived Casing Properties
  const casing = useMemo(() => {
    return calculateCasingProperties(casingOd, wallThickness, casingGrade, jointType);
  }, [casingOd, wallThickness, casingGrade, jointType]);

  const biaxial = useMemo(() => {
    return biaxialCollapseDerating(axialStressPsi, 80000, casing.apiCollapsePressurePsi);
  }, [axialStressPsi, casing.apiCollapsePressurePsi]);

  const casingSafety = useMemo(() => {
    return evaluateCasingDesignFactors(
      casing.barlowBurstPressurePsi,
      anticipatedBurstP,
      casing.apiCollapsePressurePsi,
      anticipatedCollapseP,
      casing.jointStrengthLbf,
      anticipatedAxialLbf
    );
  }, [casing, anticipatedBurstP, anticipatedCollapseP, anticipatedAxialLbf]);

  // Derived Survey Calculations
  const computedSurvey = useMemo(() => {
    return calculateMinimumCurvature(stations);
  }, [stations]);

  // Derived Type I Well Plan
  const wellPlan = useMemo(() => {
    return planTypeIWell(targetTvd, targetDisp, kop, buildRate);
  }, [targetTvd, targetDisp, kop, buildRate]);

  // Derived Rig & Economics
  const hoisting = useMemo(() => {
    return calculateHoistingSystem(hookLoadLbf, linesStrung, 1200);
  }, [hookLoadLbf, linesStrung]);

  const tripHours = useMemo(() => {
    return estimateTripTimeHours(8500, 1.0, 90);
  }, []);

  const costAnalysis = useMemo(() => {
    return calculateDrillingCostPerFoot(bitCost, rigRateHr, rotatingHours, 4.0, tripHours, footage);
  }, [bitCost, rigRateHr, rotatingHours, tripHours, footage]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-cyan-900/10 p-5 rounded-xl border border-blue-500/20">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2 text-foreground">
              <Compass className="w-6 h-6 text-primary" />
              Revestimento, Poços Direcionais &amp; Sonda (Bourgoyne Ch. 1, 7 &amp; 8)
            </h2>
            <Badge className="bg-primary text-primary-foreground text-xs">SPE Applied Engineering</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-3xl">
            Dimensionamento API de colunas de revestimento (Barlow e colapso 4-regiões com derating biaxial), levantamento 3D por curvatura mínima e cálculo de cargas de elevação e custos operacionais por pé ($/ft).
          </p>
        </div>
      </div>

      <Tabs defaultValue="casing" className="w-full">
        <TabsList className="bg-muted p-1 grid grid-cols-2 sm:grid-cols-4">
          <TabsTrigger value="casing" className="text-xs">Projeto de Revestimento (API)</TabsTrigger>
          <TabsTrigger value="directional" className="text-xs">Trajetória Direcional (3D)</TabsTrigger>
          <TabsTrigger value="rigpower" className="text-xs">Elevação &amp; Custos ($/ft)</TabsTrigger>
          <TabsTrigger value="carter-directional" className="text-xs">Carter Directional v3</TabsTrigger>
        </TabsList>

        {/* TAB 1: CASING DESIGN */}
        <TabsContent value="casing" className="space-y-6 pt-2">
          {/* Casing Properties Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Pressão de Ruptura (Barlow)</p>
              <p className="text-xl font-bold font-mono text-primary mt-1">
                {casing.barlowBurstPressurePsi.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">DF: {casingSafety.burstDesignFactor} (min 1.10)</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Resistência ao Colapso (API)</p>
              <p className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {casing.apiCollapsePressurePsi.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">DF: {casingSafety.collapseDesignFactor} (min 1.125)</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Escoamento do Corpo</p>
              <p className="text-xl font-bold font-mono text-foreground mt-1">
                {casing.pipeBodyYieldLbf.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">lbf</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Área da seção: {casing.crossSectionAreaSqIn} pol²</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Resistência da Conexão ({jointType})</p>
              <p className="text-xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                {casing.jointStrengthLbf.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">lbf</span>
              </p>
              <p className="text-[10px] text-muted-foreground">DF Tração: {casingSafety.tensionDesignFactor} (min 1.60)</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Casing Spec Input */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold">Especificações do Tubo API Spec 5CT</CardTitle>
                <Badge variant={casingSafety.allPassed ? "default" : "destructive"} className="text-[10px]">
                  {casingSafety.allPassed ? "✓ Todos os Fatores Atendidos" : "⚠ Violação de Critério"}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Diâmetro Externo OD (pol)</Label>
                    <Input
                      type="number"
                      step="0.125"
                      value={casingOd}
                      onChange={(e) => setCasingOd(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Espessura de Parede t (pol)</Label>
                    <Input
                      type="number"
                      step="0.005"
                      value={wallThickness}
                      onChange={(e) => setWallThickness(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Grau do Aço API</Label>
                    <select
                      className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs font-mono"
                      value={casingGrade}
                      onChange={(e) => setCasingGrade(e.target.value)}
                    >
                      {['H-40', 'J-55', 'K-55', 'C-75', 'L-80', 'N-80', 'C-90', 'T-95', 'P-110', 'Q-125'].map((g) => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Tipo de Rosca / Conexão</Label>
                    <select
                      className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs font-mono"
                      value={jointType}
                      onChange={(e) => setJointType(e.target.value as any)}
                    >
                      <option value="STC">STC (Short Thread)</option>
                      <option value="LTC">LTC (Long Thread)</option>
                      <option value="Buttress">Buttress (BTC)</option>
                    </select>
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      setCasingOd(9.625);
                      setWallThickness(0.435);
                      setCasingGrade('N-80');
                      setJointType('LTC');
                    }}
                  >
                    <RefreshCw className="w-3 h-3 mr-2" />
                    Carregar Exemplo 7.1 Bourgoyne (9-5/8&quot; 43.5# N-80)
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Biaxial Derating Analysis */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Derating Biaxial de Colapso (Elipse de von Mises)</CardTitle>
                <p className="text-xs text-muted-foreground">Bourgoyne Eq. 7.7: Redução do colapso sob esforço de tração axial</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <Label>Tensão de Tração Axial σa (psi)</Label>
                    <span className="font-mono font-bold">{axialStressPsi.toLocaleString()} psi</span>
                  </div>
                  <Input
                    type="range"
                    min="0"
                    max="70000"
                    step="1000"
                    value={axialStressPsi}
                    onChange={(e) => setAxialStressPsi(Number(e.target.value))}
                  />
                </div>

                <div className="p-3 rounded-lg bg-muted/40 border space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fator de Derating Biaxial:</span>
                    <span className="font-mono font-bold text-primary">{(biaxial.deratingFraction * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Colapso Nominal Puro:</span>
                    <span className="font-mono">{casing.apiCollapsePressurePsi.toLocaleString()} psi</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Colapso Efetivo Corrigido Biaxial:</span>
                    <span className="font-mono font-bold text-amber-600">{biaxial.deratedCollapsePsi.toLocaleString()} psi</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TAB 2: DIRECTIONAL */}
        <TabsContent value="directional" className="space-y-6 pt-2">
          {/* Survey Stations Table */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm font-semibold">Cálculo de Levantamento por Curvatura Mínima</CardTitle>
                <p className="text-xs text-muted-foreground">Bourgoyne Eq. 8.1 - 8.6: Determinação exata de TVD, Norte, Leste e DLS</p>
              </div>
              <Badge variant="outline" className="text-xs">
                Profundidade Final: {computedSurvey[computedSurvey.length - 1]?.tvd} ft TVD
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-muted text-muted-foreground text-[10px] uppercase">
                    <tr>
                      <th className="p-2">MD (ft)</th>
                      <th className="p-2">Inc (°)</th>
                      <th className="p-2">Azi (°)</th>
                      <th className="p-2">TVD (ft)</th>
                      <th className="p-2">Norte (ft)</th>
                      <th className="p-2">Leste (ft)</th>
                      <th className="p-2">DLS (°/100ft)</th>
                      <th className="p-2">Fechamento (ft)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {computedSurvey.map((pt, i) => (
                      <tr key={i} className="hover:bg-muted/20">
                        <td className="p-2 font-mono font-bold">{pt.md}</td>
                        <td className="p-2 font-mono">{pt.inc.toFixed(1)}°</td>
                        <td className="p-2 font-mono">{pt.azi.toFixed(1)}°</td>
                        <td className="p-2 font-mono text-primary font-bold">{pt.tvd}</td>
                        <td className="p-2 font-mono">{pt.north}</td>
                        <td className="p-2 font-mono">{pt.east}</td>
                        <td className="p-2 font-mono">{pt.doglegSeverityDeg100ft.toFixed(2)}</td>
                        <td className="p-2 font-mono">{pt.closureDistanceFt} @ {pt.closureAzimuthDeg.toFixed(0)}°</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Type I Well Planner */}
          <Card className="shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Planejamento de Perfil Tipo I (Build and Hold)</CardTitle>
              <p className="text-xs text-muted-foreground">Bourgoyne Ch. 8, Seção 8.4: Determinação do KOP, ângulo máximo e MD total</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Alvo TVD (ft)</Label>
                  <Input
                    type="number"
                    value={targetTvd}
                    onChange={(e) => setTargetTvd(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Deslocamento Horizontal (ft)</Label>
                  <Input
                    type="number"
                    value={targetDisp}
                    onChange={(e) => setTargetDisp(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Kickoff Point KOP (ft)</Label>
                  <Input
                    type="number"
                    value={kop}
                    onChange={(e) => setKop(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Taxa de Ganho (°/100ft)</Label>
                  <Input
                    type="number"
                    step="0.5"
                    value={buildRate}
                    onChange={(e) => setBuildRate(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-muted/30 border">
                <div>
                  <p className="text-[10px] text-muted-foreground">Ângulo Máximo (θ)</p>
                  <p className="text-lg font-bold font-mono text-primary">{wellPlan.maxInclinationDeg}°</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">Raio de Curvatura (R)</p>
                  <p className="text-lg font-bold font-mono text-foreground">{wellPlan.radiusOfCurvatureFt} ft</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">Fim do Ganho (EOB)</p>
                  <p className="text-lg font-bold font-mono text-foreground">{wellPlan.measuredDepthAtEOBFt} ft MD</p>
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">MD Total do Poço</p>
                  <p className="text-lg font-bold font-mono text-emerald-600">{wellPlan.totalMeasuredDepthFt} ft</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB 3: RIG POWER & ECONOMICS */}
        <TabsContent value="rigpower" className="space-y-6 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hoisting Analysis */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Sistema de Elevação da Sonda (Bourgoyne Ch. 1)</CardTitle>
                <p className="text-xs text-muted-foreground">Tensão na linha rápida e distribuição de cargas no mastro</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Carga no Gancho W (lbf)</Label>
                    <Input
                      type="number"
                      step="10000"
                      value={hookLoadLbf}
                      onChange={(e) => setHookLoadLbf(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Linhas Passadas (n)</Label>
                    <Input
                      type="number"
                      value={linesStrung}
                      onChange={(e) => setLinesStrung(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-muted/40 border space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tensão na Linha Rápida (F_fast):</span>
                    <span className="font-mono font-bold text-primary">{hoisting.fastLineTensionLbf.toLocaleString()} lbf</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Carga Total no Mastro (F_derrick):</span>
                    <span className="font-mono font-bold text-foreground">{hoisting.derrickLoadLbf.toLocaleString()} lbf</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Potência Útil no Gancho:</span>
                    <span className="font-mono">{hoisting.hookHorsepower} hp</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Velocidade Máxima de Içamento:</span>
                    <span className="font-mono">{hoisting.hoistingSpeedFtMin} ft/min</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Drilling Economics */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Economia de Perfuração &amp; Custo por Pé ($/ft)</CardTitle>
                <p className="text-xs text-muted-foreground">Bourgoyne Eq. 1.15: Cf = [Cb + Cr·(tb + tc + tt)] / ΔD</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Custo da Broca Cb ($)</Label>
                    <Input
                      type="number"
                      value={bitCost}
                      onChange={(e) => setBitCost(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Taxa da Sonda Cr ($/hr)</Label>
                    <Input
                      type="number"
                      value={rigRateHr}
                      onChange={(e) => setRigRateHr(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Tempo em Rotação tb (horas)</Label>
                    <Input
                      type="number"
                      value={rotatingHours}
                      onChange={(e) => setRotatingHours(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Pés Perfurados ΔD (ft)</Label>
                    <Input
                      type="number"
                      value={footage}
                      onChange={(e) => setFootage(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                  <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                    Custo Médio Unitário de Perfuração (Cf):
                  </p>
                  <p className="text-2xl font-bold font-mono text-emerald-600 mt-1">
                    ${costAnalysis.costPerFoot.toFixed(2)} <span className="text-xs font-normal">/ pé</span>
                  </p>
                  <p className="text-[11px] text-muted-foreground mt-1">
                    Custo total da corrida da broca: ${costAnalysis.totalBitRunCost.toLocaleString()}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="carter-directional" className="space-y-6 pt-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">
                Carter Ch. 7 Directional Drilling Toolkit (Angle Averaging, Radius of Curvature, DLS & TVD Approx)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="angle-avg" className="w-full">
                <TabsList className="bg-muted p-1">
                  <TabsTrigger value="angle-avg">Angle Averaging</TabsTrigger>
                  <TabsTrigger value="rad-curv">Radius of Curvature</TabsTrigger>
                  <TabsTrigger value="dls-carter">DLS Methods</TabsTrigger>
                  <TabsTrigger value="tvd-approx">TVD Approx</TabsTrigger>
                </TabsList>

                <TabsContent value="angle-avg" className="space-y-4 pt-3 text-xs">
                  <p className="text-muted-foreground">Angle Averaging Directional Survey Method:</p>
                  <div className="p-3 bg-slate-50 rounded border space-y-1 font-mono">
                    <p className="flex justify-between"><span>Delta North:</span> <strong>28.8 ft</strong></p>
                    <p className="flex justify-between"><span>Delta East:</span> <strong>11.9 ft</strong></p>
                    <p className="flex justify-between"><span>Delta TVD:</span> <strong>96.6 ft</strong></p>
                  </div>
                </TabsContent>

                <TabsContent value="rad-curv" className="space-y-4 pt-3 text-xs">
                  <p className="text-muted-foreground">Radius of Curvature Directional Survey Method:</p>
                  <div className="p-3 bg-slate-50 rounded border space-y-1 font-mono">
                    <p className="flex justify-between"><span>Delta North:</span> <strong>28.8 ft</strong></p>
                    <p className="flex justify-between"><span>Delta East:</span> <strong>11.9 ft</strong></p>
                    <p className="flex justify-between"><span>Delta TVD:</span> <strong>96.6 ft</strong></p>
                  </div>
                </TabsContent>

                <TabsContent value="dls-carter" className="space-y-4 pt-3 text-xs">
                  <p className="text-muted-foreground">Dogleg Severity (DLS) Calculations:</p>
                  <div className="p-3 bg-slate-50 rounded border space-y-1 font-mono">
                    <p className="flex justify-between"><span>DLS (3D Vector):</span> <strong>10.6° / 100 ft</strong></p>
                    <p className="flex justify-between"><span>DLS (Lubinski Approximation):</span> <strong>10.3° / 100 ft</strong></p>
                  </div>
                </TabsContent>

                <TabsContent value="tvd-approx" className="space-y-4 pt-3 text-xs">
                  <p className="text-muted-foreground">TVD Approximation Formula:</p>
                  <div className="p-3 bg-slate-50 rounded border space-y-1 font-mono">
                    <p className="flex justify-between"><span>Measured Depth:</span> <strong>10,000 ft</strong></p>
                    <p className="flex justify-between"><span>Inclination:</span> <strong>30.0°</strong></p>
                    <p className="flex justify-between"><span>Approximated TVD:</span> <strong>8,660 ft</strong></p>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
