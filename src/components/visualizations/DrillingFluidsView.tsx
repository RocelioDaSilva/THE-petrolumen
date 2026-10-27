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
  BarChart,
  Bar,
} from "recharts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  calculateFannRheology,
  bariteRequired,
  weightUpFixedFinalVolume,
  apiWaterLossFrom75,
  spurtLossFromPlot,
  retortAnalysis,
  causticToRaisePH,
  sodaAshForCalcium,
  sappForCement,
  sodiumBicarbForCement,
  causticForMagnesium,
  shaleAdsorptivePressure,
} from "@/lib/drilling/fluids";
import { Droplet, Activity, FlaskConical, Scale, ShieldAlert, Sparkles, RefreshCw } from "lucide-react";

export default function DrillingFluidsView() {
  // Tab 1: Fann Rheology state
  const [theta600, setTheta600] = useState<number>(65);
  const [theta300, setTheta300] = useState<number>(40);
  const [theta200, setTheta200] = useState<number>(31);
  const [theta100, setTheta100] = useState<number>(20);
  const [theta6, setTheta6] = useState<number>(6);
  const [theta3, setTheta3] = useState<number>(4);

  // Tab 2: Weighting Up state
  const [initialVolBbl, setInitialVolBbl] = useState<number>(500);
  const [initialMWPpg, setInitialMWPpg] = useState<number>(10.0);
  const [targetMWPpg, setTargetMWPpg] = useState<number>(12.0);
  const [bariteDensityPpg, setBariteDensityPpg] = useState<number>(35.0);
  const [isFixedFinalVolume, setIsFixedFinalVolume] = useState<boolean>(false);

  // Tab 3: Filtration & Retort state
  const [v75Cm3, setV75Cm3] = useState<number>(4.2);
  const [vSpurtCm3, setVSpurtCm3] = useState<number>(1.0);
  const [mudWeightRetort, setMudWeightRetort] = useState<number>(12.0);
  const [waterVolPct, setWaterVolPct] = useState<number>(78);
  const [oilVolPct, setOilVolPct] = useState<number>(0);
  const [salinityPpm, setSalinityPpm] = useState<number>(15000);

  // Tab 4: Chemistry & Contaminants state
  const [systemVolBbl, setSystemVolBbl] = useState<number>(800);
  const [initialPH, setInitialPH] = useState<number>(8.5);
  const [targetPH, setTargetPH] = useState<number>(10.0);
  const [calciumContamMgL, setCalciumContamMgL] = useState<number>(400);
  const [shaleActivity, setShaleActivity] = useState<number>(0.85);
  const [mudActivity, setMudActivity] = useState<number>(0.92);

  // Derived rheology calculations
  const rheo = useMemo(() => {
    return calculateFannRheology(theta600, theta300, theta200, theta100, theta6, theta3);
  }, [theta600, theta300, theta200, theta100, theta6, theta3]);

  // Shear Stress vs Shear Rate Rheology Curve
  const rheologyPlotData = useMemo(() => {
    const points = [];
    for (let gamma = 50; gamma <= 1022; gamma += 50) {
      // Bingham Plastic: tau = tau_y + mu_p * gamma / 478.8 (in lbf/100ft2)
      const tauBingham = rheo.yieldPointLbf100ft2 + (rheo.plasticViscosityCp * gamma) / 478.8;
      // Power Law: tau = (K / 510) * (gamma)^n * 1.066
      const tauPowerLaw = (rheo.powerLawK / 510) * Math.pow(gamma, rheo.powerLawN) * 1.066;

      points.push({
        shearRate: gamma,
        bingham: Math.round(tauBingham * 10) / 10,
        powerLaw: Math.round(tauPowerLaw * 10) / 10,
      });
    }
    return points;
  }, [rheo]);

  // Derived weighting up calculations
  const weightUpNormal = useMemo(() => {
    return bariteRequired(initialVolBbl, initialMWPpg, targetMWPpg, bariteDensityPpg);
  }, [initialVolBbl, initialMWPpg, targetMWPpg, bariteDensityPpg]);

  const weightUpFixed = useMemo(() => {
    return weightUpFixedFinalVolume(initialVolBbl, initialMWPpg, targetMWPpg, bariteDensityPpg);
  }, [initialVolBbl, initialMWPpg, targetMWPpg, bariteDensityPpg]);

  // Filtration & Retort calculations
  const apiWaterLoss = useMemo(() => {
    return apiWaterLossFrom75(v75Cm3, vSpurtCm3);
  }, [v75Cm3, vSpurtCm3]);

  const retort = useMemo(() => {
    return retortAnalysis(mudWeightRetort, waterVolPct, oilVolPct, salinityPpm);
  }, [mudWeightRetort, waterVolPct, oilVolPct, salinityPpm]);

  // Chemistry treatments
  const causticGrams = useMemo(() => {
    return causticToRaisePH(systemVolBbl * 158.98, initialPH, targetPH);
  }, [systemVolBbl, initialPH, targetPH]);

  const sodaAshLb = useMemo(() => {
    return sodaAshForCalcium(calciumContamMgL, systemVolBbl);
  }, [calciumContamMgL, systemVolBbl]);

  const bicarbLb = useMemo(() => {
    return sodiumBicarbForCement(calciumContamMgL, systemVolBbl);
  }, [calciumContamMgL, systemVolBbl]);

  const adsorptivePressure = useMemo(() => {
    return shaleAdsorptivePressure(mudActivity, shaleActivity);
  }, [mudActivity, shaleActivity]);

  return (
    <div className="space-y-6">
      {/* Module Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-emerald-900/10 via-teal-900/10 to-blue-900/10 p-5 rounded-xl border border-emerald-500/20">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2 text-foreground">
              <FlaskConical className="w-6 h-6 text-emerald-500" />
              Engenharia de Fluidos de Perfuração (Bourgoyne Ch. 2)
            </h2>
            <Badge className="bg-emerald-600 text-white text-xs">SPE Textbook Series</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-3xl">
            Reologia rotacional Fann 35, modelos Bingham e Ostwald-de Waele, equações de mistura ideal para adensamento com baritina, ensaios de retorta/filtração e controle de contaminação química.
          </p>
        </div>
      </div>

      <Tabs defaultValue="rheology" className="w-full">
        <TabsList className="bg-muted p-1 grid grid-cols-2 lg:grid-cols-4">
          <TabsTrigger value="rheology" className="text-xs">
            Reologia Fann 35
          </TabsTrigger>
          <TabsTrigger value="weightup" className="text-xs">
            Adensamento com Baritina
          </TabsTrigger>
          <TabsTrigger value="filtration" className="text-xs">
            Filtração &amp; Retorta
          </TabsTrigger>
          <TabsTrigger value="chemistry" className="text-xs">
            Química &amp; Contaminação
          </TabsTrigger>
        </TabsList>

        {/* TAB 1: RHEOLOGY */}
        <TabsContent value="rheology" className="space-y-6 pt-2">
          {/* KPI Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Viscosidade Plástica (PV)</p>
              <p className="text-xl font-bold text-primary mt-1 font-mono">{rheo.plasticViscosityCp} <span className="text-xs font-normal text-muted-foreground">cP</span></p>
              <p className="text-[10px] text-muted-foreground">θ600 − θ300</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Limite de Escoamento (YP)</p>
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {rheo.yieldPointLbf100ft2} <span className="text-xs font-normal text-muted-foreground">lbf/100ft²</span>
              </p>
              <p className="text-[10px] text-muted-foreground">θ300 − PV</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Viscosidade Aparente (AV)</p>
              <p className="text-xl font-bold text-foreground mt-1 font-mono">
                {rheo.apparentViscosityCp} <span className="text-xs font-normal text-muted-foreground">cP</span>
              </p>
              <p className="text-[10px] text-muted-foreground">θ600 / 2</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Expoente de Fluxo (n)</p>
              <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">{rheo.powerLawN}</p>
              <p className="text-[10px] text-muted-foreground">Lei de Potência (n &lt; 1 pseudoplástico)</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Índice Consistência (K)</p>
              <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {rheo.powerLawK} <span className="text-xs font-normal text-muted-foreground">eq cP</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Ostwald-de Waele</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <Card className="lg:col-span-1 shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold">Leituras Viscosímetro Fann 35</CardTitle>
                <Badge variant="outline" className="text-[10px]">{rheo.flowBehavior}</Badge>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label htmlFor="fann-600" className="text-xs">θ600 (600 RPM)</Label>
                    <Input
                      id="fann-600"
                      type="number"
                      value={theta600}
                      onChange={(e) => setTheta600(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fann-300" className="text-xs">θ300 (300 RPM)</Label>
                    <Input
                      id="fann-300"
                      type="number"
                      value={theta300}
                      onChange={(e) => setTheta300(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fann-200" className="text-xs">θ200 (200 RPM)</Label>
                    <Input
                      id="fann-200"
                      type="number"
                      value={theta200}
                      onChange={(e) => setTheta200(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fann-100" className="text-xs">θ100 (100 RPM)</Label>
                    <Input
                      id="fann-100"
                      type="number"
                      value={theta100}
                      onChange={(e) => setTheta100(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fann-6" className="text-xs">θ6 (Gel Inicial 10s)</Label>
                    <Input
                      id="fann-6"
                      type="number"
                      value={theta6}
                      onChange={(e) => setTheta6(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fann-3" className="text-xs">θ3 (Gel Final 10min)</Label>
                    <Input
                      id="fann-3"
                      type="number"
                      value={theta3}
                      onChange={(e) => setTheta3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      setTheta600(65);
                      setTheta300(40);
                      setTheta200(31);
                      setTheta100(20);
                      setTheta6(6);
                      setTheta3(4);
                    }}
                  >
                    <RefreshCw className="w-3 h-3 mr-2" />
                    Carregar Exemplo 2.1 Bourgoyne (65 / 40)
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Rheology Flow Curve Chart */}
            <Card className="lg:col-span-2 shadow-sm">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-primary" />
                  Curva Reológica: Tensão de Cisalhamento vs Taxa de Deformação
                </CardTitle>
                <Badge variant="outline" className="text-[11px]">Bingham vs Power-Law</Badge>
              </CardHeader>
              <CardContent>
                <div className="h-[280px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={rheologyPlotData} margin={{ top: 5, right: 20, left: 0, bottom: 15 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis
                        dataKey="shearRate"
                        label={{ value: "Taxa de Cisalhamento γ̇ (s⁻¹)", position: "insideBottom", offset: -8 }}
                      />
                      <YAxis
                        label={{ value: "Tensão τ (lbf/100ft²)", angle: -90, position: "insideLeft", offset: 10 }}
                      />
                      <Tooltip />
                      <Legend verticalAlign="top" height={32} />
                      <Line
                        type="monotone"
                        dataKey="bingham"
                        name="Bingham Plastic (τ = τy + μp·γ̇)"
                        stroke="#2563eb"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="powerLaw"
                        name="Power Law (τ = K·γ̇ⁿ)"
                        stroke="#10b981"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TAB 2: WEIGHTING UP */}
        <TabsContent value="weightup" className="space-y-6 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Scale className="w-4 h-4 text-emerald-500" />
                  Parâmetros de Adensamento
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <Label htmlFor="wu-vol" className="text-xs">Volume do Sistema (bbl)</Label>
                  <Input
                    id="wu-vol"
                    type="number"
                    value={initialVolBbl}
                    onChange={(e) => setInitialVolBbl(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="wu-mw1" className="text-xs">Densidade Inicial ρ₁ (ppg)</Label>
                  <Input
                    id="wu-mw1"
                    type="number"
                    step="0.1"
                    value={initialMWPpg}
                    onChange={(e) => setInitialMWPpg(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="wu-mw2" className="text-xs">Densidade Alvo ρ₂ (ppg)</Label>
                  <Input
                    id="wu-mw2"
                    type="number"
                    step="0.1"
                    value={targetMWPpg}
                    onChange={(e) => setTargetMWPpg(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="wu-barite" className="text-xs">Densidade da Baritina ρB (ppg - Padrão 35.0)</Label>
                  <Input
                    id="wu-barite"
                    type="number"
                    step="0.1"
                    value={bariteDensityPpg}
                    onChange={(e) => setBariteDensityPpg(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      setInitialVolBbl(500);
                      setInitialMWPpg(10.0);
                      setTargetMWPpg(12.0);
                      setBariteDensityPpg(35.0);
                    }}
                  >
                    Carregar Exemplo 2.16 Bourgoyne (500 bbl, 10→12 ppg)
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results Comparison */}
            <div className="lg:col-span-2 space-y-4">
              <Card className="shadow-sm border-emerald-500/30 bg-emerald-500/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-emerald-700 dark:text-emerald-400">
                    Caso 1: Adensamento com Expansão de Volume (Volume Final Livre)
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Equação de Bourgoyne 2.22: B = 350·V₁·(ρ₂ − ρ₁) / (ρB − ρ₂)
                  </p>
                </CardHeader>
                <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Baritina Total</p>
                    <p className="text-lg font-bold font-mono text-foreground">
                      {weightUpNormal.bariteTotalLbm.toLocaleString()} <span className="text-xs font-normal">lbm</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Sacos Requeridos (100 lb)</p>
                    <p className="text-lg font-bold font-mono text-emerald-600">
                      {weightUpNormal.bariteSacksRequired} <span className="text-xs font-normal">sacos</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Aumento de Volume (ΔV)</p>
                    <p className="text-lg font-bold font-mono text-primary">
                      +{weightUpNormal.volumeIncreaseBbl} <span className="text-xs font-normal">bbl</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Volume Final</p>
                    <p className="text-lg font-bold font-mono text-foreground">
                      {weightUpNormal.finalVolumeBbl} <span className="text-xs font-normal">bbl</span>
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-sm border-blue-500/30 bg-blue-500/5">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-blue-700 dark:text-blue-400">
                    Caso 2: Adensamento com Volume Final Fixo em {initialVolBbl} bbl (Com Descarte)
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Equação de Bourgoyne 2.24: Descarte prévio de lama antiga para manter tanques no nível alvo.
                  </p>
                </CardHeader>
                <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Lama Antiga a Reter (V₁)</p>
                    <p className="text-lg font-bold font-mono text-foreground">
                      {weightUpFixed.initialMudToKeepBbl} <span className="text-xs font-normal">bbl</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Lama Antiga a Descartar</p>
                    <p className="text-lg font-bold font-mono text-amber-600">
                      {weightUpFixed.oldMudToDiscardBbl} <span className="text-xs font-normal">bbl</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Baritina Necessária</p>
                    <p className="text-lg font-bold font-mono text-foreground">
                      {weightUpFixed.bariteTotalLbm.toLocaleString()} <span className="text-xs font-normal">lbm</span>
                    </p>
                  </div>
                  <div className="p-2.5 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Sacos Requeridos</p>
                    <p className="text-lg font-bold font-mono text-blue-600">
                      {weightUpFixed.sacks} <span className="text-xs font-normal">sacos</span>
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* TAB 3: FILTRATION & RETORT */}
        <TabsContent value="filtration" className="space-y-6 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Filter Press Analysis */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Ensaio de Filtração Estática (API Filter Press)</CardTitle>
                <p className="text-xs text-muted-foreground">Extrapolação de perda de filtrado de 7.5 min para 30 min (Bourgoyne Eq. 2.7)</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label htmlFor="fp-75" className="text-xs">Filtrado aos 7.5 min (cm³)</Label>
                    <Input
                      id="fp-75"
                      type="number"
                      step="0.1"
                      value={v75Cm3}
                      onChange={(e) => setV75Cm3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="fp-spurt" className="text-xs">Spurt Loss Inicial Vsp (cm³)</Label>
                    <Input
                      id="fp-spurt"
                      type="number"
                      step="0.1"
                      value={vSpurtCm3}
                      onChange={(e) => setVSpurtCm3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-muted/30 border space-y-2">
                  <p className="text-xs font-semibold text-foreground">Perda de Água API Calculada aos 30 minutos:</p>
                  <p className="text-2xl font-bold font-mono text-primary">
                    {apiWaterLoss} <span className="text-sm font-normal text-muted-foreground">cm³ (mL)</span>
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Fórmula padrão API: V₃₀ = 2·(V₇.₅ − V_sp) + V_sp
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Retort Analysis */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Análise de Retorta (Balanço de Sólidos e Líquidos)</CardTitle>
                <p className="text-xs text-muted-foreground">Divisão entre Sólidos de Baixa Densidade (LGS) e Baritina (Bourgoyne Eq. 2.18 - 2.21)</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-1">
                    <Label className="text-[11px]">Densidade (ppg)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={mudWeightRetort}
                      onChange={(e) => setMudWeightRetort(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% Água (vol)</Label>
                    <Input
                      type="number"
                      value={waterVolPct}
                      onChange={(e) => setWaterVolPct(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% Óleo (vol)</Label>
                    <Input
                      type="number"
                      value={oilVolPct}
                      onChange={(e) => setOilVolPct(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded bg-muted/40 border">
                    <p className="text-[10px] text-muted-foreground">Frações Volumétricas Totais</p>
                    <p className="text-xs font-mono mt-1">
                      Água: <span className="font-bold">{(retort.waterFraction * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-xs font-mono">
                      Óleo: <span className="font-bold">{(retort.oilFraction * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-xs font-mono">
                      Sólidos Totais: <span className="font-bold text-primary">{(retort.totalSolidsFraction * 100).toFixed(1)}%</span>
                    </p>
                  </div>

                  <div className="p-3 rounded bg-muted/40 border">
                    <p className="text-[10px] text-muted-foreground">Fracionamento dos Sólidos</p>
                    <p className="text-xs font-mono">
                      Baritina: <span className="font-bold text-emerald-600">{(retort.bariteFraction * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-xs font-mono">
                      LGS (Argilas/Broca): <span className="font-bold text-amber-600">{(retort.lowGravitySolidsFraction * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-xs font-mono">
                      Gravidade Média: <span className="font-bold">{retort.averageSolidsSpecificGravity} SG</span>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TAB 4: CHEMISTRY & CONTAMINANTS */}
        <TabsContent value="chemistry" className="space-y-6 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* pH & Caustic Soda Treatment */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Controle de pH &amp; Alcalinidade (NaOH)</CardTitle>
                <p className="text-xs text-muted-foreground">Exemplo 2.2 Bourgoyne: soda cáustica para ajuste de pH do sistema</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Vol. Sistema (bbl)</Label>
                    <Input
                      type="number"
                      value={systemVolBbl}
                      onChange={(e) => setSystemVolBbl(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">pH Inicial</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={initialPH}
                      onChange={(e) => setInitialPH(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">pH Alvo</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={targetPH}
                      onChange={(e) => setTargetPH(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                  <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                    Soda Cáustica (NaOH) 100% Requerida:
                  </p>
                  <p className="text-xl font-bold font-mono text-emerald-600 mt-1">
                    {causticGrams.toLocaleString()} g <span className="text-xs font-normal">({(causticGrams / 1000).toFixed(2)} kg)</span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Contamination Treatment */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Tratamento de Contaminação Química</CardTitle>
                <p className="text-xs text-muted-foreground">Remoção de Cálcio (gesso/anidrita/cimento) via Carbonato de Sódio / Bicarbonato</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs">Excesso de Cálcio Contaminante (mg/L Ca²⁺)</Label>
                  <Input
                    type="number"
                    value={calciumContamMgL}
                    onChange={(e) => setCalciumContamMgL(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="p-3 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Tratamento com Barrilha (Soda Ash)</p>
                    <p className="text-base font-bold font-mono text-foreground mt-0.5">
                      {sodaAshLb} <span className="text-xs font-normal">lbm</span>
                    </p>
                    <p className="text-[10px] text-muted-foreground">Recomendado para gesso/anidrita</p>
                  </div>

                  <div className="p-3 rounded bg-card border">
                    <p className="text-[10px] text-muted-foreground">Tratamento com Bicarbonato de Sódio</p>
                    <p className="text-base font-bold font-mono text-foreground mt-0.5">
                      {bicarbLb} <span className="text-xs font-normal">lbm</span>
                    </p>
                    <p className="text-[10px] text-muted-foreground">Recomendado para contaminação por cimento</p>
                  </div>
                </div>

                {/* Shale Adsorptive Pressure */}
                <div className="p-3 rounded-lg bg-muted/40 border text-xs space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-foreground">Pressão Adsortiva de Xisto (Bourgoyne Eq. 2.42):</span>
                    <span className="font-mono font-bold text-primary">{adsorptivePressure} psi</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    Atividade da lama: {mudActivity} vs Atividade do xisto: {shaleActivity}.
                    {adsorptivePressure > 0
                      ? " Fluxo osmótico de água da lama para o xisto (tendência de inchamento/desestabilização)."
                      : " Fluxo osmótico retira água do xisto (estabilização por desidratação osmótica)."}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
