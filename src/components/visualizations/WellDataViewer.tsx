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
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Database, Upload, CheckCircle, AlertTriangle } from "lucide-react";
import { ProvenanceBadge } from "@/components/ui/ProvenanceBadge";
import { parseLASContent, getCalibratedSampleLog, ParsedWellLogData } from "@/lib/lasParser";
import {
  classifyFacies,
  FaciesClassificationResult,
  LasParseResult,
  OoipCalculationResult,
  parseLasFile,
  runOoipCalculation,
  uploadOoipLas,
} from "@/lib/api";

interface WellLogPoint {
  depth: number;
  gr: number; // Gamma ray (API)
  res: number; // Resistivity (ohm.m)
  rhob: number; // Bulk density (g/cm3)
  nphi: number; // Neutron porosity (v/v)
}

const mockWells = [
  { id: "VOLVE-15-9-F12", name: "Campo de Volve - Poço 15/9-F-12", basin: "Mar do Norte", type: "Produtor Horizontal" },
  { id: "SANTOS-7-SP-04", name: "Bacia de Santos - Pré-Sal 7-SP-04", basin: "Santos (Carbonatos)", type: "Produtor EOR WAG" },
  { id: "PERMIAN-HZ-108", name: "Permian Wolfcamp HZ-108", basin: "Delaware Basin", type: "Shale Fraturado" },
  { id: "CAMPOS-PR-02", name: "Bacia de Campos - Arenito Carapebus", basin: "Campos (Turbiditos)", type: "Produtor Subsea" },
];

export default function WellDataViewer() {
  const [selectedWellId, setSelectedWellId] = useState<string>("VOLVE-15-9-F12");
  const [uploadedLog, setUploadedLog] = useState<ParsedWellLogData | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [ooipAreaAcres, setOoipAreaAcres] = useState(100);
  const [netToGrossCutoff, setNetToGrossCutoff] = useState(0.5);
  const [ooipSessionId, setOoipSessionId] = useState<string | null>(null);
  const [ooipResult, setOoipResult] = useState<OoipCalculationResult | null>(null);
  const [ooipError, setOoipError] = useState<string | null>(null);
  const [isCalculatingOoip, setIsCalculatingOoip] = useState(false);
  const [serverLasInfo, setServerLasInfo] = useState<LasParseResult | null>(null);
  const [serverLasError, setServerLasError] = useState<string | null>(null);
  const [isParsingOnServer, setIsParsingOnServer] = useState(false);
  const [faciesResult, setFaciesResult] = useState<FaciesClassificationResult | null>(null);
  const [faciesError, setFaciesError] = useState<string | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);

  const selectedWell = mockWells.find((w) => w.id === selectedWellId) || mockWells[0];

  const logData: WellLogPoint[] = useMemo(() => {
    if (uploadedLog) {
      return uploadedLog.points;
    }
    return getCalibratedSampleLog();
  }, [uploadedLog]);

  const depthMin = useMemo(() => {
    if (logData.length === 0) return 2800;
    return Math.floor(logData[0].depth);
  }, [logData]);

  const depthMax = useMemo(() => {
    if (logData.length === 0) return 2950;
    return Math.ceil(logData[logData.length - 1].depth);
  }, [logData]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadedLog(null);
    setUploadedFile(null);
    setUploadStatus(null);
    setOoipSessionId(null);
    setOoipResult(null);
    setOoipError(null);
    setServerLasInfo(null);
    setServerLasError(null);
    setFaciesResult(null);
    setFaciesError(null);

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        if (!text || text.trim().length === 0) {
          throw new Error("Arquivo vazio ou ilegível.");
        }
        const parsed = parseLASContent(text, file.name);
        setUploadedLog(parsed);
        setUploadedFile(file);
        setUploadStatus({
          success: true,
          message: `Arquivo "${file.name}" processado com sucesso. ${parsed.sampleCount} amostras reais carregadas (Profundidade: ${parsed.startDepth}m a ${parsed.stopDepth}m).`,
        });
      } catch (err: unknown) {
        setUploadedLog(null);
        const msg = err instanceof Error ? err.message : "Erro desconhecido ao processar arquivo LAS.";
        setUploadStatus({
          success: false,
          message: `Falha na leitura do arquivo: ${msg}`,
        });
      }
    };

    reader.onerror = () => {
      setUploadedLog(null);
      setUploadStatus({
        success: false,
        message: "Erro de E/S ao ler o arquivo selecionado.",
      });
    };

    reader.readAsText(file);
  };

  const handleOoipCalculation = async () => {
    if (!uploadedFile || !uploadedFile.name.toLowerCase().endsWith(".las")) {
      setOoipError("Upload a LAS file to run the OOIP workflow.");
      return;
    }
    if (!Number.isFinite(ooipAreaAcres) || ooipAreaAcres <= 0) {
      setOoipError("Area must be a positive number of acres.");
      return;
    }
    if (!Number.isFinite(netToGrossCutoff) || netToGrossCutoff < 0 || netToGrossCutoff > 1) {
      setOoipError("Net-to-gross porosity cutoff must be between 0 and 1.");
      return;
    }

    setIsCalculatingOoip(true);
    setOoipError(null);
    setOoipResult(null);
    try {
      const session = ooipSessionId
        ? { session_id: ooipSessionId }
        : await uploadOoipLas(uploadedFile);
      setOoipSessionId(session.session_id);
      const result = await runOoipCalculation({
        session_id: session.session_id,
        area_acres: ooipAreaAcres,
        net_to_gross_cutoff: netToGrossCutoff,
        water_saturation_method: "archie",
        archie_params: { a: 1, m: 2, n: 2, Rw: 0.1 },
      });
      setOoipResult(result);
    } catch (error: unknown) {
      setOoipSessionId(null);
      setOoipError(
        typeof error === "object" && error !== null && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : error instanceof Error ? error.message : "OOIP calculation failed.",
      );
    } finally {
      setIsCalculatingOoip(false);
    }
  };

  const handleServerLasParse = async () => {
    if (!uploadedFile || !uploadedFile.name.toLowerCase().endsWith(".las")) {
      setServerLasError("Select a LAS file to validate with the server parser.");
      return;
    }
    setIsParsingOnServer(true);
    setServerLasError(null);
    setServerLasInfo(null);
    try {
      setServerLasInfo(await parseLasFile(uploadedFile));
    } catch (error: unknown) {
      setServerLasError(
        typeof error === "object" && error !== null && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : error instanceof Error ? error.message : "Server LAS parsing failed.",
      );
    } finally {
      setIsParsingOnServer(false);
    }
  };

  const handleFaciesClassification = async () => {
    setIsClassifying(true);
    setFaciesError(null);
    setFaciesResult(null);
    try {
      const result = await classifyFacies(logData.map((point) => ({
        gamma: point.gr,
        resistivity: point.res,
        density: point.rhob,
        porosity: point.nphi,
        depth: point.depth,
      })));
      setFaciesResult(result);
    } catch (error: unknown) {
      setFaciesError(
        typeof error === "object" && error !== null && "detail" in error && typeof error.detail === "string"
          ? error.detail
          : error instanceof Error ? error.message : "Facies classification failed.",
      );
    } finally {
      setIsClassifying(false);
    }
  };

  const resetUploadedLog = () => {
    setUploadedLog(null);
    setUploadedFile(null);
    setUploadStatus(null);
    setOoipSessionId(null);
    setOoipResult(null);
    setOoipError(null);
    setServerLasInfo(null);
    setServerLasError(null);
    setFaciesResult(null);
    setFaciesError(null);
  };

  const faciesCounts = faciesResult?.facies_predictions.reduce<Record<string, number>>(
    (counts, facies) => {
      const key = String(facies);
      counts[key] = (counts[key] ?? 0) + 1;
      return counts;
    },
    {},
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Database className="w-6 h-6 text-primary" />
              Visualizador de Perfis de Poços (LAS Log Viewer)
            </h2>
            {uploadedLog ? (
              <ProvenanceBadge kind="calculated" source={`Arquivo LAS: ${uploadedLog.fileName}`} />
            ) : (
              <ProvenanceBadge kind="sample" source="Amostra Padrão Calibrada (Não São Dados Reais)" />
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Inspeção geofísica de curvas de perfilagem de poço (Raio Gama, Resistividade Profunda, Densidade e Porosidade Neutrão).
          </p>
        </div>
        <div className="flex items-center gap-2">
          {uploadedLog && (
            <Button
              size="sm"
              variant="outline"
              className="text-xs"
              onClick={() => {
                resetUploadedLog();
              }}
            >
              Restaurar Amostra
            </Button>
          )}
          <label className="cursor-pointer">
            <input type="file" accept=".las,.csv,.txt" onChange={handleFileUpload} className="hidden" />
            <div className="inline-flex items-center justify-center rounded-md text-xs font-medium border border-input bg-background shadow-sm hover:bg-accent px-3 py-1.5 gap-2">
              <Upload className="w-4 h-4 text-primary" />
              Carregar LAS / CSV Real
            </div>
          </label>
        </div>
      </div>

      {uploadStatus && (
        <div
          className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
            uploadStatus.success
              ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300"
              : "bg-destructive/10 border border-destructive/30 text-destructive"
          }`}
        >
          {uploadStatus.success ? (
            <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-destructive flex-shrink-0" />
          )}
          <span>{uploadStatus.message}</span>
        </div>
      )}

      {/* Well Selector and Header info */}
      <Card className="p-4 bg-card border">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">Poço Selecionado:</span>
            <Select
              className="w-72"
              value={selectedWellId}
              onChange={(e) => {
                setSelectedWellId(e.target.value);
                resetUploadedLog();
              }}
            >
              {mockWells.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge variant="outline">Bacia: {selectedWell.basin}</Badge>
            <Badge variant="outline">Tipo: {selectedWell.type}</Badge>
            <Badge variant="outline" className="text-emerald-600 border-emerald-500/40">
              {logData.length} Pontos ({depthMin}m - {depthMax}m)
            </Badge>
          </div>
        </div>
      </Card>

      {/* Well Log Multi-Track Plots */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Track 1: Gamma Ray (Lithology) */}
        <Card className="shadow-sm">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold text-amber-600 dark:text-amber-400">
              Track 1: Raio Gama (GR)
            </CardTitle>
            <Badge variant="outline" className="text-[10px]">0 - 150 API</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={logData} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" domain={[0, 150]} label={{ value: "GR (API)", position: "insideBottom", offset: -5 }} />
                  <YAxis type="number" dataKey="depth" reversed domain={[depthMin, depthMax]} label={{ value: "Profundidade MD (m)", angle: -90, position: "insideLeft", offset: -5 }} />
                  <Tooltip
                    formatter={(value, name) => [`${Number(value).toFixed(2)} API`, String(name)]}
                    labelFormatter={(depth) => `Measured depth: ${depth} m`}
                  />
                  <Line type="monotone" dataKey="gr" name="Gamma ray" stroke="hsl(var(--chart-4))" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[10px] text-muted-foreground text-center mt-2">
              Arenito limpo &lt; 45 API | Folhelho &gt; 80 API
            </p>
          </CardContent>
        </Card>

        {/* Track 2: Deep Resistivity (Hydrocarbon Indicator) */}
        <Card className="shadow-sm">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold text-rose-600 dark:text-rose-400">
              Track 2: Resistividade Profunda (RT)
            </CardTitle>
            <Badge variant="outline" className="text-[10px]">0.2 - 200 ohm.m</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={logData} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" domain={[0.1, 200]} label={{ value: "Resistividade (ohm.m)", position: "insideBottom", offset: -5 }} />
                  <YAxis type="number" dataKey="depth" reversed domain={[depthMin, depthMax]} label={{ value: "Measured depth (m)", angle: -90, position: "insideLeft", offset: -5 }} />
                  <Tooltip
                    formatter={(value, name) => [`${Number(value).toFixed(2)} ohm·m`, String(name)]}
                    labelFormatter={(depth) => `Measured depth: ${depth} m`}
                  />
                  <Line type="monotone" dataKey="res" name="Resistivity" stroke="hsl(var(--chart-5))" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[10px] text-muted-foreground text-center mt-2">
              Alta resistividade (&gt; 50) indica hidrocarbonetos saturados
            </p>
          </CardContent>
        </Card>

        {/* Track 3: Density (RHOB) & Neutron Porosity (NPHI) */}
        <Card className="shadow-sm">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-semibold text-blue-600 dark:text-blue-400">
              Track 3: RHOB (Densidade) & NPHI
            </CardTitle>
            <Badge variant="outline" className="text-[10px]">Crossover de Óleo/Gás</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={logData} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" domain={[1.9, 2.7]} label={{ value: "RHOB (g/cm³)", position: "insideBottom", offset: -5 }} />
                  <YAxis type="number" dataKey="depth" reversed domain={[depthMin, depthMax]} label={{ value: "Measured depth (m)", angle: -90, position: "insideLeft", offset: -5 }} />
                  <Tooltip
                    formatter={(value, name) => [`${Number(value).toFixed(3)} g/cm³`, String(name)]}
                    labelFormatter={(depth) => `Measured depth: ${depth} m`}
                  />
                  <Legend verticalAlign="top" height={30} />
                  <Line type="monotone" dataKey="rhob" name="RHOB (g/cm³)" stroke="hsl(var(--chart-2))" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[10px] text-muted-foreground text-center mt-2">
              Zona de Pay identificada entre 2860m e 2910m (net pay = 50m)
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">LAS-based volumetric OOIP</CardTitle>
            <p className="text-sm text-muted-foreground">
              Uses the backend Archie workflow. It requires a LAS file with a porosity curve;
              resistivity defaults to 20 ohm-m when absent.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="ooip-area">Area (acres)</Label>
                <Input
                  id="ooip-area"
                  type="number"
                  min="0"
                  step="any"
                  value={ooipAreaAcres}
                  onChange={(event) => setOoipAreaAcres(Number(event.target.value))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ooip-ntg-cutoff">Porosity cutoff</Label>
                <Input
                  id="ooip-ntg-cutoff"
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={netToGrossCutoff}
                  onChange={(event) => setNetToGrossCutoff(Number(event.target.value))}
                />
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={handleServerLasParse}
              disabled={isParsingOnServer || !uploadedFile?.name.toLowerCase().endsWith(".las")}
            >
              {isParsingOnServer ? "Validating..." : "Validate LAS with server"}
            </Button>
            {serverLasError && <p role="alert" className="text-sm text-destructive">{serverLasError}</p>}
            {serverLasInfo && (
              <p role="status" className="text-sm text-muted-foreground">
                Server parsed {serverLasInfo.row_count} rows across {serverLasInfo.curves.length} curves
                ({serverLasInfo.depth_range[0]}–{serverLasInfo.depth_range[1]}).
              </p>
            )}
            <Button
              type="button"
              onClick={handleOoipCalculation}
              disabled={isCalculatingOoip || !uploadedFile?.name.toLowerCase().endsWith(".las")}
            >
              {isCalculatingOoip ? "Calculating..." : "Calculate OOIP"}
            </Button>
            {!uploadedFile?.name.toLowerCase().endsWith(".las") && (
              <p className="text-sm text-muted-foreground">Select a .las file above to enable this workflow.</p>
            )}
            {ooipError && <p role="alert" className="text-sm text-destructive">{ooipError}</p>}
            {ooipResult && (
              <div role="status" className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">OOIP</p>
                  <p className="font-mono text-lg font-semibold">{ooipResult.ooip_bbl.toLocaleString()} STB</p>
                </div>
                <div className="rounded-md border bg-muted/30 p-3">
                  <p className="text-xs text-muted-foreground">Net pay / gross pay</p>
                  <p className="font-mono text-lg font-semibold">
                    {ooipResult.net_pay_ft.toFixed(2)} / {ooipResult.gross_pay_ft.toFixed(2)} ft
                  </p>
                </div>
                <p className="text-xs text-muted-foreground sm:col-span-2">{ooipResult.note}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Backend facies classification</CardTitle>
            <p className="text-sm text-muted-foreground">
              Classifies each displayed depth sample using gamma ray, resistivity, density, and porosity.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button type="button" onClick={handleFaciesClassification} disabled={isClassifying || logData.length === 0}>
              {isClassifying ? "Classifying..." : `Classify ${logData.length} samples`}
            </Button>
            {faciesError && <p role="alert" className="text-sm text-destructive">{faciesError}</p>}
            {faciesResult && faciesCounts && (
              <div role="status" className="space-y-2">
                <p className="text-sm">
                  {faciesResult.training_samples_count} training samples; features: {faciesResult.features_used.join(", ")}.
                </p>
                <ul className="space-y-1 text-sm">
                  {Object.entries(faciesCounts).map(([facies, count]) => (
                    <li key={facies} className="flex justify-between rounded-md border bg-muted/30 px-3 py-2">
                      <span>Facies {facies}</span>
                      <span>{count} samples</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
