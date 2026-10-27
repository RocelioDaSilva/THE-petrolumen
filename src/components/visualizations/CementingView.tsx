import React, { useState, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  designCementSlurry,
  planCementJob,
  bogueCompoundsFromOxides,
  recommendCementAdditives,
  additiveForTargetDensity,
} from "@/lib/drilling/cements";
import { Layers, Package, Clock, ShieldCheck, RefreshCw, Flame, CheckCircle2 } from "lucide-react";

export default function CementingView() {
  // Tab 1: Slurry Design state
  const [cementClass, setCementClass] = useState<'Class A' | 'Class C' | 'Class G' | 'Class H'>('Class G');
  const [bentonitePct, setBentonitePct] = useState<number>(0);
  const [hematitePct, setHematitePct] = useState<number>(0);

  // Tab 2: Job Volume & Time Planning state
  const [holeDia, setHoleDia] = useState<number>(12.25);
  const [casingOd, setCasingOd] = useState<number>(9.625);
  const [casingId, setCasingId] = useState<number>(8.681);
  const [intervalLen, setIntervalLen] = useState<number>(3000);
  const [shoeTrackLen, setShoeTrackLen] = useState<number>(80);
  const [excessFactor, setExcessFactor] = useState<number>(1.25); // 25%
  const [mixingRate, setMixingRate] = useState<number>(30); // sacks/min
  const [displacementRate, setDisplacementRate] = useState<number>(6.0); // bpm
  const [casingTotalLen, setCasingTotalLen] = useState<number>(8500);

  // Tab 3: Bogue Oxides state
  const [cao, setCao] = useState<number>(64.2);
  const [sio2, setSio2] = useState<number>(21.5);
  const [al2o3, setAl2o3] = useState<number>(5.2);
  const [fe2o3, setFe2o3] = useState<number>(3.0);
  const [so3, setSo3] = useState<number>(2.4);

  // Tab 3: Advisor inputs
  const [bhtF, setBhtF] = useState<number>(180);
  const [targetSlurryDensity, setTargetSlurryDensity] = useState<number>(15.8);
  const [waterSensitive, setWaterSensitive] = useState<boolean>(true);

  // Derived Slurry Design
  const slurry = useMemo(() => {
    const adds = [];
    if (bentonitePct > 0) {
      adds.push({
        name: 'Bentonite',
        pctByWeightOfCement: bentonitePct,
        specificGravity: 2.65,
        waterRequirementGalPerLb: 0.65,
      });
    }
    if (hematitePct > 0) {
      adds.push({
        name: 'Hematite',
        pctByWeightOfCement: hematitePct,
        specificGravity: 5.05,
        waterRequirementGalPerLb: 0.02,
      });
    }
    return designCementSlurry(cementClass, adds);
  }, [cementClass, bentonitePct, hematitePct]);

  // Derived Job Plan
  const plan = useMemo(() => {
    return planCementJob(
      holeDia,
      casingOd,
      casingId,
      intervalLen,
      shoeTrackLen,
      excessFactor,
      slurry.slurryYieldFt3Sack,
      mixingRate,
      displacementRate,
      casingTotalLen
    );
  }, [holeDia, casingOd, casingId, intervalLen, shoeTrackLen, excessFactor, slurry.slurryYieldFt3Sack, mixingRate, displacementRate, casingTotalLen]);

  // Derived Bogue Composition
  const bogue = useMemo(() => {
    return bogueCompoundsFromOxides(cao, sio2, al2o3, fe2o3, so3);
  }, [cao, sio2, al2o3, fe2o3, so3]);

  // Derived Additive Recommendations
  const recommendations = useMemo(() => {
    return recommendCementAdditives(bhtF, targetSlurryDensity, waterSensitive);
  }, [bhtF, targetSlurryDensity, waterSensitive]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-slate-900/10 via-zinc-900/10 to-stone-900/10 p-5 rounded-xl border border-zinc-500/20">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2 text-foreground">
              <Package className="w-6 h-6 text-zinc-600 dark:text-zinc-400" />
              Engenharia de Cimentação &amp; Pastas API (Bourgoyne Ch. 3)
            </h2>
            <Badge className="bg-zinc-700 text-white text-xs">SPE Textbook Series</Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-3xl">
            Formulações de pastas API Classes A-H, equações de Bogue para compostos de óxidos, planejamento de volume anular com excesso e simulação dos tempos críticos de mistura e deslocamento.
          </p>
        </div>
      </div>

      <Tabs defaultValue="slurry" className="w-full">
        <TabsList className="bg-muted p-1 grid grid-cols-3">
          <TabsTrigger value="slurry" className="text-xs">Formulação de Pasta</TabsTrigger>
          <TabsTrigger value="planning" className="text-xs">Volumes &amp; Tempos da Operação</TabsTrigger>
          <TabsTrigger value="bogue" className="text-xs">Óxidos (Bogue) &amp; Aditivos</TabsTrigger>
        </TabsList>

        {/* TAB 1: SLURRY DESIGN */}
        <TabsContent value="slurry" className="space-y-6 pt-2">
          {/* Slurry Results Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Densidade da Pasta</p>
              <p className="text-2xl font-bold font-mono text-primary mt-1">
                {slurry.slurryDensityPpg} <span className="text-xs font-normal text-muted-foreground">ppg</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Massa total / Volume total</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Rendimento da Pasta (Yield)</p>
              <p className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {slurry.slurryYieldFt3Sack} <span className="text-xs font-normal text-muted-foreground">ft³/saco</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Volume gerado por saco de 94 lb</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Água de Mistura</p>
              <p className="text-2xl font-bold font-mono text-foreground mt-1">
                {slurry.waterGallonsPerSack} <span className="text-xs font-normal text-muted-foreground">gal/saco</span>
              </p>
              <p className="text-[10px] text-muted-foreground">{slurry.mixWaterPercent.toFixed(1)}% BWOC (por peso de cimento)</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Classe API Selecionada</p>
              <p className="text-2xl font-bold font-mono text-amber-600 dark:text-amber-400 mt-1">
                {slurry.apiClass}
              </p>
              <p className="text-[10px] text-muted-foreground">Especificação API Spec 10A</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Seleção de Classe &amp; Aditivos de Densidade</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label className="text-xs">Classe do Cimento API</Label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {(['Class A', 'Class C', 'Class G', 'Class H'] as const).map((cls) => (
                      <Button
                        key={cls}
                        size="sm"
                        variant={cementClass === cls ? "default" : "outline"}
                        className="text-xs h-8"
                        onClick={() => setCementClass(cls)}
                      >
                        {cls}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <Label>Bentonita Extensora (% BWOC - Reduz densidade)</Label>
                    <span className="font-mono font-bold">{bentonitePct}%</span>
                  </div>
                  <Input
                    type="range"
                    min="0"
                    max="12"
                    step="0.5"
                    value={bentonitePct}
                    onChange={(e) => setBentonitePct(Number(e.target.value))}
                  />
                  <p className="text-[10px] text-muted-foreground">Cada 2% de bentonita requer ~1.3 gal extras de água por saco.</p>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <Label>Hematita Adensante (% BWOC - Aumenta densidade)</Label>
                    <span className="font-mono font-bold">{hematitePct}%</span>
                  </div>
                  <Input
                    type="range"
                    min="0"
                    max="35"
                    step="1"
                    value={hematitePct}
                    onChange={(e) => setHematitePct(Number(e.target.value))}
                  />
                  <p className="text-[10px] text-muted-foreground">Densidade da hematita: 5.05 SG (requer mínimo acréscimo de água).</p>
                </div>

                <div className="pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs"
                    onClick={() => {
                      setCementClass('Class G');
                      setBentonitePct(0);
                      setHematitePct(0);
                    }}
                  >
                    <RefreshCw className="w-3 h-3 mr-2" />
                    Restaurar Pasta Padrão API Classe G Pura (15.8 ppg)
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Absolute Volumes Breakdown Card */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Balanço Volumétrico Absoluto por Saco (94 lb)</CardTitle>
                <p className="text-xs text-muted-foreground">Cálculo de volume absoluto: V = Massa / (SG · 62.37 lb/ft³)</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between p-2 rounded bg-muted/30">
                    <span>Cimento Seco (94 lb, SG = 3.14):</span>
                    <span className="font-mono font-bold">0.478 ft³</span>
                  </div>
                  <div className="flex justify-between p-2 rounded bg-muted/30">
                    <span>Água de Mistura ({slurry.waterGallonsPerSack} gal, SG = 1.00):</span>
                    <span className="font-mono font-bold">{(slurry.waterGallonsPerSack / 7.4805).toFixed(3)} ft³</span>
                  </div>
                  {bentonitePct > 0 && (
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span>Bentonita ({((94 * bentonitePct) / 100).toFixed(1)} lb, SG = 2.65):</span>
                      <span className="font-mono font-bold">{(((94 * bentonitePct) / 100) / (2.65 * 62.37)).toFixed(3)} ft³</span>
                    </div>
                  )}
                  {hematitePct > 0 && (
                    <div className="flex justify-between p-2 rounded bg-muted/30">
                      <span>Hematita ({((94 * hematitePct) / 100).toFixed(1)} lb, SG = 5.05):</span>
                      <span className="font-mono font-bold">{(((94 * hematitePct) / 100) / (5.05 * 62.37)).toFixed(3)} ft³</span>
                    </div>
                  )}
                  <div className="flex justify-between p-2 rounded bg-primary/10 border border-primary/20 font-bold text-primary">
                    <span>Rendimento Total por Saco:</span>
                    <span className="font-mono">{slurry.slurryYieldFt3Sack} ft³/sk</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TAB 2: JOB PLANNING */}
        <TabsContent value="planning" className="space-y-6 pt-2">
          {/* Operations Time Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Sacos de Cimento</p>
              <p className="text-2xl font-bold font-mono text-foreground mt-1">
                {plan.sacksRequired.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">sacos</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Com {((excessFactor - 1) * 100).toFixed(0)}% de excesso anular</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Volume de Pasta</p>
              <p className="text-2xl font-bold font-mono text-primary mt-1">
                {plan.totalSlurryVolumeBbl} <span className="text-xs font-normal text-muted-foreground">bbl</span>
              </p>
              <p className="text-[10px] text-muted-foreground">{plan.totalSlurryVolumeFt3.toLocaleString()} ft³ totais</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Tempo de Mistura</p>
              <p className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400 mt-1">
                {plan.mixingTimeMinutes} <span className="text-xs font-normal text-muted-foreground">min</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Taxa de {mixingRate} sacos/min</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Tempo Total do Trabalho</p>
              <p className="text-2xl font-bold font-mono text-purple-600 dark:text-purple-400 mt-1">
                {plan.totalJobTimeMinutes} <span className="text-xs font-normal text-muted-foreground">min</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Mistura ({plan.mixingTimeMinutes}m) + Deslocamento ({plan.displacementTimeMinutes}m)</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Geometria do Poço e Revestimento</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Diâmetro do Poço (pol)</Label>
                    <Input
                      type="number"
                      step="0.125"
                      value={holeDia}
                      onChange={(e) => setHoleDia(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">OD do Revestimento (pol)</Label>
                    <Input
                      type="number"
                      step="0.125"
                      value={casingOd}
                      onChange={(e) => setCasingOd(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">ID do Revestimento (pol)</Label>
                    <Input
                      type="number"
                      step="0.001"
                      value={casingId}
                      onChange={(e) => setCasingId(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Intervalo Cimentado (ft)</Label>
                    <Input
                      type="number"
                      value={intervalLen}
                      onChange={(e) => setIntervalLen(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Comprimento da Sapata (ft)</Label>
                    <Input
                      type="number"
                      value={shoeTrackLen}
                      onChange={(e) => setShoeTrackLen(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Fator de Excesso Anular</Label>
                    <Input
                      type="number"
                      step="0.05"
                      value={excessFactor}
                      onChange={(e) => setExcessFactor(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Parâmetros de Bombeio e Deslocamento</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-1">
                  <Label className="text-xs">Vazão de Deslocamento da Lama (bpm)</Label>
                  <Input
                    type="number"
                    step="0.5"
                    value={displacementRate}
                    onChange={(e) => setDisplacementRate(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="space-y-1">
                  <Label className="text-xs">Taxa de Mistura de Cimento (sacos/min)</Label>
                  <Input
                    type="number"
                    value={mixingRate}
                    onChange={(e) => setMixingRate(Number(e.target.value))}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="p-3 rounded-lg bg-muted/40 border space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Volume de Deslocamento (Fluido de Completação):</span>
                    <span className="font-mono font-bold">{plan.displacementVolumeBbl} bbl</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Volume da Sapata (Shoe Track):</span>
                    <span className="font-mono">{plan.shoeTrackVolumeFt3} ft³</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Volume Anular Efetivo:</span>
                    <span className="font-mono">{plan.annularVolumeBbl} bbl</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* TAB 3: BOGUE & ADVISOR */}
        <TabsContent value="bogue" className="space-y-6 pt-2">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bogue Compounds */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold">Equações de Bogue: Óxidos → Compostos Minerais</CardTitle>
                <p className="text-xs text-muted-foreground">Bourgoyne Ch. 3, Eq. 3.1 - 3.4 (C3S, C2S, C3A, C4AF)</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-2">
                  <div className="space-y-1">
                    <Label className="text-[11px]">% CaO</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={cao}
                      onChange={(e) => setCao(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% SiO2</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={sio2}
                      onChange={(e) => setSio2(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% Al2O3</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={al2o3}
                      onChange={(e) => setAl2o3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% Fe2O3</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={fe2o3}
                      onChange={(e) => setFe2o3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[11px]">% SO3</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={so3}
                      onChange={(e) => setSo3(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2">
                  <div className="p-2.5 rounded bg-card border text-xs">
                    <p className="text-[10px] text-muted-foreground">C3S (Alita - Resistência Inicial)</p>
                    <p className="text-base font-bold font-mono text-primary mt-0.5">{bogue.c3s}%</p>
                  </div>
                  <div className="p-2.5 rounded bg-card border text-xs">
                    <p className="text-[10px] text-muted-foreground">C2S (Belita - Resistência Final)</p>
                    <p className="text-base font-bold font-mono text-foreground mt-0.5">{bogue.c2s}%</p>
                  </div>
                  <div className="p-2.5 rounded bg-card border text-xs">
                    <p className="text-[10px] text-muted-foreground">C3A (Aluminato Tricálcico)</p>
                    <p className="text-base font-bold font-mono text-amber-600 mt-0.5">{bogue.c3a}%</p>
                  </div>
                  <div className="p-2.5 rounded bg-card border text-xs">
                    <p className="text-[10px] text-muted-foreground">C4AF (Aluminoferrito Tetracálcico)</p>
                    <p className="text-base font-bold font-mono text-foreground mt-0.5">{bogue.c4af}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Additive Advisor */}
            <Card className="shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-500" />
                  Recomendador de Aditivos de Cimentação
                </CardTitle>
                <p className="text-xs text-muted-foreground">Análise termomecânica baseada em temperatura e densidade alvo</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Temperatura de Fundo (°F)</Label>
                    <Input
                      type="number"
                      value={bhtF}
                      onChange={(e) => setBhtF(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Densidade Alvo (ppg)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={targetSlurryDensity}
                      onChange={(e) => setTargetSlurryDensity(Number(e.target.value))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase">
                    Aditivos Recomendados (Bourgoyne Tabelas 3.8 - 3.11):
                  </p>
                  {recommendations.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic">Nenhum aditivo especial necessário para estas condições.</p>
                  ) : (
                    recommendations.map((rec, i) => (
                      <div key={i} className="p-2.5 rounded bg-muted/40 border text-xs space-y-0.5">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-foreground">{rec.name} ({rec.category})</span>
                          <Badge variant="outline" className="text-[10px]">{rec.dosage}</Badge>
                        </div>
                        <p className="text-[11px] text-muted-foreground">{rec.reason}</p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
