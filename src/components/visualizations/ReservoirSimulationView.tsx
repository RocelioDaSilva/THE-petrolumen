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
import { run1DReservoirSimulation } from "@/lib/reservoirMath";
import { Droplets, Play, RefreshCw, Activity, Layers } from "lucide-react";

export default function ReservoirSimulationView() {
  const [nx, setNx] = useState<number>(10);
  const [dx, setDx] = useState<number>(120); // ft
  const [permeability, setPermeability] = useState<number>(65); // mD
  const [porosity, setPorosity] = useState<number>(0.22);
  const [viscosity, setViscosity] = useState<number>(1.4); // cP
  const [pi, setPi] = useState<number>(3600); // psia
  const [dt, setDt] = useState<number>(10); // days
  const [nSteps, setNSteps] = useState<number>(20); // 200 days total
  const [wellRate, setWellRate] = useState<number>(-600); // STB/d

  const [isRunning, setIsRunning] = useState<boolean>(false);

  const history = useMemo(() => {
    return run1DReservoirSimulation({
      nx,
      dx,
      permeability,
      porosity,
      viscosity,
      compressibility: 1e-5,
      pi,
      dt,
      nSteps,
      wellRate,
    });
  }, [nx, dx, permeability, porosity, viscosity, pi, dt, nSteps, wellRate]);

  // Spatial pressure profile at final step
  const spatialProfile = useMemo(() => {
    const finalStep = history[history.length - 1];
    if (!finalStep) return [];
    return finalStep.pressures.map((press, i) => ({
      block: `B-${i + 1}`,
      distance: (i + 0.5) * dx,
      pressure: press,
    }));
  }, [history, dx]);

  const handleRun = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
    }, 400);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Droplets className="w-6 h-6 text-primary" />
            Simulação Numérica de Reservatórios (Modelo IMPES 1D)
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Solução por diferenças finitas para difusividade de pressão em meio poroso radial/linear com poço produtor no Bloco 1.
          </p>
        </div>
        <Button onClick={handleRun} disabled={isRunning} className="shadow-md">
          <Play className={`w-4 h-4 mr-2 ${isRunning ? "animate-spin" : ""}`} />
          {isRunning ? "Calculando Passos..." : "Executar Simulação"}
        </Button>
      </div>

      {/* Simulator Parameters + Output Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card className="lg:col-span-1 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">Parâmetros do Modelo</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="sim-nx">Número de Blocos (nx)</Label>
              <Input
                id="sim-nx"
                type="number"
                min="5"
                max="25"
                value={nx}
                onChange={(e) => setNx(Math.min(25, Math.max(5, Number(e.target.value))))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="sim-dx">Dimensão do Bloco dx (ft)</Label>
              <Input
                id="sim-dx"
                type="number"
                value={dx}
                onChange={(e) => setDx(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="sim-perm">Permeabilidade Absoluta (mD)</Label>
              <Input
                id="sim-perm"
                type="number"
                value={permeability}
                onChange={(e) => setPermeability(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="sim-phi">Porosidade (φ fracionária)</Label>
              <Input
                id="sim-phi"
                type="number"
                step="0.01"
                value={porosity}
                onChange={(e) => setPorosity(Number(e.target.value))}
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="sim-rate">Vazão do Poço Produtor (STB/d)</Label>
              <Input
                id="sim-rate"
                type="number"
                value={wellRate}
                onChange={(e) => setWellRate(Number(e.target.value))}
              />
              <p className="text-[10px] text-muted-foreground">Valor negativo indica produção</p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="sim-steps">Passos de Tempo (dt={dt} dias)</Label>
              <Input
                id="sim-steps"
                type="number"
                value={nSteps}
                onChange={(e) => setNSteps(Number(e.target.value))}
              />
              <p className="text-[10px] text-muted-foreground">Horizonte total: {nSteps * dt} dias</p>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-xs mt-2"
              onClick={() => {
                setNx(10);
                setDx(120);
                setPermeability(65);
                setPorosity(0.22);
                setViscosity(1.4);
                setPi(3600);
                setDt(10);
                setNSteps(20);
                setWellRate(-600);
              }}
            >
              <RefreshCw className="w-3 h-3 mr-2" />
              Resetar Modelo
            </Button>
          </CardContent>
        </Card>

        {/* Charts: Transient Pressure over Time & Spatial Gradient */}
        <div className="lg:col-span-3 space-y-6">
          {/* Pressure evolution over time */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                Depleção Temporal de Pressão (Poço vs Bloco Central)
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {nSteps * dt} Dias de Histórico
              </Badge>
            </CardHeader>
            <CardContent>
              <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="time"
                      label={{ value: "Tempo (Dias)", position: "insideBottom", offset: -10 }}
                    />
                    <YAxis
                      domain={["auto", "auto"]}
                      label={{ value: "Pressão (psia)", angle: -90, position: "insideLeft", offset: 0 }}
                    />
                    <Tooltip
                      formatter={(val: any, name: any) => [`${val} psia`, name]}
                      labelFormatter={(t) => `Dia ${t}`}
                    />
                    <Legend verticalAlign="top" height={36} />
                    <Line
                      type="monotone"
                      dataKey="wellbore"
                      stroke="#dc2626"
                      strokeWidth={2.5}
                      name="Bloco 1 (Poço Produtor)"
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="block5"
                      stroke="#2563eb"
                      strokeWidth={2.5}
                      name="Bloco Central (Meio do Reservatório)"
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Spatial pressure profile across grid */}
          <Card className="shadow-sm">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <Layers className="w-4 h-4 text-primary" />
                Perfil Espacial de Pressão no Reservatório (Dia {nSteps * dt})
              </CardTitle>
              <Badge variant="outline" className="text-xs font-mono">{nx} Blocos Discretizados</Badge>
            </CardHeader>
            <CardContent>
              <div className="h-[230px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={spatialProfile} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis
                      dataKey="distance"
                      label={{ value: "Distância do Poço (ft)", position: "insideBottom", offset: -10 }}
                    />
                    <YAxis
                      domain={["auto", "auto"]}
                      label={{ value: "Pressão (psia)", angle: -90, position: "insideLeft", offset: 0 }}
                    />
                    <Tooltip
                      formatter={(val: any) => [`${val} psia`, "Pressão"]}
                      labelFormatter={(d) => `${d} ft`}
                    />
                    <Line
                      type="monotone"
                      dataKey="pressure"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      name="Pressão do Grid"
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
