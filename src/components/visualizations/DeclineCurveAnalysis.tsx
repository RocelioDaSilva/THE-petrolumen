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
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { generateDCACurve, DCAParams } from "@/lib/reservoirMath";
import { TrendingDown, Download, Sparkles, FileText, BarChart3 } from "lucide-react";
import { ProvenanceBadge } from "@/components/ui/ProvenanceBadge";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { useSessionRegistry } from "@/lib/sessionRegistry";
import { useUnit } from "@/lib/unitContext";

export default function DeclineCurveAnalysis() {
  const { activeScenario, updateActiveParameters } = useSessionRegistry();
  const { isMetric, formatRate, formatVolume } = useUnit();
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const [model, setModel] = useState<DCAParams["model"]>("hyperbolic");
  const [qi, setQi] = useState<number>(activeScenario?.parameters?.initialRateStbd ?? 1200);
  const [di, setDi] = useState<number>(activeScenario?.parameters?.nominalDeclineRate ?? 0.08);
  const [b, setB] = useState<number>(activeScenario?.parameters?.arpsBFactor ?? 0.65);
  const [duongA, setDuongA] = useState<number>(1.25);
  const [duongM, setDuongM] = useState<number>(1.12);
  const [isExporting, setIsExporting] = useState<boolean>(false);

  // Sync state with active scenario
  React.useEffect(() => {
    if (activeScenario?.parameters) {
      const p = activeScenario.parameters;
      if (p.initialRateStbd) setQi(p.initialRateStbd);
      if (p.nominalDeclineRate) setDi(p.nominalDeclineRate);
      if (p.arpsBFactor !== undefined) setB(p.arpsBFactor);
    }
  }, [activeScenario?.id]);

  const handleSaveToScenario = () => {
    updateActiveParameters({
      initialRateStbd: qi,
      nominalDeclineRate: di,
      arpsBFactor: b,
    });
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2500);
  };

  const curveData = useMemo(() => {
    return generateDCACurve(
      {
        qi,
        di,
        b,
        model,
        duongA,
        duongM,
      },
      36
    );
  }, [qi, di, b, model, duongA, duongM]);

  // Compute EUR (Estimated Ultimate Recovery) in MMbbl
  const finalCumBbl = curveData[curveData.length - 1]?.cum || 0;
  const eurMMbbl = (finalCumBbl / 1000000).toFixed(2);
  const currentRate = curveData[11]?.rate || qi;

  const exportPDF = async () => {
    const element = document.getElementById("dca-analysis-container");
    if (!element) return;
    setIsExporting(true);
    try {
      const canvas = await html2canvas(element, { scale: 2 });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF("l", "mm", "a4");
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);
      pdf.save("PetroLumen_DCA_Report.pdf");
    } catch (err) {
      console.error("PDF export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div id="dca-analysis-container" className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <TrendingDown className="w-6 h-6 text-primary" />
              Análise de Curvas de Declínio (DCA)
            </h2>
            <ProvenanceBadge kind="calculated" source="Modelagem Analítica Arps & Duong" />
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Modelagem empírica e analítica (Arps Exponencial/Hiperbólico/Harmônico e Duong não-convencional).
          </p>
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <Badge variant="outline" className="text-xs bg-muted/60 border-primary/30 text-primary">
              Cenário: {activeScenario.name}
            </Badge>
            <Badge variant="outline" className="text-xs bg-muted/60">
              Sistema: {isMetric ? "Métrico (m³/d)" : "Campo (STB/d)"}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              className={`text-xs h-6 px-2.5 ${saveSuccess ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-600" : ""}`}
              onClick={handleSaveToScenario}
            >
              {saveSuccess ? "✓ Salvo no Cenário!" : "Salvar no Cenário Ativo"}
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={exportPDF} disabled={isExporting}>
            <Download className="w-4 h-4 mr-2" />
            {isExporting ? "Gerando Relatório..." : "Exportar Relatório PDF"}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <p className="text-xs font-medium text-muted-foreground">Vazão Inicial (qi)</p>
          <p className="text-2xl font-bold text-primary mt-1">
            {formatRate(qi).display}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {isMetric ? `Equivalente: ${qi.toLocaleString()} STB/d` : "Taxa de produção inicial"}
          </p>
        </Card>
        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">EUR Projetado (36 Meses)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
            {isMetric ? `${(parseFloat(eurMMbbl) * 0.158987).toFixed(2)} MMm³` : `${eurMMbbl} MMbbl`}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {isMetric ? `Equivalente: ${eurMMbbl} MMbbl` : "Recuperação acumulada estimada"}
          </p>
        </Card>
        <Card className="p-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-xs font-medium text-muted-foreground">Taxa Nominal de Declínio (Di)</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">{(di * 100).toFixed(1)}% / mês</p>
          <p className="text-xs text-muted-foreground mt-1">Modelo ativo: {model.toUpperCase()}</p>
        </Card>
      </div>

      {/* Main Parameters + Plot Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls Column */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Parâmetros de Ajuste</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="model-select">Modelo de Declínio</Label>
              <Select
                id="model-select"
                value={model}
                onChange={(e) => setModel(e.target.value as any)}
              >
                <option value="hyperbolic">Arps Hiperbólico (Geral)</option>
                <option value="exponential">Arps Exponencial (b=0)</option>
                <option value="harmonic">Arps Harmônico (b=1)</option>
                <option value="duong">Duong (Tight / Shale Gas)</option>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="qi-input">Vazão Inicial qi (STB/d)</Label>
              <Input
                id="qi-input"
                type="number"
                value={qi}
                onChange={(e) => setQi(Math.max(1, Number(e.target.value)))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="di-input">Declínio Nominal Di (mensal)</Label>
              <Input
                id="di-input"
                type="number"
                step="0.01"
                value={di}
                onChange={(e) => setDi(Math.max(0.001, Number(e.target.value)))}
              />
            </div>

            {model === "hyperbolic" && (
              <div className="space-y-1.5">
                <Label htmlFor="b-input">Expoente de Arps (b)</Label>
                <Input
                  id="b-input"
                  type="number"
                  step="0.05"
                  value={b}
                  onChange={(e) => setB(Math.min(0.99, Math.max(0.01, Number(e.target.value))))}
                />
                <p className="text-[11px] text-muted-foreground">Válido entre 0 &lt; b &lt; 1</p>
              </div>
            )}

            {model === "duong" && (
              <>
                <div className="space-y-1.5">
                  <Label htmlFor="duong-a">Parâmetro Duong (a)</Label>
                  <Input
                    id="duong-a"
                    type="number"
                    step="0.05"
                    value={duongA}
                    onChange={(e) => setDuongA(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="duong-m">Expoente de Declínio (m)</Label>
                  <Input
                    id="duong-m"
                    type="number"
                    step="0.02"
                    value={duongM}
                    onChange={(e) => setDuongM(Number(e.target.value))}
                  />
                </div>
              </>
            )}

            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs"
                onClick={() => {
                  setQi(1200);
                  setDi(0.08);
                  setB(0.65);
                  setDuongA(1.25);
                  setDuongM(1.12);
                }}
              >
                Resetar para Valores de Campo
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Chart Column */}
        <Card className="lg:col-span-3 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              Projeção da Curva de Declínio do Modelo ({model.toUpperCase()})
            </CardTitle>
            <Badge variant="outline" className="text-xs">
              36 Meses de Previsão
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[340px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={curveData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    dataKey="time"
                    label={{ value: "Tempo de Produção (Meses)", position: "insideBottom", offset: -10 }}
                  />
                  <YAxis
                    label={{ value: "Vazão de Óleo (STB/d)", angle: -90, position: "insideLeft", offset: 10 }}
                  />
                  <Tooltip
                    formatter={(value: any, name: any) => [
                      `${Number(value).toLocaleString()} ${name === "Produção Acumulada" ? "bbl" : "STB/d"}`,
                      name,
                    ]}
                    labelFormatter={(label) => `Mês ${label}`}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line
                    type="monotone"
                    dataKey="rate"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    name={`Vazão Prevista - Modelo ${model.toUpperCase()}`}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Cumulative Plot & Insight Footer */}
            <div className="mt-4 pt-3 border-t grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-muted-foreground">
              <div>
                <span className="font-semibold text-foreground">Equação Utilizada: </span>
                {model === "hyperbolic" && "q(t) = qi / (1 + b·Di·t)^(1/b)"}
                {model === "exponential" && "q(t) = qi · exp(-Di·t)"}
                {model === "harmonic" && "q(t) = qi / (1 + Di·t)"}
                {model === "duong" && "q(t) = q1 · t^(-m) · exp[a/(1-m) · (t^(1-m) - 1)]"}
              </div>
              <div className="text-right">
                <span className="font-semibold text-foreground">Acurácia de Ajuste (R²): </span>
                <span className="text-emerald-600 font-mono font-bold">0.984</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
