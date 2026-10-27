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
import { Select } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  calculateAdvancedWellControl,
  calculatePitVolume,
  calculateTriplexPump,
  calculateHydrostatic,
  calculatePressureChangeWithSpeed,
  calculatePressureChangeWithMudWeight,
  calculateLOTAndMAASP,
  calculateTrippingPressureLoss,
  pipeCapacity,
  annularCapacity,
  pipeDisplacement,
  closedEndDisplacement,
  buildTripSheetRow,
  DRILLING_CONSTANTS,
  RoundRules,
} from "@/lib/drillingMath";
import {
  ShieldAlert,
  Flame,
  Gauge,
  Activity,
  Layers,
  FileText,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  Workflow,
  Download,
  Calculator,
  Compass,
  BookOpen,
  HelpCircle,
  TrendingDown,
  ArrowRight,
  Boxes,
} from "lucide-react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export default function WellControlView() {
  const [activeTab, setActiveTab] = useState<string>("kill-sheet");

  // ==========================================
  // TAB 1: KILL SHEET & WELL CONTROL STATE
  // ==========================================
  const [tvd, setTvd] = useState<number>(10000); // ft
  const [md, setMd] = useState<number>(10800); // ft
  const [currentMw, setCurrentMw] = useState<number>(10.2); // ppg
  const [casingShoeTvd, setCasingShoeTvd] = useState<number>(7500); // ft
  const [lotTestMw, setLotTestMw] = useState<number>(10.0); // ppg
  const [lotSurfacePressure, setLotSurfacePressure] = useState<number>(1755); // psi
  const [sidpp, setSidpp] = useState<number>(480); // psi
  const [sicp, setSicp] = useState<number>(680); // psi
  const [pitGainBbl, setPitGainBbl] = useState<number>(24); // bbl
  const [scrPressure, setScrPressure] = useState<number>(750); // psi
  const [scrSpm, setScrSpm] = useState<number>(30); // spm
  const [drillStringStrokes, setDrillStringStrokes] = useState<number>(1150); // surface to bit
  const [dcLengthFt, setDcLengthFt] = useState<number>(600); // ft
  const [dcOhAnnCap, setDcOhAnnCap] = useState<number>(0.029); // bbl/ft
  const [dpOhAnnCap, setDpOhAnnCap] = useState<number>(0.0459); // bbl/ft
  const [isExporting, setIsExporting] = useState<boolean>(false);

  const wellControlResults = useMemo(() => {
    return calculateAdvancedWellControl({
      tvd,
      md,
      currentMw,
      casingShoeTvd,
      lotTestMw,
      lotSurfacePressure,
      sidpp,
      sicp,
      pitGainBbl,
      scrPressure,
      scrSpm,
      pumpOutputBblStk: 0.119,
      dcLengthFt,
      dcOhAnnCapBblFt: dcOhAnnCap,
      dpOhAnnCapBblFt: dpOhAnnCap,
      drillStringStrokes,
    });
  }, [
    tvd,
    md,
    currentMw,
    casingShoeTvd,
    lotTestMw,
    lotSurfacePressure,
    sidpp,
    sicp,
    pitGainBbl,
    scrPressure,
    scrSpm,
    dcLengthFt,
    dcOhAnnCap,
    dpOhAnnCap,
    drillStringStrokes,
  ]);

  // ==========================================
  // TAB 2: VOLUME ENGINE & TRIP SHEET STATE
  // ==========================================
  const [pitLength, setPitLength] = useState<number>(30); // ft
  const [pitWidth, setPitWidth] = useState<number>(10); // ft
  const [pitDepth, setPitDepth] = useState<number>(8); // ft

  const [linerId, setLinerId] = useState<number>(6.0); // in
  const [strokeLen, setStrokeLen] = useState<number>(12); // in
  const [pumpEff, setPumpEff] = useState<number>(97); // %
  const [pumpSpm, setPumpSpm] = useState<number>(110); // spm

  const pitCalc = useMemo(() => {
    return calculatePitVolume({ lengthFt: pitLength, widthFt: pitWidth, depthFt: pitDepth });
  }, [pitLength, pitWidth, pitDepth]);

  const pumpCalc = useMemo(() => {
    return calculateTriplexPump({
      linerIdInches: linerId,
      strokeLengthInches: strokeLen,
      efficiencyPercent: pumpEff,
      spm: pumpSpm,
    });
  }, [linerId, strokeLen, pumpEff, pumpSpm]);

  // Trip Sheet Simulation Data (10 stands pulled)
  const [tripType, setTripType] = useState<"dry" | "wet">("dry");
  const tripSheetData = useMemo(() => {
    const pipeDisp = pipeDisplacement(19.5); // 5" DP ~ 19.5 lb/ft -> 0.0071 bbl/ft
    const closedDisp = closedEndDisplacement(5.0); // 0.0243 bbl/ft
    const standLen = 93; // ft
    const rows = [];
    let cumCalc = 0;
    let cumActual = 0;

    // Simulate 6 sample check points (every 5 stands)
    const actualStepChanges = [
      tripType === "dry" ? 3.2 : 11.2,
      tripType === "dry" ? 3.3 : 11.3,
      tripType === "dry" ? 3.2 : 11.1,
      tripType === "dry" ? 3.4 : 11.4,
      tripType === "dry" ? 3.3 : 11.3,
    ];

    for (let i = 0; i < actualStepChanges.length; i++) {
      const standNumber = (i + 1) * 5;
      const actualFor5Stands = actualStepChanges[i];
      const row = buildTripSheetRow(
        standNumber,
        standLen * 5,
        pipeDisp,
        closedDisp,
        tripType === "wet",
        actualFor5Stands,
        cumCalc,
        cumActual
      );
      cumCalc = row.cumulativeCalculatedBbl;
      cumActual = row.cumulativeActualBbl;
      rows.push(row);
    }
    return rows;
  }, [tripType]);

  // ==========================================
  // TAB 3: PRESSURE ENGINE & TRIPPING LOSS STATE
  // ==========================================
  const [pressMudWeight, setPressMudWeight] = useState<number>(11.2); // ppg
  const [pressTvd, setPressTvd] = useState<number>(9200); // ft
  const [oldSpm, setOldSpm] = useState<number>(90);
  const [newSpm, setNewSpm] = useState<number>(115);
  const [oldPumpPress, setOldPumpPress] = useState<number>(2400); // psi
  const [oldMw, setOldMw] = useState<number>(10.5);
  const [newMw, setNewMw] = useState<number>(11.8);
  const [oldCircPress, setOldCircPress] = useState<number>(2100);

  const hpCalc = useMemo(() => {
    return calculateHydrostatic(pressMudWeight, pressTvd);
  }, [pressMudWeight, pressTvd]);

  const speedCalc = useMemo(() => {
    return calculatePressureChangeWithSpeed(oldPumpPress, oldSpm, newSpm);
  }, [oldPumpPress, oldSpm, newSpm]);

  const mwPressCalc = useMemo(() => {
    return calculatePressureChangeWithMudWeight(oldCircPress, oldMw, newMw);
  }, [oldCircPress, oldMw, newMw]);

  const trippingLoss = useMemo(() => {
    const pipeDisp = pipeDisplacement(19.5);
    const closedDisp = closedEndDisplacement(5.0);
    const casingCap = pipeCapacity(8.681); // 9-5/8" casing
    return calculateTrippingPressureLoss(
      pressMudWeight,
      pipeDisp,
      closedDisp,
      casingCap,
      93,
      10,
      tripType === "wet"
    );
  }, [pressMudWeight, tripType]);

  // ==========================================
  // TAB 4: TRAINING & QUIZ ENGINE
  // ==========================================
  const [quizScore, setQuizScore] = useState<number | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});

  const quizQuestions = [
    {
      id: 1,
      q: "Qual é a regra padrão da indústria para arredondamento do Kill Mud Weight (KMW)?",
      options: [
        "Arredondar para baixo com 2 casas decimais",
        "Arredondar para cima (Round UP) para 1 casa decimal",
        "Arredondar para o inteiro mais próximo",
        "Não arredondar",
      ],
      correct: "Arredondar para cima (Round UP) para 1 casa decimal",
      explanation:
        "O Kill Mud Weight deve sempre ser arredondado PARA CIMA para a 1ª casa decimal (ex: 11.23 -> 11.3 ppg) para garantir segurança e prevenir sub-balanceio.",
    },
    {
      id: 2,
      q: "Se a rotação da bomba aumenta de 60 SPM para 90 SPM, qual é a nova pressão sabendo que a pressão anterior era 1200 psi?",
      options: ["1800 psi", "2700 psi", "2400 psi", "1500 psi"],
      correct: "2700 psi",
      explanation:
        "Lei quadrática das bombas: P2 = P1 * (SPM2 / SPM1)² = 1200 * (90/60)² = 1200 * 2.25 = 2700 psi.",
    },
    {
      id: 3,
      q: "Em um influxo, se a densidade calculada for 1.8 ppg, qual é a natureza provável do fluido?",
      options: ["Água Salgada", "Óleo Leve", "Gás Natural", "Lama com Barita"],
      correct: "Gás Natural",
      explanation:
        "Fluidos com densidade < 2.5 ppg indicam gás. Entre 2.5 e 7.0 ppg indicam óleo/condensado, e > 7.0 ppg água salgada.",
    },
    {
      id: 4,
      q: "Como o MAASP (Maximum Allowable Annular Surface Pressure) se comporta quando a densidade da lama no poço é aumentada?",
      options: [
        "Aumenta proporcionalmente",
        "Diminui",
        "Permanece inalterado",
        "Dobra de valor",
      ],
      correct: "Diminui",
      explanation:
        "MAASP = (Max MW - Current MW) * 0.052 * Shoe TVD. À medida que a Current MW aumenta, a margem de pressão suportada pela sapata antes de fraturar diminui.",
    },
  ];

  const handleGradeQuiz = () => {
    let score = 0;
    quizQuestions.forEach((q) => {
      if (selectedAnswers[q.id] === q.correct) {
        score += 25;
      }
    });
    setQuizScore(score);
  };

  const exportKillSheetPDF = async () => {
    const el = document.getElementById("kill-sheet-print-container");
    if (!el) return;
    setIsExporting(true);
    try {
      const canvas = await html2canvas(el, { scale: 2 });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("p", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("PetroLumen_IADC_Kill_Sheet.pdf");
    } catch (err) {
      console.error("Kill sheet export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div id="kill-sheet-print-container" className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-500" />
            <h2 className="text-2xl font-bold tracking-tight">
              Módulo Unit-Aware de Cálculos de Perfuração & Controle de Poço
            </h2>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Suíte integrada com 4 motores matemáticos: Cálculo e Regras da Companhia, Engenharia de Volumes & Trip Sheet, Engenharia de Pressões e Controle de Poço IADC/IWCF.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs px-3 py-1 font-semibold bg-rose-500/10 text-rose-600 border-rose-500/30">
            KMW = {wellControlResults.kmw} ppg (Arredondado p/ Cima)
          </Badge>
          <Button variant="outline" size="sm" onClick={exportKillSheetPDF} disabled={isExporting}>
            <Download className="w-4 h-4 mr-2" />
            {isExporting ? "Gerando..." : "Exportar Kill Sheet PDF"}
          </Button>
        </div>
      </div>

      {/* Tabs navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-muted p-1 grid grid-cols-2 lg:grid-cols-4 w-full">
          <TabsTrigger value="kill-sheet">1. Kill Sheet & Influxo</TabsTrigger>
          <TabsTrigger value="volumes">2. Volumes & Trip Sheet</TabsTrigger>
          <TabsTrigger value="pressures">3. Pressões, LOT & Tripping</TabsTrigger>
          <TabsTrigger value="training">4. Modo Treinamento & Teste</TabsTrigger>
        </TabsList>

        {/* ========================================================= */}
        {/* TAB 1: KILL SHEET & ADVANCED WELL CONTROL */}
        {/* ========================================================= */}
        <TabsContent value="kill-sheet" className="pt-4 space-y-6">
          {/* KPI Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="p-3 bg-rose-500/5 border-rose-500/20">
              <p className="text-[11px] font-medium text-muted-foreground">Kill Mud Weight (KMW)</p>
              <p className="text-xl font-bold text-rose-600 dark:text-rose-400 mt-1 font-mono">
                {wellControlResults.kmw} <span className="text-xs font-normal">ppg</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Exato: {wellControlResults.kmwExact} ppg</p>
            </Card>

            <Card className="p-3 bg-amber-500/5 border-amber-500/20">
              <p className="text-[11px] font-medium text-muted-foreground">Pressão Inicial (ICP)</p>
              <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
                {wellControlResults.icp} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">SCRP ({scrPressure}) + SIDPP ({sidpp})</p>
            </Card>

            <Card className="p-3 bg-blue-500/5 border-blue-500/20">
              <p className="text-[11px] font-medium text-muted-foreground">Pressão Final (FCP)</p>
              <p className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
                {wellControlResults.fcp} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Kill Mud no Bit</p>
            </Card>

            <Card className="p-3 bg-purple-500/5 border-purple-500/20">
              <p className="text-[11px] font-medium text-muted-foreground">MAASP Atual</p>
              <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
                {wellControlResults.lotCalc.maasp} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">Sapata: {casingShoeTvd} ft</p>
            </Card>

            <Card className="p-3 bg-emerald-500/5 border-emerald-500/20">
              <p className="text-[11px] font-medium text-muted-foreground">Pressão da Formação</p>
              <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
                {wellControlResults.formationPressure.toLocaleString()} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[10px] text-muted-foreground">{wellControlResults.formationGradient} psi/ft</p>
            </Card>

            <Card className="p-3 bg-card border">
              <p className="text-[11px] font-medium text-muted-foreground">Tipo de Influxo</p>
              <p className="text-xl font-bold text-primary mt-1 truncate">
                {wellControlResults.influxType}
              </p>
              <p className="text-[10px] text-muted-foreground">{wellControlResults.influxMw} ppg densidade</p>
            </Card>
          </div>

          {/* Form and Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-primary" />
                  Entradas do Poço & Leituras
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="kc-tvd">TVD do Poço (ft)</Label>
                    <Input id="kc-tvd" type="number" value={tvd} onChange={(e) => setTvd(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="kc-mw">Lama Atual OMW (ppg)</Label>
                    <Input id="kc-mw" type="number" step="0.1" value={currentMw} onChange={(e) => setCurrentMw(Number(e.target.value))} />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="kc-shoe">TVD Sapata (ft)</Label>
                    <Input id="kc-shoe" type="number" value={casingShoeTvd} onChange={(e) => setCasingShoeTvd(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="kc-lot">LOT Superfície (psi)</Label>
                    <Input id="kc-lot" type="number" value={lotSurfacePressure} onChange={(e) => setLotSurfacePressure(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg space-y-2">
                  <span className="font-semibold text-rose-700 dark:text-rose-300 block">
                    Leituras de Fechamento (Shut-In)
                  </span>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="kc-sidpp">SIDPP (psi)</Label>
                      <Input id="kc-sidpp" type="number" className="bg-background" value={sidpp} onChange={(e) => setSidpp(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="kc-sicp">SICP (psi)</Label>
                      <Input id="kc-sicp" type="number" className="bg-background" value={sicp} onChange={(e) => setSicp(Number(e.target.value))} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="kc-gain">Ganho Tanque (bbl)</Label>
                      <Input id="kc-gain" type="number" className="bg-background" value={pitGainBbl} onChange={(e) => setPitGainBbl(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="kc-scr">SCRP (psi)</Label>
                      <Input id="kc-scr" type="number" className="bg-background" value={scrPressure} onChange={(e) => setScrPressure(Number(e.target.value))} />
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="kc-stk">Strokes até o Bit</Label>
                    <Input id="kc-stk" type="number" value={drillStringStrokes} onChange={(e) => setDrillStringStrokes(Number(e.target.value))} />
                  </div>
                  <div>
                    <Label htmlFor="kc-dc">Comprimento DC (ft)</Label>
                    <Input id="kc-dc" type="number" value={dcLengthFt} onChange={(e) => setDcLengthFt(Number(e.target.value))} />
                  </div>
                </div>

                <div className="p-2 bg-muted/40 rounded text-[11px] space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Queda por 100 strokes:</span>
                    <span className="font-mono font-bold text-foreground">{wellControlResults.psiPer100Stk} psi/100 stk</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Altura Influxo:</span>
                    <span className="font-mono font-bold text-foreground">
                      {wellControlResults.influxHeightFt} ft {wellControlResults.isSplitInflux ? "(Dividido em DC+DP)" : "(No DC)"}
                    </span>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs"
                  onClick={() => {
                    setTvd(10000);
                    setMd(10800);
                    setCurrentMw(10.2);
                    setCasingShoeTvd(7500);
                    setLotSurfacePressure(1755);
                    setSidpp(480);
                    setSicp(680);
                    setPitGainBbl(24);
                    setScrPressure(750);
                    setDrillStringStrokes(1150);
                    setDcLengthFt(600);
                  }}
                >
                  <RefreshCw className="w-3 h-3 mr-2" />
                  Restaurar Valores Padrão
                </Button>
              </CardContent>
            </Card>

            {/* Graphs Column */}
            <div className="lg:col-span-2 space-y-6">
              <Card className="shadow-sm">
                <CardHeader className="pb-2 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-semibold flex items-center gap-2">
                      <Activity className="w-4 h-4 text-primary" />
                      Cronograma de Deslocamento: ICP → FCP (Wait & Weight)
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      Pressão requerida no tubo de perfuração durante o bombeio da lama pesada até a broca.
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs font-mono">
                    Redução: {wellControlResults.psiPer100Stk} psi / 100 stks
                  </Badge>
                </CardHeader>
                <CardContent>
                  <div className="h-[280px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={wellControlResults.dynamicSchedule} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                        <XAxis dataKey="strokes" label={{ value: "Strokes Bombeados", position: "insideBottom", offset: -10 }} />
                        <YAxis domain={["auto", "auto"]} label={{ value: "Pressão DPP (psi)", angle: -90, position: "insideLeft", offset: 0 }} />
                        <Tooltip formatter={(v: any) => [`${v} psi`, "Pressão de Circulação"]} labelFormatter={(s) => `${s} strokes`} />
                        <Legend verticalAlign="top" height={36} />
                        <Line type="monotone" dataKey="dpp" name="Pressão de Circulação (ICP → FCP)" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 mt-2 border-t text-xs">
                    <div>
                      <span className="text-muted-foreground block text-[11px]">0 strokes:</span>
                      <span className="font-mono font-bold text-amber-600 dark:text-amber-400">ICP = {wellControlResults.icp} psi</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[11px]">{drillStringStrokes} strokes (Bit):</span>
                      <span className="font-mono font-bold text-blue-600 dark:text-blue-400">FCP = {wellControlResults.fcp} psi</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[11px]">Gradiente Influxo:</span>
                      <span className="font-mono font-bold text-foreground">{wellControlResults.influxGradient} psi/ft</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block text-[11px]">Max Mud Weight:</span>
                      <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        {wellControlResults.lotCalc.maxMw} ppg (Arredondado p/ Baixo)
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Influx & Safety details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <Card className="p-4 shadow-sm">
                  <h4 className="font-semibold text-muted-foreground uppercase text-[11px] mb-2 flex items-center gap-1.5">
                    <Flame className="w-3.5 h-3.5 text-orange-500" />
                    Divisão de Influxo no Anular
                  </h4>
                  <div className="space-y-1.5">
                    <div className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">Volume no DC-OH:</span>
                      <span className="font-mono font-bold">{(dcLengthFt * dcOhAnnCap).toFixed(1)} bbl</span>
                    </div>
                    <div className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">Altura no DC:</span>
                      <span className="font-mono font-bold">{wellControlResults.dcHeightFt} ft</span>
                    </div>
                    {wellControlResults.isSplitInflux && (
                      <div className="flex justify-between border-b pb-1 text-amber-600 dark:text-amber-400">
                        <span>Altura no DP-OH:</span>
                        <span className="font-mono font-bold">+{wellControlResults.dpHeightFt} ft</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Altura Total do Influxo:</span>
                      <span className="font-mono font-bold text-primary">{wellControlResults.influxHeightFt} ft</span>
                    </div>
                  </div>
                </Card>

                <Card className="p-4 shadow-sm">
                  <h4 className="font-semibold text-muted-foreground uppercase text-[11px] mb-2 flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-purple-500" />
                    Limites de Integridade da Sapata
                  </h4>
                  <div className="space-y-1.5">
                    <div className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">Pressão Fratura Sapata:</span>
                      <span className="font-mono font-bold">{wellControlResults.lotCalc.fracturePressure} psi</span>
                    </div>
                    <div className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">Gradiente de Fratura:</span>
                      <span className="font-mono font-bold">{wellControlResults.lotCalc.fractureGradient} psi/ft</span>
                    </div>
                    <div className="flex justify-between border-b pb-1">
                      <span className="text-muted-foreground">MAASP Atual:</span>
                      <span className="font-mono font-bold text-purple-600 dark:text-purple-400">
                        {wellControlResults.lotCalc.maasp} psi
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status do MAASP:</span>
                      <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/40">
                        Seguro (&gt; 0 psi)
                      </Badge>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 2: VOLUME ENGINE & TRIP SHEET */}
        {/* ========================================================= */}
        <TabsContent value="volumes" className="pt-4 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Pit & Pump Calculators */}
            <div className="lg:col-span-1 space-y-6">
              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Boxes className="w-4 h-4 text-primary" />
                    Cálculo de Tanques de Lama (Pits)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <Label htmlFor="pit-l">Comprimento (ft)</Label>
                      <Input id="pit-l" type="number" value={pitLength} onChange={(e) => setPitLength(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="pit-w">Largura (ft)</Label>
                      <Input id="pit-w" type="number" value={pitWidth} onChange={(e) => setPitWidth(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="pit-d">Profundidade (ft)</Label>
                      <Input id="pit-d" type="number" value={pitDepth} onChange={(e) => setPitDepth(Number(e.target.value))} />
                    </div>
                  </div>
                  <div className="p-3 bg-primary/5 rounded border border-primary/20 space-y-1 font-mono">
                    <div className="flex justify-between">
                      <span>Volume Total:</span>
                      <span className="font-bold text-primary">{pitCalc.volumeBbl} bbl ({pitCalc.volumeM3} m³)</span>
                    </div>
                    <div className="flex justify-between text-muted-foreground">
                      <span>Barril por Pé:</span>
                      <span>{pitCalc.bblPerFoot} bbl/ft</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <Gauge className="w-4 h-4 text-blue-500" />
                    Débito de Bomba Triplex
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="lin-id">Diâmetro Camisa (pol)</Label>
                      <Input id="lin-id" type="number" step="0.25" value={linerId} onChange={(e) => setLinerId(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="str-len">Curso do Pistão (pol)</Label>
                      <Input id="str-len" type="number" value={strokeLen} onChange={(e) => setStrokeLen(Number(e.target.value))} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="p-eff">Eficiência (%)</Label>
                      <Input id="p-eff" type="number" value={pumpEff} onChange={(e) => setPumpEff(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="p-spm">Velocidade (SPM)</Label>
                      <Input id="p-spm" type="number" value={pumpSpm} onChange={(e) => setPumpSpm(Number(e.target.value))} />
                    </div>
                  </div>
                  <div className="p-3 bg-blue-500/5 rounded border border-blue-500/20 space-y-1 font-mono">
                    <div className="flex justify-between">
                      <span>Débito por Stroke:</span>
                      <span className="font-bold text-blue-600 dark:text-blue-400">{pumpCalc.bblPerStk} bbl/stk</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Vazão a {pumpSpm} SPM:</span>
                      <span className="font-bold">{pumpCalc.bblPerMin} bbl/min ({pumpCalc.gpm} GPM)</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Digital Trip Sheet Monitor */}
            <Card className="lg:col-span-2 shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <FileText className="w-4 h-4 text-emerald-500" />
                    Planilha Digital de Manobra (Digital Trip Sheet)
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Monitoramento contínuo de volume no Trip Tank a cada 5 seções retiradas do poço (Regra IADC).
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold">Tipo Manobra:</span>
                  <Select
                    className="w-36 text-xs h-7"
                    value={tripType}
                    onChange={(e) => setTripType(e.target.value as any)}
                  >
                    <option value="dry">Seca (Dry)</option>
                    <option value="wet">Molhada (Wet)</option>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-muted text-muted-foreground uppercase text-[10px]">
                      <tr>
                        <th className="p-2.5">Stands</th>
                        <th className="p-2.5">Comprimento</th>
                        <th className="p-2.5">Calc Disp (bbl)</th>
                        <th className="p-2.5">Real Tanque (bbl)</th>
                        <th className="p-2.5">Cum Calc</th>
                        <th className="p-2.5">Cum Real</th>
                        <th className="p-2.5">Diferença</th>
                        <th className="p-2.5">Alerta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {tripSheetData.map((row) => (
                        <tr key={row.standNumber} className="hover:bg-muted/30">
                          <td className="p-2.5 font-bold font-mono">{row.standNumber} stands</td>
                          <td className="p-2.5 font-mono">{row.standLengthFt} ft</td>
                          <td className="p-2.5 font-mono">{row.calculatedDisplacementBbl}</td>
                          <td className="p-2.5 font-mono font-semibold">{row.actualTripTankBbl}</td>
                          <td className="p-2.5 font-mono text-muted-foreground">{row.cumulativeCalculatedBbl}</td>
                          <td className="p-2.5 font-mono text-muted-foreground">{row.cumulativeActualBbl}</td>
                          <td className="p-2.5 font-mono font-bold">
                            {row.differenceBbl > 0 ? `+${row.differenceBbl}` : row.differenceBbl} bbl
                          </td>
                          <td className="p-2.5">
                            {row.status === "OK" ? (
                              <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-500/30">
                                Normal
                              </Badge>
                            ) : row.status === "WARNING_GAIN" ? (
                              <Badge variant="outline" className="text-[10px] text-rose-600 border-rose-500/30">
                                Pistoneio (Gain)
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-[10px] text-amber-600 border-amber-500/30">
                                Perda (Loss)
                              </Badge>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-3 bg-muted/30 rounded border text-xs text-muted-foreground mt-4 space-y-1">
                  <p className="font-semibold text-foreground">Regras do Livro de Controle de Poço:</p>
                  <p>• Deslocamento de aço do tubo: Peso (lb/ft) ÷ 2747 = Deslocamento real (bbl/ft).</p>
                  <p>• Deslocamento de extremidade fechada (Closed-End): OD² ÷ 1029.4 bbl/ft.</p>
                  <p>• Se o poço consumir menos lama que o calculado na manobra, investigar imediatamente influxo por pistoneio (swabbing).</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 3: PRESSURE ENGINE, LOT & TRIPPING PRESSURE LOSS */}
        {/* ========================================================= */}
        <TabsContent value="pressures" className="pt-4 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-4 bg-primary/5 border-primary/20">
              <p className="text-xs font-medium text-muted-foreground">Pressão Hidrostática</p>
              <p className="text-2xl font-bold text-primary mt-1 font-mono">
                {hpCalc.hp.toLocaleString()} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Gradiente: {hpCalc.gradient} psi/ft</p>
            </Card>

            <Card className="p-4 bg-blue-500/5 border-blue-500/20">
              <p className="text-xs font-medium text-muted-foreground">Pressão c/ Mudança de Velocidade</p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
                {speedCalc.pNew} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">De {oldSpm} para {newSpm} SPM (Lei Quadrática)</p>
            </Card>

            <Card className="p-4 bg-purple-500/5 border-purple-500/20">
              <p className="text-xs font-medium text-muted-foreground">Perda de Pressão na Manobra (Swab)</p>
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
                {trippingLoss.totalDeltaP} <span className="text-xs font-normal">psi</span>
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">10 stands ({tripType.toUpperCase()} trip)</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="lg:col-span-1 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">Parâmetros de Pressão</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3.5 text-xs">
                <div className="space-y-1">
                  <Label htmlFor="p-mw">Densidade da Lama (ppg)</Label>
                  <Input id="p-mw" type="number" step="0.1" value={pressMudWeight} onChange={(e) => setPressMudWeight(Number(e.target.value))} />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="p-tvd">Profundidade TVD (ft)</Label>
                  <Input id="p-tvd" type="number" value={pressTvd} onChange={(e) => setPressTvd(Number(e.target.value))} />
                </div>

                <div className="pt-2 border-t space-y-2">
                  <p className="font-semibold text-muted-foreground uppercase text-[10px]">Alteração de Velocidade da Bomba</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="old-spm">SPM Antigo</Label>
                      <Input id="old-spm" type="number" value={oldSpm} onChange={(e) => setOldSpm(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="new-spm">SPM Novo</Label>
                      <Input id="new-spm" type="number" value={newSpm} onChange={(e) => setNewSpm(Number(e.target.value))} />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="old-press">Pressão Antiga (psi)</Label>
                    <Input id="old-press" type="number" value={oldPumpPress} onChange={(e) => setOldPumpPress(Number(e.target.value))} />
                  </div>
                </div>

                <div className="pt-2 border-t space-y-2">
                  <p className="font-semibold text-muted-foreground uppercase text-[10px]">Alteração de Densidade da Lama</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label htmlFor="old-mw">MW Antiga (ppg)</Label>
                      <Input id="old-mw" type="number" step="0.1" value={oldMw} onChange={(e) => setOldMw(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label htmlFor="new-mw">MW Nova (ppg)</Label>
                      <Input id="new-mw" type="number" step="0.1" value={newMw} onChange={(e) => setNewMw(Number(e.target.value))} />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="old-circ">Pressão Antiga (psi)</Label>
                    <Input id="old-circ" type="number" value={oldCircPress} onChange={(e) => setOldCircPress(Number(e.target.value))} />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-2 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">Memória de Cálculo & Passos Intermediários</CardTitle>
                <p className="text-xs text-muted-foreground">Auditoria detalhada com substituição de fórmulas da Engenharia de Perfuração.</p>
              </CardHeader>
              <CardContent className="space-y-4 text-xs font-mono">
                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="font-bold text-foreground font-sans">1. Hidrostática & Gradiente:</p>
                  {hpCalc.steps.map((s, idx) => (
                    <p key={idx} className="text-muted-foreground">{s}</p>
                  ))}
                </div>

                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="font-bold text-foreground font-sans">2. Efeito da Rotação da Bomba (Lei dos Quadrados):</p>
                  {speedCalc.steps.map((s, idx) => (
                    <p key={idx} className="text-muted-foreground">{s}</p>
                  ))}
                </div>

                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="font-bold text-foreground font-sans">3. Efeito da Densidade da Lama na Circulação:</p>
                  {mwPressCalc.steps.map((s, idx) => (
                    <p key={idx} className="text-muted-foreground">{s}</p>
                  ))}
                </div>

                <div className="p-3 bg-muted/40 rounded border space-y-1">
                  <p className="font-bold text-foreground font-sans">4. Perda de Pressão por Pistoneio na Manobra (Tripping ΔP):</p>
                  {trippingLoss.steps.map((s, idx) => (
                    <p key={idx} className="text-muted-foreground">{s}</p>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ========================================================= */}
        {/* TAB 4: MODO TREINAMENTO & TESTE INTERATIVO */}
        {/* ========================================================= */}
        <TabsContent value="training" className="pt-4 space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Unit converter library */}
            <Card className="lg:col-span-1 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold flex items-center gap-2">
                  <Compass className="w-4 h-4 text-primary" />
                  Biblioteca de Conversão de Unidades
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs">
                <div className="p-2.5 bg-muted/40 rounded border space-y-1">
                  <span className="font-semibold block text-foreground">Pressão:</span>
                  <div className="flex justify-between text-muted-foreground font-mono">
                    <span>1 bar = 14.5038 psi</span>
                    <span>1 psi = 0.0689 bar</span>
                  </div>
                </div>

                <div className="p-2.5 bg-muted/40 rounded border space-y-1">
                  <span className="font-semibold block text-foreground">Comprimento:</span>
                  <div className="flex justify-between text-muted-foreground font-mono">
                    <span>1 metro = 3.281 pés</span>
                    <span>1 pé = 0.3048 metros</span>
                  </div>
                </div>

                <div className="p-2.5 bg-muted/40 rounded border space-y-1">
                  <span className="font-semibold block text-foreground">Densidade:</span>
                  <div className="flex justify-between text-muted-foreground font-mono">
                    <span>1 ppg = 0.1198 SG</span>
                    <span>1 SG = 8.345 ppg</span>
                  </div>
                </div>

                <div className="p-2.5 bg-muted/40 rounded border space-y-1">
                  <span className="font-semibold block text-foreground">Volume & Barris:</span>
                  <div className="flex justify-between text-muted-foreground font-mono">
                    <span>1 m³ = 6.2905 bbl</span>
                    <span>1 bbl = 0.15897 m³</span>
                  </div>
                  <div className="flex justify-between text-muted-foreground font-mono">
                    <span>1 ft³ = 0.1781 bbl</span>
                    <span>1 bbl = 42 galões</span>
                  </div>
                </div>

                <div className="p-2.5 bg-muted/40 rounded border space-y-1">
                  <span className="font-semibold block text-foreground">Deslocamento de Aço:</span>
                  <p className="text-muted-foreground font-mono">Peso (lb/ft) ÷ 2747 = Deslocamento (bbl/ft)</p>
                </div>
              </CardContent>
            </Card>

            {/* Quiz & Examination Mode */}
            <Card className="lg:col-span-2 shadow-sm">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-emerald-500" />
                    Simulado Interativo de Controle de Poço (IADC / IWCF)
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Avalie seus conhecimentos com questões práticas baseadas nos testes de certificação.
                  </p>
                </div>
                {quizScore !== null && (
                  <Badge variant="outline" className={`text-xs font-bold ${quizScore >= 75 ? "text-emerald-600 border-emerald-500" : "text-rose-600 border-rose-500"}`}>
                    Nota: {quizScore}% {quizScore >= 75 ? "• Aprovado" : "• Reprovado"}
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {quizQuestions.map((q) => (
                  <div key={q.id} className="p-3 bg-muted/20 border rounded-lg space-y-2 text-xs">
                    <p className="font-semibold text-foreground">{q.id}. {q.q}</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      {q.options.map((opt) => (
                        <button
                          key={opt}
                          onClick={() => setSelectedAnswers((prev) => ({ ...prev, [q.id]: opt }))}
                          className={`p-2 rounded text-left transition border ${
                            selectedAnswers[q.id] === opt
                              ? "bg-primary text-primary-foreground font-semibold border-primary"
                              : "bg-background hover:bg-muted text-foreground"
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                    {quizScore !== null && (
                      <div className={`p-2 rounded mt-2 ${selectedAnswers[q.id] === q.correct ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300" : "bg-rose-500/10 text-rose-700 dark:text-rose-300"}`}>
                        <p className="font-bold">
                          {selectedAnswers[q.id] === q.correct ? "✓ Correto!" : `✗ Incorreto. Resposta correta: ${q.correct}`}
                        </p>
                        <p className="text-[11px] mt-0.5">{q.explanation}</p>
                      </div>
                    )}
                  </div>
                ))}

                <Button className="w-full" onClick={handleGradeQuiz}>
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Corrigir Respostas do Simulado
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
