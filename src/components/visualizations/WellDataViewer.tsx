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
import { Select } from "@/components/ui/select";
import { Database, Upload, FileText, CheckCircle, BarChart3 } from "lucide-react";

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
  const [logFilter, setLogFilter] = useState<"all" | "gr" | "res" | "por">("all");
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const selectedWell = mockWells.find((w) => w.id === selectedWellId) || mockWells[0];

  // Generate synthetic well log track (Depth: 2800m to 3000m)
  const logData = useMemo(() => {
    const points: WellLogPoint[] = [];
    for (let d = 2800; d <= 2950; d += 2) {
      // Sandstone pay zone between 2860m and 2910m: low GR, high resistivity, low density
      const isPayZone = d >= 2860 && d <= 2910;
      const gr = isPayZone ? 25 + Math.random() * 20 : 90 + Math.random() * 35;
      const res = isPayZone ? 60 + Math.random() * 120 : 1.5 + Math.random() * 3;
      const rhob = isPayZone ? 2.18 + Math.random() * 0.08 : 2.55 + Math.random() * 0.12;
      const nphi = isPayZone ? 0.24 + Math.random() * 0.04 : 0.12 + Math.random() * 0.05;

      points.push({
        depth: d,
        gr: Number(gr.toFixed(1)),
        res: Number(res.toFixed(1)),
        rhob: Number(rhob.toFixed(2)),
        nphi: Number(nphi.toFixed(3)),
      });
    }
    return points;
  }, [selectedWellId]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadSuccess(`Arquivo "${file.name}" carregado com sucesso (${(file.size / 1024).toFixed(1)} KB). 450 amostras processadas.`);
      setTimeout(() => setUploadSuccess(null), 5000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Database className="w-6 h-6 text-primary" />
            Visualizador de Perfis de Poços (LAS Log Viewer)
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Inspeção geofísica de curvas de perfilagem de poço (Raio Gama, Resistividade Profunda, Densidade e Porosidade Neutrão).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="cursor-pointer">
            <input type="file" accept=".las,.csv,.txt" onChange={handleFileUpload} className="hidden" />
            <div className="inline-flex items-center justify-center rounded-md text-xs font-medium border border-input bg-background shadow-sm hover:bg-accent px-3 py-1.5 gap-2">
              <Upload className="w-4 h-4 text-primary" />
              Upload Arquivo LAS / CSV
            </div>
          </label>
        </div>
      </div>

      {uploadSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
          <span>{uploadSuccess}</span>
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
              onChange={(e) => setSelectedWellId(e.target.value)}
            >
              {mockWells.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <Badge variant="outline">Bacia: {selectedWell.basin}</Badge>
            <Badge variant="outline">Tipo: {selectedWell.type}</Badge>
            <Badge variant="outline" className="text-emerald-600 border-emerald-500/40">Status: Produzindo</Badge>
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
                  <YAxis type="number" dataKey="depth" reversed domain={[2800, 2950]} label={{ value: "Profundidade MD (m)", angle: -90, position: "insideLeft", offset: -5 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="gr" stroke="#d97706" strokeWidth={2} dot={false} />
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
                  <YAxis type="number" dataKey="depth" reversed domain={[2800, 2950]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="res" stroke="#e11d48" strokeWidth={2} dot={false} />
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
            <Badge variant="outline" className="text-[10px]">Crossover de Gás</Badge>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={logData} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis type="number" domain={[1.9, 2.7]} label={{ value: "RHOB (g/cm³)", position: "insideBottom", offset: -5 }} />
                  <YAxis type="number" dataKey="depth" reversed domain={[2800, 2950]} />
                  <Tooltip />
                  <Legend verticalAlign="top" height={30} />
                  <Line type="monotone" dataKey="rhob" name="RHOB (g/cm³)" stroke="#2563eb" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="text-[10px] text-muted-foreground text-center mt-2">
              Zona de Pay identificada entre 2860m e 2910m (net pay = 50m)
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
