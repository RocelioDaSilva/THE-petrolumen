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
import { calculateFMBGas } from "@/lib/reservoirMath";
import { Target, Layers, Activity, RefreshCw } from "lucide-react";

export default function FlowingMaterialBalanceView() {
  const [pi, setPi] = useState<number>(3600); // psia
  const [tf, setTf] = useState<number>(175); // °F
  const [gammaG, setGammaG] = useState<number>(0.68);
  const [expectedOgip, setExpectedOgip] = useState<number>(1450); // MMscf

  const { points, ogip, slope } = useMemo(() => {
    return calculateFMBGas(pi, tf, gammaG, expectedOgip);
  }, [pi, tf, gammaG, expectedOgip]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Target className="w-6 h-6 text-primary" />
            Rate Transient Analysis & Balanço de Materiais (FMB)
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Flowing Material Balance para estimativa de gás original in-place (OGIP) e diagnóstico de mecanismos de suporte de pressão.
          </p>
        </div>
        <Badge variant="outline" className="text-sm px-3 py-1 bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400">
          OGIP Estimado: {(ogip / 1000).toFixed(2)} Bcf ({ogip.toLocaleString()} MMscf)
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <p className="text-xs font-medium text-muted-foreground">Pressão Inicial Pi</p>
          <p className="text-2xl font-bold text-primary mt-1 font-mono">{pi.toLocaleString()} psia</p>
          <p className="text-xs text-muted-foreground mt-1">Condição original virgem</p>
        </Card>
        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">OGIP Estimado (FMB)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {ogip.toLocaleString()} MMscf
          </p>
          <p className="text-xs text-muted-foreground mt-1">Interseção do eixo P/Z = 0</p>
        </Card>
        <Card className="p-4 bg-purple-500/5 border-purple-500/20">
          <p className="text-xs font-medium text-muted-foreground">Declive da Reta (dP/Z / dGp)</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1 font-mono">
            {slope} psia/MMscf
          </p>
          <p className="text-xs text-muted-foreground mt-1">Regime pseudoestacionário</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Parâmetros de Entrada RTA</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="fmb-pi">Pressão Estática Inicial Pi (psia)</Label>
              <Input
                id="fmb-pi"
                type="number"
                value={pi}
                onChange={(e) => setPi(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="fmb-tf">Temperatura do Reservatório (°F)</Label>
              <Input
                id="fmb-tf"
                type="number"
                value={tf}
                onChange={(e) => setTf(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="fmb-gamma">Densidade Relativa do Gás (γg)</Label>
              <Input
                id="fmb-gamma"
                type="number"
                step="0.01"
                value={gammaG}
                onChange={(e) => setGammaG(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="fmb-ogip">OGIP Esperado / Hipótese (MMscf)</Label>
              <Input
                id="fmb-ogip"
                type="number"
                step="50"
                value={expectedOgip}
                onChange={(e) => setExpectedOgip(Number(e.target.value))}
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setPi(3600);
                setTf(175);
                setGammaG(0.68);
                setExpectedOgip(1450);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Restaurar Parâmetros
            </Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Gráfico P/Z vs Produção Acumulada (Gp)</CardTitle>
            <Badge variant="outline" className="text-xs">Flowing Material Balance</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[340px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={points} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    dataKey="gp"
                    label={{ value: "Produção Acumulada Gp (MMscf)", position: "insideBottom", offset: -10 }}
                  />
                  <YAxis
                    label={{ value: "P/Z (psia)", angle: -90, position: "insideLeft", offset: 0 }}
                  />
                  <Tooltip
                    formatter={(val: any, name: any) => [`${val} psia`, name]}
                    labelFormatter={(gp) => `Gp: ${gp} MMscf`}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line
                    type="monotone"
                    dataKey="pz"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    name="P/Z Histórico & Projetado"
                    dot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="pwf"
                    stroke="#f59e0b"
                    strokeWidth={2}
                    name="Pressão de Fundo de Fluxo (Pwf)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="p-3 bg-muted/30 rounded border text-xs text-muted-foreground mt-2">
              <span className="font-semibold text-foreground">Diagnóstico de Mecanismo de Drive: </span>
              A linearidade pura da curva P/Z confirma comportamento volumétrico com depleção por expansão de gás, sem influxo significativo de aquífero ativo no estágio atual.
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
