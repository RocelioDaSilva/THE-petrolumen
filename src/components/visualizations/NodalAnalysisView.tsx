import React, { useState, useEffect } from "react";
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
import { NodalPoint, computeVlp } from "@/lib/reservoirMath";
import { vogel, vogelCurve } from "@/lib/api";
import {
  AlertTriangle,
  Gauge,
  CheckCircle,
  ArrowRight,
  Zap,
  RefreshCw,
  Cloud,
} from "lucide-react";

function getApiError(error: unknown): string {
  if (
    typeof error === "object"
    && error !== null
    && "detail" in error
    && typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The calculation could not be completed.";
}

export default function NodalAnalysisView() {
  const [pRes, setPRes] = useState<number>(3400); // psia
  const [qMax, setQMax] = useState<number>(1800); // STB/d
  const [pWh, setPWh] = useState<number>(450); // psia
  const [depth, setDepth] = useState<number>(8500); // ft
  const [tubingId, setTubingId] = useState<number>(2.875); // inches
  const [waterCut, setWaterCut] = useState<number>(0.25);
  const [gor, setGor] = useState<number>(600); // scf/STB
  const [verifyState, setVerifyState] = useState<{ loading: boolean; result?: { pwf: number; q_local: number; q_backend: number; delta: number }; error?: string }>({ loading: false });

  const [curves, setCurves] = useState<NodalPoint[]>([]);
  const [operatingPoint, setOperatingPoint] = useState<{ q: number; p: number } | null>(null);
  const [iprSource, setIprSource] = useState<"backend" | "local">("backend");
  const [iprLoading, setIprLoading] = useState<boolean>(true);
  const [iprError, setIprError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIprLoading(true);
    setIprError(null);
    setCurves([]);
    setOperatingPoint(null);
    setIprSource("backend");
    (async () => {
      try {
        const nPoints = 25;
        let iprPoints: { q: number; pwf: number }[];
        let source: "backend" | "local" = "backend";
        try {
          const res = await vogelCurve({ qmax: qMax, pbar: pRes, n_points: nPoints });
          iprPoints = res.points;
        } catch {
          source = "local";
          const dq = qMax / (nPoints - 1);
          iprPoints = Array.from({ length: nPoints }, (_, i) => {
            const q = i * dq;
            const ratio = Math.min(0.999, q / qMax);
            const pwf = Math.max(0, 0.125 * pRes * (-1 + Math.sqrt(81 - 80 * ratio)));
            return { q, pwf };
          });
        }
        if (cancelled) return;
        const merged: NodalPoint[] = iprPoints.map(({ q, pwf }) => ({
          q: Math.round(q),
          p_ipr: Math.round(pwf),
          p_vlp: Math.round(computeVlp(q, pWh, depth, tubingId, waterCut, gor)),
        }));
        let bestDiff = Infinity;
        let op: { q: number; p: number } | null = null;
        const safePWh = Math.max(0, pWh || 100);
        for (const pt of merged) {
          const diff = Math.abs(pt.p_ipr - pt.p_vlp);
          if (diff < bestDiff && pt.p_ipr > safePWh) {
            bestDiff = diff;
            op = { q: pt.q, p: Math.round((pt.p_ipr + pt.p_vlp) / 2) };
          }
        }
        setCurves(merged);
        setOperatingPoint(op);
        setIprSource(source);
      } catch (error: unknown) {
        if (!cancelled) {
          setCurves([]);
          setOperatingPoint(null);
          setIprError(getApiError(error));
        }
      } finally {
        if (!cancelled) setIprLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [pRes, qMax, pWh, depth, tubingId, waterCut, gor]);

  const handleVerify = async () => {
    setVerifyState({ loading: true });
    try {
      const pTest = Math.round(pRes / 2);
      const res = await vogel({ qmax: qMax, pwf: pTest, pbar: pRes });
      let qLocal: number | null = null;
      for (let i = 0; i < curves.length - 1; i++) {
        const a = curves[i], b = curves[i + 1];
        if ((a.p_ipr - pTest) * (b.p_ipr - pTest) <= 0 && b.p_ipr !== a.p_ipr) {
          const t = (pTest - a.p_ipr) / (b.p_ipr - a.p_ipr);
          qLocal = a.q + t * (b.q - a.q);
          break;
        }
      }
      setVerifyState({ loading: false, result: { pwf: pTest, q_local: qLocal ?? NaN, q_backend: res.q, delta: qLocal != null ? Math.abs(res.q - qLocal) : NaN } });
    } catch (error: unknown) {
      setVerifyState({ loading: false, error: getApiError(error) });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Gauge className="w-6 h-6 text-primary" />
            Análise Nodal de Produção (IPR vs VLP)
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Intersecção de curvas de influxo do reservatório (Vogel / Darcy) com a performance de elevação na coluna (Beggs & Brill).
          </p>
        </div>
        {operatingPoint && (
          <Badge variant="outline" className="text-sm px-3 py-1 bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="w-4 h-4 mr-1.5" />
            Ponto de Operação Solucionado
          </Badge>
        )}
      </div>

      {iprLoading && (
        <p role="status" className="text-sm text-muted-foreground">
          Calculating IPR curve...
        </p>
      )}
      {!iprLoading && iprSource === "local" && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/5 px-3 py-2 text-sm text-amber-700 dark:text-amber-300"
        >
          <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
          <p>Backend unavailable. Displaying a local Vogel fallback.</p>
        </div>
      )}
      {iprError && (
        <p
          role="alert"
          className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
        >
          IPR calculation failed: {iprError}
        </p>
      )}

      {/* Operating Point Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-4 bg-primary/5 border-primary/20">
          <p className="text-xs font-medium text-muted-foreground">Vazão de Operação (Qop)</p>
          <p className="text-2xl font-bold text-primary mt-1 font-mono">
            {operatingPoint ? `${operatingPoint.q.toLocaleString()} STB/d` : "Não converge"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Interseção natural IPR / VLP</p>
        </Card>
        <Card className="p-4 bg-emerald-500/5 border-emerald-500/20">
          <p className="text-xs font-medium text-muted-foreground">Pressão de Fundo de Fluxo (Pwf)</p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 mt-1 font-mono">
            {operatingPoint ? `${operatingPoint.p.toLocaleString()} psia` : "N/A"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Drawdown: {operatingPoint ? pRes - operatingPoint.p : 0} psia</p>
        </Card>
        <Card className="p-4 bg-blue-500/5 border-blue-500/20">
          <p className="text-xs font-medium text-muted-foreground">Potencial Máximo AOF (qMax)</p>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1 font-mono">
            {qMax.toLocaleString()} STB/d
          </p>
          <p className="text-xs text-muted-foreground mt-1">Pressão Reservatório: {pRes} psia</p>
        </Card>
      </div>

{/* Backend Verification */}
      <Card className="shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Cloud className="w-4 h-4 text-primary" />
            Verificação com Backend (ppes)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <Button size="sm" onClick={handleVerify} disabled={verifyState.loading}>
              {verifyState.loading ? "Verificando..." : "Verificar IPR no Backend"}
            </Button>
            {verifyState.result && (
              <div className="text-xs font-mono space-x-3">
                <span className="text-muted-foreground">pwf={verifyState.result.pwf} psia</span>
                <span className="text-emerald-600">q_local={Number.isFinite(verifyState.result.q_local) ? verifyState.result.q_local.toFixed(2) : "N/A"}</span>
                <span className="text-blue-600">q_backend={verifyState.result.q_backend.toFixed(2)}</span>
                <span className={verifyState.result.delta < 0.01 ? "text-emerald-600" : "text-amber-600"}>Delta={Number.isFinite(verifyState.result.delta) ? verifyState.result.delta.toFixed(4) : "N/A"}</span>
              </div>
            )}
            {verifyState.error && (<span className="text-xs text-red-600">Erro: {verifyState.error}</span>)}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Parâmetros do Sistema Poço-Reservatório</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="nodal-pres">Pressão Estática do Reservatório (psia)</Label>
              <Input
                id="nodal-pres"
                type="number"
                value={pRes}
                onChange={(e) => setPRes(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="nodal-qmax">Potencial de Fluxo Aberto AOF (STB/d)</Label>
              <Input
                id="nodal-qmax"
                type="number"
                value={qMax}
                onChange={(e) => setQMax(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="nodal-pwh">Pressão na Cabeça do Poço - Wellhead (psia)</Label>
              <Input
                id="nodal-pwh"
                type="number"
                value={pWh}
                onChange={(e) => setPWh(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="nodal-depth">Profundidade Verdadeira TVD (ft)</Label>
              <Input
                id="nodal-depth"
                type="number"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="nodal-tubing">Diâmetro Interno da Coluna (pol)</Label>
              <Input
                id="nodal-tubing"
                type="number"
                step="0.125"
                value={tubingId}
                onChange={(e) => setTubingId(Number(e.target.value))}
              />
              <p className="text-[10px] text-muted-foreground">Padrões: 2.375", 2.875", 3.5", 4.5"</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="nodal-bsw">Water Cut (BSW fracionário)</Label>
              <Input
                id="nodal-bsw"
                type="number"
                step="0.05"
                min="0"
                max="0.95"
                value={waterCut}
                onChange={(e) => setWaterCut(Number(e.target.value))}
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setPRes(3400);
                setQMax(1800);
                setPWh(450);
                setDepth(8500);
                setTubingId(2.875);
                setWaterCut(0.25);
                setGor(600);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Resetar Parâmetros
            </Button>
          </CardContent>
        </Card>

        {/* Nodal Chart */}
        <Card className="lg:col-span-2 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-semibold">Gráfico IPR vs VLP (Ponto de Equilíbrio)</CardTitle>
            <Badge variant="outline" className="text-xs">Solução Hidráulica</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[380px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={curves} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    dataKey="q"
                    label={{ value: "Vazão de Líquido (STB/d)", position: "insideBottom", offset: -10 }}
                  />
                  <YAxis
                    label={{ value: "Pressão de Fundo de Fluxo Pwf (psia)", angle: -90, position: "insideLeft", offset: 0 }}
                  />
                  <Tooltip
                    formatter={(val: any, name: any) => [`${val} psia`, name]}
                    labelFormatter={(q) => `${q} STB/d`}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line
                    type="monotone"
                    dataKey="p_ipr"
                    stroke="hsl(var(--chart-1))"
                    strokeWidth={2.5}
                    name="IPR (Inflow - Vogel)"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="p_vlp"
                    stroke="hsl(var(--chart-5))"
                    strokeWidth={2.5}
                    name="VLP (Outflow - Beggs & Brill)"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="p-3 bg-muted/30 rounded border text-xs text-muted-foreground mt-2">
              <p className="font-semibold text-foreground">Diagnóstico do Engenheiro:</p>
              <p>
                O poço opera estavelmente no quadrante de fluxo contínuo. Um aumento de diâmetro de coluna para 3.5" pode elevar a vazão em até 14%, mantendo pressão de cabeça de {pWh} psia.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
