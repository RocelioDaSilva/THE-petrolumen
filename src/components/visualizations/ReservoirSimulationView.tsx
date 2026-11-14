import React, { useMemo, useState } from "react";
import {
  Activity,
  ChevronDown,
  Droplets,
  Gauge,
  Layers,
  LoaderCircle,
  Play,
  RefreshCw,
} from "lucide-react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { run1DReservoirSimulation } from "@/lib/reservoirMath";
import { useSessionRegistry } from "@/lib/sessionRegistry";
import {
  createSavedSimulation,
  SavedSimulation,
} from "@/lib/api";
import { useAuth } from "@/lib/authContext";

const axisColor = "hsl(var(--muted-foreground))";
const gridColor = "hsl(var(--border))";
const tooltipStyle: React.CSSProperties = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "0.75rem",
  color: "hsl(var(--popover-foreground))",
};

interface ReservoirSimulationViewProps {
  savedRun?: SavedSimulation | null;
}

interface ReservoirSimulationInputs {
  nx: number;
  dx: number;
  permeability: number;
  porosity: number;
  viscosity: number;
  pi: number;
  dt: number;
  nSteps: number;
  wellRate: number;
}

function isReservoirSimulationInputs(
  input: Record<string, unknown>,
): input is Record<string, unknown> & ReservoirSimulationInputs {
  return [
    input.nx,
    input.dx,
    input.permeability,
    input.porosity,
    input.viscosity,
    input.pi,
    input.dt,
    input.nSteps,
    input.wellRate,
  ].every((value) => typeof value === "number" && Number.isFinite(value));
}

export default function ReservoirSimulationView({ savedRun = null }: ReservoirSimulationViewProps) {
  const { activeScenario, updateActiveParameters } = useSessionRegistry();
  const { user, openAuthDialog } = useAuth();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [savedRunMessage, setSavedRunMessage] = useState("");
  const [saveRunError, setSaveRunError] = useState("");
  const [isSavingRun, setIsSavingRun] = useState(false);
  const [nx, setNx] = useState(10);
  const [dx, setDx] = useState(120);
  const [permeability, setPermeability] = useState(
    activeScenario?.parameters?.permeabilityMd ?? 65,
  );
  const [porosity, setPorosity] = useState(
    activeScenario?.parameters?.porosityFraction ?? 0.22,
  );
  const [viscosity, setViscosity] = useState(1.4);
  const [pi, setPi] = useState(
    activeScenario?.parameters?.reservoirPressurePsia ?? 3600,
  );
  const [dt, setDt] = useState(10);
  const [nSteps, setNSteps] = useState(20);
  const [wellRate, setWellRate] = useState(-600);
  const [isRunning, setIsRunning] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  React.useEffect(() => {
    if (activeScenario?.parameters) {
      const parameters = activeScenario.parameters;
      if (parameters.permeabilityMd) setPermeability(parameters.permeabilityMd);
      if (parameters.porosityFraction) setPorosity(parameters.porosityFraction);
      if (parameters.reservoirPressurePsia) setPi(parameters.reservoirPressurePsia);
    }
  }, [activeScenario?.id]);

  React.useEffect(() => {
    if (!savedRun || savedRun.simulation_type !== "reservoir-simulation") return;
    const values = savedRun.input_data;
    if (!isReservoirSimulationInputs(values)) {
      setSaveRunError("This saved run has incomplete or invalid model inputs.");
      return;
    }

    setNx(values.nx);
    setDx(values.dx);
    setPermeability(values.permeability);
    setPorosity(values.porosity);
    setViscosity(values.viscosity);
    setPi(values.pi);
    setDt(values.dt);
    setNSteps(values.nSteps);
    setWellRate(values.wellRate);
    setHasRun(true);
    setSaveRunError("");
    setSavedRunMessage(`Loaded saved run: ${savedRun.name}`);
  }, [savedRun]);

  const handleSaveToScenario = () => {
    updateActiveParameters({
      permeabilityMd: permeability,
      porosityFraction: porosity,
      reservoirPressurePsia: pi,
    });
    setSaveSuccess(true);
    window.setTimeout(() => setSaveSuccess(false), 2500);
  };

  const history = useMemo(
    () =>
      run1DReservoirSimulation({
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
      }),
    [nx, dx, permeability, porosity, viscosity, pi, dt, nSteps, wellRate],
  );

  const spatialProfile = useMemo(() => {
    const finalStep = history[history.length - 1];
    if (!finalStep) return [];
    return finalStep.pressures.map((pressure, index) => ({
      block: `B-${index + 1}`,
      distance: (index + 0.5) * dx,
      pressure,
    }));
  }, [history, dx]);

  const handleRun = () => {
    setSavedRunMessage("");
    setSaveRunError("");
    setIsRunning(true);
    window.setTimeout(() => {
      setHasRun(true);
      setIsRunning(false);
    }, 350);
  };

  const handleSaveRun = async () => {
    if (!user) {
      openAuthDialog();
      return;
    }
    setIsSavingRun(true);
    setSaveRunError("");
    try {
      await createSavedSimulation({
        name: `${activeScenario.name} • Reservoir run ${new Date().toLocaleString()}`.slice(0, 120),
        simulation_type: "reservoir-simulation",
        input_data: {
          nx,
          dx,
          permeability,
          porosity,
          viscosity,
          pi,
          dt,
          nSteps,
          wellRate,
          scenario: activeScenario.name,
        },
        result_data: {
          history,
          finalPressure,
          pressureDrop,
        },
      });
      setSavedRunMessage("Run saved. Find it in My Saved Runs on the dashboard.");
    } catch (error) {
      setSaveRunError(getApiError(error));
    } finally {
      setIsSavingRun(false);
    }
  };

  const resetModel = () => {
    setNx(10);
    setDx(120);
    setPermeability(65);
    setPorosity(0.22);
    setViscosity(1.4);
    setPi(3600);
    setDt(10);
    setNSteps(20);
    setWellRate(-600);
    setHasRun(false);
  };

  const finalStep = history[history.length - 1];
  const finalPressure = finalStep?.wellbore ?? pi;
  const pressureDrop = Math.max(0, pi - finalPressure);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            {activeScenario.name}
          </div>
          <h2 className="flex items-center gap-2 text-xl font-semibold tracking-tight sm:text-2xl">
            <Droplets className="h-6 w-6 shrink-0 text-primary" />
            Simulação de Reservatórios
          </h2>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Modelo IMPES 1D para avaliar a evolução da pressão e o perfil espacial do reservatório.
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className={`h-9 ${saveSuccess ? "border-primary/40 bg-primary/10 text-primary" : ""}`}
            onClick={handleSaveToScenario}
          >
            {saveSuccess ? "Salvo no cenário" : "Salvar parâmetros"}
          </Button>
          {hasRun && (
            <Button
              variant="outline"
              onClick={() => void handleSaveRun()}
              disabled={isSavingRun}
              className="h-9 gap-2"
            >
              {isSavingRun && <LoaderCircle className="h-4 w-4 animate-spin" />}
              {isSavingRun ? "Saving..." : "Save run"}
            </Button>
          )}
          <Button onClick={handleRun} disabled={isRunning} className="h-9 gap-2 shadow-sm">
            {isRunning ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isRunning ? "Calculando..." : "Executar"}
          </Button>
        </div>
      </div>

      {savedRunMessage && (
        <p role="status" className="rounded-lg border border-primary/25 bg-primary/10 px-3 py-2 text-xs text-primary">
          {savedRunMessage}
        </p>
      )}
      {saveRunError && (
        <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {saveRunError}
        </p>
      )}

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(18rem,2fr)_minmax(0,3fr)]">
        <Card className="overflow-hidden">
          <CardHeader className="border-b border-border px-5 py-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-sm font-semibold">Configuração do modelo</CardTitle>
                <p className="mt-1 text-xs text-muted-foreground">Defina os parâmetros principais da malha e do poço.</p>
              </div>
              <Badge variant="outline" className="shrink-0 font-mono text-[10px] text-muted-foreground">
                IMPES · 1D
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 p-5">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="sim-nx">Blocos (nx)</Label>
                <Input
                  id="sim-nx"
                  type="number"
                  min="5"
                  max="25"
                  value={nx}
                  onChange={(event) => setNx(Math.min(25, Math.max(5, Number(event.target.value))))}
                  className="font-mono tabular-nums"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="sim-perm">Permeabilidade (mD)</Label>
                <Input
                  id="sim-perm"
                  type="number"
                  min="0.1"
                  value={permeability}
                  onChange={(event) => setPermeability(Number(event.target.value))}
                  className="font-mono tabular-nums"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="sim-phi">Porosidade (fração)</Label>
                <Input
                  id="sim-phi"
                  type="number"
                  min="0.01"
                  max="0.5"
                  step="0.01"
                  value={porosity}
                  onChange={(event) => setPorosity(Number(event.target.value))}
                  className="font-mono tabular-nums"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="sim-rate">Vazão do poço (STB/d)</Label>
                <Input
                  id="sim-rate"
                  type="number"
                  value={wellRate}
                  onChange={(event) => setWellRate(Number(event.target.value))}
                  className="font-mono tabular-nums"
                />
              </div>
            </div>
            <p className="-mt-2 text-[11px] text-muted-foreground">
              Vazão negativa representa produção.
            </p>

            <details className="group rounded-lg border border-border bg-background/50">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2.5 text-xs font-medium text-foreground [&::-webkit-details-marker]:hidden">
                Parâmetros avançados
                <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-180" />
              </summary>
              <div className="grid grid-cols-2 gap-3 border-t border-border p-3">
                <div className="space-y-1.5">
                  <Label htmlFor="sim-dx">Dimensão do bloco (ft)</Label>
                  <Input
                    id="sim-dx"
                    type="number"
                    min="10"
                    value={dx}
                    onChange={(event) => setDx(Number(event.target.value))}
                    className="font-mono tabular-nums"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sim-mu">Viscosidade (cP)</Label>
                  <Input
                    id="sim-mu"
                    type="number"
                    min="0.05"
                    step="0.1"
                    value={viscosity}
                    onChange={(event) => setViscosity(Number(event.target.value))}
                    className="font-mono tabular-nums"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sim-pi">Pressão inicial (psia)</Label>
                  <Input
                    id="sim-pi"
                    type="number"
                    min="100"
                    value={pi}
                    onChange={(event) => setPi(Number(event.target.value))}
                    className="font-mono tabular-nums"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sim-dt">Passo de tempo (dias)</Label>
                  <Input
                    id="sim-dt"
                    type="number"
                    min="0.1"
                    step="1"
                    value={dt}
                    onChange={(event) => setDt(Number(event.target.value))}
                    className="font-mono tabular-nums"
                  />
                </div>
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="sim-steps">Número de passos</Label>
                  <Input
                    id="sim-steps"
                    type="number"
                    min="1"
                    max="100"
                    value={nSteps}
                    onChange={(event) => setNSteps(Number(event.target.value))}
                    className="font-mono tabular-nums"
                  />
                  <p className="text-[10px] text-muted-foreground">
                    Horizonte total: <span className="font-mono tabular-nums">{nSteps * dt} dias</span>
                  </p>
                </div>
              </div>
            </details>

            <Button variant="ghost" size="sm" className="w-full gap-2 text-muted-foreground" onClick={resetModel}>
              <RefreshCw className="h-3.5 w-3.5" />
              Restaurar valores padrão
            </Button>
          </CardContent>
        </Card>

        <section className="min-w-0 space-y-4" aria-label="Resultados da simulação">
          {isRunning ? (
            <Card role="status" className="flex min-h-[22rem] items-center justify-center">
              <div className="space-y-3 text-center">
                <LoaderCircle className="mx-auto h-7 w-7 animate-spin text-primary" />
                <p className="text-sm font-medium">Calculando a resposta do reservatório...</p>
                <p className="text-xs text-muted-foreground">Preparando os perfis de pressão e os resultados.</p>
              </div>
            </Card>
          ) : !hasRun ? (
            <Card className="flex min-h-[22rem] items-center justify-center border-dashed bg-card/60 px-6">
              <div className="max-w-sm space-y-3 text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary">
                  <Activity className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold">Resultados aguardando simulação</h3>
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Revise os parâmetros do modelo e execute a simulação para visualizar a evolução de pressão.
                </p>
                <Button size="sm" onClick={handleRun} className="mt-1 gap-2">
                  <Play className="h-3.5 w-3.5" />
                  Executar simulação
                </Button>
              </div>
            </Card>
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-3">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Gauge className="h-3.5 w-3.5 text-primary" />
                      Pressão no poço
                    </div>
                    <div className="mt-2 font-mono text-xl font-semibold tabular-nums">
                      {finalPressure.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">psia</span>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Activity className="h-3.5 w-3.5 text-primary" />
                      Queda de pressão
                    </div>
                    <div className="mt-2 font-mono text-xl font-semibold tabular-nums">
                      {pressureDrop.toLocaleString()} <span className="text-xs font-normal text-muted-foreground">psia</span>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Layers className="h-3.5 w-3.5 text-primary" />
                      Horizonte
                    </div>
                    <div className="mt-2 font-mono text-xl font-semibold tabular-nums">
                      {nSteps * dt} <span className="text-xs font-normal text-muted-foreground">dias</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between gap-3 px-5 py-4">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                      <Activity className="h-4 w-4 text-primary" />
                      Evolução de pressão
                    </CardTitle>
                    <p className="mt-1 text-xs text-muted-foreground">Pressão no poço e no bloco central ao longo do tempo.</p>
                  </div>
                  <Badge variant="outline" className="shrink-0 font-mono text-[10px] tabular-nums">
                    {nSteps * dt} d
                  </Badge>
                </CardHeader>
                <CardContent className="px-3 pb-4 sm:px-5">
                  <div className="h-[260px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={history} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
                        <XAxis
                          dataKey="time"
                          tick={{ fill: axisColor, fontSize: 11 }}
                          tickLine={{ stroke: gridColor }}
                          axisLine={{ stroke: gridColor }}
                          label={{ value: "Tempo (dias)", position: "insideBottom", offset: -4, fill: axisColor, fontSize: 11 }}
                        />
                        <YAxis
                          domain={["auto", "auto"]}
                          tick={{ fill: axisColor, fontSize: 11 }}
                          tickLine={{ stroke: gridColor }}
                          axisLine={{ stroke: gridColor }}
                          label={{ value: "Pressão (psia)", angle: -90, position: "insideLeft", fill: axisColor, fontSize: 11 }}
                        />
                        <Tooltip
                          contentStyle={tooltipStyle}
                          formatter={(value, name) => [`${value} psia`, name]}
                          labelFormatter={(time) => `Dia ${time}`}
                        />
                        <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: 11 }} />
                        <Line type="monotone" dataKey="wellbore" stroke="hsl(var(--chart-1))" strokeWidth={2.5} name="Poço produtor" dot={false} />
                        <Line type="monotone" dataKey="block5" stroke="hsl(var(--chart-4))" strokeWidth={2} name="Bloco central" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between gap-3 px-5 py-4">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                      <Layers className="h-4 w-4 text-primary" />
                      Perfil espacial de pressão
                    </CardTitle>
                    <p className="mt-1 text-xs text-muted-foreground">Distribuição de pressão na malha ao final do horizonte.</p>
                  </div>
                  <Badge variant="outline" className="shrink-0 font-mono text-[10px] tabular-nums">
                    {nx} blocos
                  </Badge>
                </CardHeader>
                <CardContent className="px-3 pb-4 sm:px-5">
                  <div className="h-[240px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={spatialProfile} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
                        <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
                        <XAxis
                          dataKey="distance"
                          tick={{ fill: axisColor, fontSize: 11 }}
                          tickLine={{ stroke: gridColor }}
                          axisLine={{ stroke: gridColor }}
                          label={{ value: "Distância do poço (ft)", position: "insideBottom", offset: -4, fill: axisColor, fontSize: 11 }}
                        />
                        <YAxis
                          domain={["auto", "auto"]}
                          tick={{ fill: axisColor, fontSize: 11 }}
                          tickLine={{ stroke: gridColor }}
                          axisLine={{ stroke: gridColor }}
                          label={{ value: "Pressão (psia)", angle: -90, position: "insideLeft", fill: axisColor, fontSize: 11 }}
                        />
                        <Tooltip
                          contentStyle={tooltipStyle}
                          formatter={(value) => [`${value} psia`, "Pressão"]}
                          labelFormatter={(distance) => `${distance} ft`}
                        />
                        <Line type="monotone" dataKey="pressure" stroke="hsl(var(--chart-1))" strokeWidth={2.5} name="Pressão da malha" dot={{ r: 3, fill: "hsl(var(--chart-1))" }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function getApiError(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "detail" in error &&
    typeof error.detail === "string"
  ) {
    return error.detail;
  }
  return error instanceof Error ? error.message : "The saved run could not be stored.";
}
