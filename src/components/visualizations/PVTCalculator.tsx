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
import { calculatePVT, calculateZFactor } from "@/lib/reservoirMath";
import { convert, UnitSystem } from "@/lib/units";
import { sanitizePVT } from "@/lib/pvt/sanitize";
import { Beaker, Droplets, Flame, Activity, Zap, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react";
import { ProvenanceBadge } from "@/components/ui/ProvenanceBadge";

interface ComponentEntry {
  name: string;
  formula: string;
  moleFrac: number;
  mw: number;
  tc: number; // °R
  pc: number; // psia
}

export default function PVTCalculator() {
  const [unitSystem, setUnitSystem] = useState<UnitSystem>("field");
  const [pressure, setPressure] = useState<number>(3200); // psia
  const [temperature, setTemperature] = useState<number>(180); // °F
  const [gammaG, setGammaG] = useState<number>(0.72);
  const [api, setApi] = useState<number>(34.5);
  const [gor, setGor] = useState<number>(650);

  // Composition table
  const [composition, setComposition] = useState<ComponentEntry[]>([
    { name: "Metano", formula: "C1", moleFrac: 0.65, mw: 16.04, tc: 343.0, pc: 667.8 },
    { name: "Etano", formula: "C2", moleFrac: 0.08, mw: 30.07, tc: 549.8, pc: 707.8 },
    { name: "Propano", formula: "C3", moleFrac: 0.05, mw: 44.1, tc: 665.7, pc: 616.3 },
    { name: "i-Butano", formula: "i-C4", moleFrac: 0.02, mw: 58.12, tc: 734.7, pc: 529.1 },
    { name: "n-Butano", formula: "n-C4", moleFrac: 0.03, mw: 58.12, tc: 765.3, pc: 550.7 },
    { name: "Pentanos+", formula: "C5+", moleFrac: 0.05, mw: 82.0, tc: 880.0, pc: 480.0 },
    { name: "Heptanos+", formula: "C7+", moleFrac: 0.08, mw: 142.0, tc: 1100.0, pc: 340.0 },
    { name: "Nitrogênio", formula: "N2", moleFrac: 0.01, mw: 28.01, tc: 227.3, pc: 493.0 },
    { name: "Dióxido Carbono", formula: "CO2", moleFrac: 0.03, mw: 44.01, tc: 547.4, pc: 1071.0 },
  ]);

  // PVT Input Validation using strict sanitizer
  const validation = useMemo(() => {
    return sanitizePVT({
      pressure,
      temperature,
      gasGravity: gammaG,
      apiGravity: api,
      gor,
      unitSystem,
    });
  }, [pressure, temperature, gammaG, api, gor, unitSystem]);

  const validationErrors = 'errors' in validation ? validation.errors : [];

  // Derived PVT properties (calculated safely using validated values or fallback)
  const results = useMemo(() => {
    const p = validation.ok ? validation.value.pressure : Math.max(14.7, pressure || 3200);
    const t = validation.ok ? validation.value.temperature : Math.max(32, temperature || 180);
    const gg = validation.ok ? validation.value.gasGravity : 0.72;
    const oApi = validation.ok ? validation.value.apiGravity : 35;
    const rGor = validation.ok ? validation.value.gor : 600;

    return calculatePVT({
      pressure: p,
      temperature: t,
      gammaG: gg,
      api: oApi,
      gor: rGor,
    });
  }, [validation, pressure, temperature]);

  // Pressure Sweep (500 psia to 6000 psia)
  const sweepData = useMemo(() => {
    const t = validation.ok ? validation.value.temperature : 180;
    const gg = validation.ok ? validation.value.gasGravity : 0.72;
    const oApi = validation.ok ? validation.value.apiGravity : 35;
    const rGor = validation.ok ? validation.value.gor : 600;

    const points = [];
    for (let p = 500; p <= 6000; p += 250) {
      const calc = calculatePVT({
        pressure: p,
        temperature: t,
        gammaG: gg,
        api: oApi,
        gor: rGor,
      });

      const displayP = unitSystem === "metric" ? Math.round(convert(p, "psi", "kPa")) : p;

      points.push({
        pressure: displayP,
        zFactor: calc.zFactor,
        bo: calc.bo,
        rs: calc.rs,
        oilViscosity: calc.oilViscosity,
      });
    }
    return points;
  }, [validation, unitSystem]);

  // Phase envelope P-T data (Standing correlation bubble point curve)
  const phaseEnvelopeData = useMemo(() => {
    const points = [];
    const minTemp = 60;
    const maxTemp = 300;
    for (let t = minTemp; t <= maxTemp; t += 15) {
      // Standing (1947) Bubble point pressure as function of temperature
      const standingPb = 18.2 * (
        Math.pow(gor / Math.max(0.4, gammaG), 0.83) *
        Math.pow(10, 0.00091 * t - 0.0125 * api) - 1.4
      );
      const pBubble = Math.max(50, Math.round(standingPb));

      const displayT = unitSystem === "metric" ? Math.round(convert(t, "F", "C")) : t;
      const displayPBubble = unitSystem === "metric" ? Math.round(convert(pBubble, "psi", "kPa")) : pBubble;

      points.push({
        temp: displayT,
        bubblePoint: displayPBubble,
      });
    }
    return points;
  }, [gor, gammaG, api, unitSystem]);

  const pUnit = unitSystem === "metric" ? "kPa" : "psia";
  const tUnit = unitSystem === "metric" ? "°C" : "°F";

  const displayPressure = unitSystem === "metric" ? Math.round(convert(pressure, "psi", "kPa")) : pressure;
  const displayTemp = unitSystem === "metric" ? Math.round(convert(temperature, "F", "C")) : temperature;

  return (
    <div className="space-y-6">
      {/* Header and Unit System Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Beaker className="w-6 h-6 text-primary" />
              Cálculos e Análise de Fluidos PVT
            </h2>
            <Badge variant="outline" className={validation.ok ? "text-emerald-600 border-emerald-500/30 bg-emerald-500/10" : "text-amber-600 border-amber-500/30 bg-amber-500/10"}>
              {validation.ok ? (
                <span className="flex items-center gap-1"><CheckCircle2 className="w-3 h-3 text-emerald-500" /> Inputs Validados</span>
              ) : (
                <span className="flex items-center gap-1"><AlertCircle className="w-3 h-3 text-amber-500" /> Atenção / Limites Físicos</span>
              )}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Modelagem termodinâmica de propriedades de rocha-fluido, envelope de fases e correlações de Standing / Hall-Yarborough com sanitização científica contra divisão por zero e pressões nulas.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-muted-foreground">Sistema de Unidades:</span>
          <div className="inline-flex rounded-md border p-1 bg-muted/40">
            <Button
              size="sm"
              variant={unitSystem === "field" ? "default" : "ghost"}
              className="text-xs h-7 px-3"
              onClick={() => setUnitSystem("field")}
            >
              Campo (Field)
            </Button>
            <Button
              size="sm"
              variant={unitSystem === "metric" ? "default" : "ghost"}
              className="text-xs h-7 px-3"
              onClick={() => setUnitSystem("metric")}
            >
              Métrico (SI)
            </Button>
          </div>
        </div>
      </div>

      {/* Validation Alert Banner if inputs are out of bounds */}
      {!validation.ok && (
        <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/10 text-red-900 dark:text-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-red-600 dark:text-red-400">
                Aviso de Inconsistência nos Dados Termodinâmicos (Fail-Loudly Guard)
              </p>
              <ul className="text-xs space-y-0.5 list-disc list-inside">
                {validationErrors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
              <p className="text-[11px] text-muted-foreground mt-1">
                Os cálculos termodinâmicos foram protegidos contra divisão por zero e singularidades. Por favor corrija os parâmetros acima.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Fator Z (Gás)</p>
          <p className="text-xl font-bold text-primary mt-1 font-mono">{results.zFactor}</p>
          <p className="text-[10px] text-muted-foreground">Hall-Yarborough</p>
        </Card>
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Bo (FVF Óleo)</p>
          <p className="text-xl font-bold text-foreground mt-1 font-mono">
            {results.bo} <span className="text-xs font-normal text-muted-foreground">bbl/STB</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Standing Correlation</p>
        </Card>
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Bg (FVF Gás)</p>
          <p className="text-xl font-bold text-foreground mt-1 font-mono">
            {results.bg} <span className="text-xs font-normal text-muted-foreground">bbl/scf</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Fator Volumétrico</p>
        </Card>
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Rs (Solubilidade)</p>
          <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {results.rs} <span className="text-xs font-normal text-muted-foreground">scf/STB</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Razão Gás-Óleo</p>
        </Card>
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Pressão de Bolha (Pb)</p>
          <p className="text-xl font-bold text-amber-600 dark:text-amber-400 mt-1 font-mono">
            {unitSystem === "metric" ? Math.round(convert(results.pb, "psi", "kPa")) : results.pb}{" "}
            <span className="text-xs font-normal text-muted-foreground">{pUnit}</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Ponto de Saturação</p>
        </Card>
        <Card className="p-3 bg-card border">
          <p className="text-[11px] font-medium text-muted-foreground">Viscosidade Óleo (μo)</p>
          <p className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {results.oilViscosity} <span className="text-xs font-normal text-muted-foreground">cP</span>
          </p>
          <p className="text-[10px] text-muted-foreground">Beggs-Robinson</p>
        </Card>
      </div>

      {/* Input Parameters + Plot Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Parameters Form */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3 flex flex-row items-center justify-between">
            <CardTitle className="text-base font-semibold">Propriedades do Reservatório</CardTitle>
            <Badge variant="outline" className="text-[10px]">
              Sanitização Ativa
            </Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <Label htmlFor="pvt-p">Pressão ({pUnit})</Label>
                <span className="text-xs font-mono font-bold text-primary">{displayPressure}</span>
              </div>
              <Input
                id="pvt-p"
                type="number"
                value={pressure}
                onChange={(e) => setPressure(Number(e.target.value))}
                className={pressure <= 0 ? "border-red-500 focus-visible:ring-red-500" : ""}
              />
              <p className="text-[10px] text-muted-foreground">
                Base de cálculo: {pressure} psia (deve ser estritamente &gt; 0)
              </p>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between items-center">
                <Label htmlFor="pvt-t">Temperatura ({tUnit})</Label>
                <span className="text-xs font-mono font-bold text-primary">{displayTemp}</span>
              </div>
              <Input
                id="pvt-t"
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className={temperature <= -459.67 ? "border-red-500 focus-visible:ring-red-500" : ""}
              />
              <p className="text-[10px] text-muted-foreground">Zero absoluto: -459.67 °F / -273.15 °C</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pvt-gammag">Densidade Relativa do Gás (γg - Ar=1.0)</Label>
              <Input
                id="pvt-gammag"
                type="number"
                step="0.01"
                value={gammaG}
                onChange={(e) => setGammaG(Number(e.target.value))}
                className={gammaG < 0.5 || gammaG > 2.0 ? "border-amber-500" : ""}
              />
              <p className="text-[10px] text-muted-foreground">Faixa típica de hidrocarbonetos: 0.55 - 1.20</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pvt-api">Grau API do Óleo (°API)</Label>
              <Input
                id="pvt-api"
                type="number"
                step="0.5"
                value={api}
                onChange={(e) => setApi(Number(e.target.value))}
                className={api <= 0 || api > 100 ? "border-red-500" : ""}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pvt-gor">Razão Gás-Óleo de Produção (GOR, scf/STB)</Label>
              <Input
                id="pvt-gor"
                type="number"
                step="10"
                value={gor}
                onChange={(e) => setGor(Number(e.target.value))}
                className={gor < 0 ? "border-red-500" : ""}
              />
            </div>

            <div className="pt-2 space-y-2">
              <Button
                variant="outline"
                size="sm"
                className="w-full text-xs"
                onClick={() => {
                  setPressure(3200);
                  setTemperature(180);
                  setGammaG(0.72);
                  setApi(34.5);
                  setGor(650);
                }}
              >
                <RefreshCw className="w-3 h-3 mr-2" />
                Restaurar Parâmetros Padrão
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-[11px] text-amber-600 hover:text-amber-700"
                onClick={() => {
                  setPressure(0); // Test boundary
                }}
              >
                Testar Rejeição Estrita (P = 0)
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Charts: Z-Factor Sweep & Phase Envelope */}
        <div className="lg:col-span-2 space-y-6">
          {/* Z-Factor vs Pressure */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Variação de Z-Factor e FVF de Óleo (Bo) vs Pressão
              </CardTitle>
              <Badge variant="outline" className="text-[11px]">Varredura 500 - 6000 {pUnit}</Badge>
            </CardHeader>
            <CardContent>
              <div className="h-[240px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={sweepData} margin={{ top: 5, right: 20, left: 0, bottom: 15 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="pressure"
                      label={{ value: `Pressão (${pUnit})`, position: "insideBottom", offset: -8 }}
                    />
                    <YAxis yAxisId="left" domain={[0.6, 1.3]} />
                    <YAxis yAxisId="right" orientation="right" domain={[1.0, 1.8]} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={30} />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="zFactor"
                      name="Fator Z do Gás"
                      stroke="#8884d8"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="bo"
                      name="Bo (bbl/STB)"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Phase Envelope (P-T Diagram) */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Flame className="w-4 h-4 text-amber-500" />
                  Curva de Ponto de Bolha vs Temperatura (Standing 1947)
                </CardTitle>
                <ProvenanceBadge kind="calculated" source="Standing Pb(T)" />
              </div>
              <Badge variant="outline" className="text-[11px] bg-emerald-500/10 text-emerald-600">
                Pb @ {displayTemp}{tUnit}: {results.pb} {pUnit}
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="h-[220px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={phaseEnvelopeData} margin={{ top: 5, right: 20, left: 0, bottom: 15 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="temp"
                      label={{ value: `Temperatura (${tUnit})`, position: "insideBottom", offset: -8 }}
                    />
                    <YAxis label={{ value: `Pressão (${pUnit})`, angle: -90, position: "insideLeft", offset: 10 }} />
                    <Tooltip />
                    <Legend verticalAlign="top" height={30} />
                    <Line
                      type="monotone"
                      dataKey="bubblePoint"
                      name={`Ponto de Bolha Standing (Pb)`}
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Fluid Composition Editor Table */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Droplets className="w-4 h-4 text-primary" />
            Composição Molar do Fluido de Reservatório
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-muted text-muted-foreground uppercase text-[10px]">
                <tr>
                  <th className="p-2.5">Componente</th>
                  <th className="p-2.5">Fórmula</th>
                  <th className="p-2.5">Fração Molar (zi)</th>
                  <th className="p-2.5">Peso Molecular (g/mol)</th>
                  <th className="p-2.5">Temp. Crítica Tc (°R)</th>
                  <th className="p-2.5">Pressão Crítica Pc (psia)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {composition.map((comp, idx) => (
                  <tr key={comp.formula} className="hover:bg-muted/30">
                    <td className="p-2.5 font-medium">{comp.name}</td>
                    <td className="p-2.5 font-mono text-primary font-bold">{comp.formula}</td>
                    <td className="p-2.5">
                      <Input
                        type="number"
                        step="0.01"
                        className="h-7 w-20 text-xs font-mono"
                        value={comp.moleFrac}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setComposition((prev) =>
                            prev.map((c, i) => (i === idx ? { ...c, moleFrac: val } : c))
                          );
                        }}
                      />
                    </td>
                    <td className="p-2.5 font-mono">{comp.mw}</td>
                    <td className="p-2.5 font-mono">{comp.tc}</td>
                    <td className="p-2.5 font-mono">{comp.pc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
