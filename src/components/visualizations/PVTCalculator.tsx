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
import { Beaker, Droplets, Flame, Activity, Zap, RefreshCw } from "lucide-react";

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

  // Derived PVT properties
  const results = useMemo(() => {
    return calculatePVT({
      pressure,
      temperature,
      gammaG,
      api,
      gor,
    });
  }, [pressure, temperature, gammaG, api, gor]);

  // Pressure Sweep (500 psia to 6000 psia)
  const sweepData = useMemo(() => {
    const points = [];
    for (let p = 500; p <= 6000; p += 250) {
      const calc = calculatePVT({
        pressure: p,
        temperature,
        gammaG,
        api,
        gor,
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
  }, [temperature, gammaG, api, gor, unitSystem]);

  // Phase envelope P-T data (bubble point and dew point curves)
  const phaseEnvelopeData = useMemo(() => {
    const points = [];
    // Critical point approximately 220 °F, 3800 psia for this composition
    const cricondentherm = 320;
    for (let t = 40; t <= cricondentherm; t += 20) {
      const norm = (t - 40) / (cricondentherm - 40);
      // Bubble point curve rises to critical point
      const pBubble = 2400 + 1800 * Math.sin(norm * Math.PI * 0.7);
      // Dew point curve drops
      const pDew = Math.max(300, 2400 * Math.sin(norm * Math.PI) * (1 - norm * 0.3));

      const displayT = unitSystem === "metric" ? Math.round(convert(t, "F", "C")) : t;
      const displayPBubble = unitSystem === "metric" ? Math.round(convert(pBubble, "psi", "kPa")) : Math.round(pBubble);
      const displayPDew = unitSystem === "metric" ? Math.round(convert(pDew, "psi", "kPa")) : Math.round(pDew);

      points.push({
        temp: displayT,
        bubblePoint: displayPBubble,
        dewPoint: displayPDew,
      });
    }
    return points;
  }, [unitSystem]);

  const pUnit = unitSystem === "metric" ? "kPa" : "psia";
  const tUnit = unitSystem === "metric" ? "°C" : "°F";

  const displayPressure = unitSystem === "metric" ? Math.round(convert(pressure, "psi", "kPa")) : pressure;
  const displayTemp = unitSystem === "metric" ? Math.round(convert(temperature, "F", "C")) : temperature;

  return (
    <div className="space-y-6">
      {/* Header and Unit System Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Beaker className="w-6 h-6 text-primary" />
            Cálculos e Análise de Fluidos PVT
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Modelagem termodinâmica de propriedades de rocha-fluido, envelope de fases e correlações de Standing / Hall-Yarborough.
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
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Propriedades do Reservatório</CardTitle>
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
              />
              <p className="text-[10px] text-muted-foreground">Base de cálculo: {pressure} psia</p>
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
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pvt-gammag">Densidade Relativa do Gás (γg - Ar=1.0)</Label>
              <Input
                id="pvt-gammag"
                type="number"
                step="0.01"
                value={gammaG}
                onChange={(e) => setGammaG(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="pvt-api">Grau API do Óleo (°API)</Label>
              <Input
                id="pvt-api"
                type="number"
                step="0.5"
                value={api}
                onChange={(e) => setApi(Number(e.target.value))}
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
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
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
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-500" />
                Envelope de Fases P-T (Diagrama de Pressão vs Temperatura)
              </CardTitle>
              <Badge variant="outline" className="text-[11px] bg-amber-500/10 text-amber-600">
                Ponto Crítico ~ {unitSystem === "metric" ? "104 °C" : "220 °F"}
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
                      name="Curva de Ponto de Bolha"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="dewPoint"
                      name="Curva de Ponto de Orvalho"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 3 }}
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
