import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
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
import {
  Server,
  Activity,
  Brain,
  CheckCircle,
  Layers,
  TrendingDown,
  Beaker,
  Gauge,
  ArrowRight,
  TrendingUp,
  Droplets,
  Zap,
} from "lucide-react";

interface DashboardOverviewProps {
  onNavigate: (moduleId: string) => void;
}

export default function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  // Field summary monthly production data
  const fieldProduction = [
    { month: "Jan", oil: 18500, gas: 12200, water: 3100 },
    { month: "Fev", oil: 17800, gas: 12050, water: 3400 },
    { month: "Mar", oil: 17200, gas: 11900, water: 3800 },
    { month: "Abr", oil: 16750, gas: 11820, water: 4100 },
    { month: "Mai", oil: 16400, gas: 11700, water: 4450 },
    { month: "Jun", oil: 15950, gas: 11600, water: 4800 },
    { month: "Jul", oil: 15600, gas: 11500, water: 5100 },
    { month: "Ago", oil: 15250, gas: 11420, water: 5400 },
    { month: "Set", oil: 14900, gas: 11300, water: 5750 },
    { month: "Out", oil: 14600, gas: 11200, water: 6100 },
    { month: "Nov", oil: 14350, gas: 11150, water: 6400 },
    { month: "Dez", oil: 14100, gas: 11050, water: 6700 },
  ];

  const modulesStatus = [
    { id: "well-control", name: "Controle de Poço & Kick Sheet", status: "active", desc: "KMW, ICP/FCP, MAASP, Método Wait & Weight e Influx ID" },
    { id: "drilling-hydraulics", name: "Hidráulica de Perfuração & ECD", status: "active", desc: "Jatos na Broca (TFA, HHP, JIF), Bingham Plastic e Teste LOT" },
    { id: "surface-facilities", name: "Instalações & Separadores", status: "active", desc: "Dimensionamento 2/3 Fases (Arnold & Stewart) e Coluna TEG" },
    { id: "reservoir-simulation", name: "Simulação de Reservatórios", status: "active", desc: "Solucionador IMPES 1D & Malha Geocelular 3D" },
    { id: "production-dca", name: "Análise de Declínio (DCA)", status: "active", desc: "Modelos Arps (Exp/Hip/Harm) e Duong" },
    { id: "pvt", name: "Cálculos e Termodinâmica PVT", status: "active", desc: "Equações Standing, Hall-Yarborough e Envelope P-T" },
    { id: "nodal", name: "Análise Nodal", status: "active", desc: "Curvas IPR (Vogel) vs VLP (Beggs-Brill)" },
    { id: "rta", name: "Rate Transient Analysis (RTA)", status: "active", desc: "Flowing Material Balance Gas & Estimativa OGIP" },
    { id: "economics", name: "Avaliação Econômica e Reservas", status: "active", desc: "Fluxo de Caixa Descontado, VPL e TIR" },
    { id: "ai-analytics", name: "Analytics Avançado & IA", status: "active", desc: "Treinamento XGBoost, SVR e Redes LSTM" },
    { id: "well-logs", name: "Perfis de Poço (LAS)", status: "active", desc: "Visualização Geofísica de Curvas GR, RT e Densidade" },
    { id: "connectors", name: "Conectores Comerciais", status: "active", desc: "Interfaces Eclipse, CMG, tNavigator e OSDU" },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-purple-900/10 p-6 rounded-xl border border-blue-500/20">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            PetroLúmen • Plataforma Integrada de Engenharia de Petróleo
          </h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
            Ambiente integrado para controle de poço, hidráulica de perfuração, instalações de superfície, simulação hidrodinâmica, termodinâmica PVT e análise de produção.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 text-xs">
            Todos os 12 Módulos Operacionais
          </Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Status do Sistema</CardTitle>
            <Server className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">100% Operacional</div>
            <p className="text-xs text-muted-foreground mt-1">Todos os subsistemas de cálculo ativos</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Simulações Realizadas</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">24 Simulações</div>
            <p className="text-xs text-muted-foreground mt-1">Históricos casados e convergidos</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Modelos de IA & Machine Learning</CardTitle>
            <Brain className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">8 / 8 Ativos</div>
            <p className="text-xs text-muted-foreground mt-1">XGBoost, SVR e LSTM calibrados</p>
          </CardContent>
        </Card>
      </div>

      {/* Field Production Overview Chart */}
      <Card className="shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary" />
              Histórico Consolidado de Produção do Campo (Últimos 12 Meses)
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Vazões totais de óleo (bbl/d), gás (Mscf/d) e água produzida (bbl/d).
            </p>
          </div>
          <Badge variant="outline" className="text-xs">Produção de Campo</Badge>
        </CardHeader>
        <CardContent>
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fieldProduction} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="month" />
                <YAxis label={{ value: "Vazão Diária", angle: -90, position: "insideLeft", offset: 0 }} />
                <Tooltip />
                <Legend verticalAlign="top" height={36} />
                <Line
                  type="monotone"
                  dataKey="oil"
                  stroke="#16a34a"
                  strokeWidth={2.5}
                  name="Óleo (bbl/d)"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="gas"
                  stroke="#dc2626"
                  strokeWidth={2}
                  name="Gás (Mscf/d)"
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="water"
                  stroke="#2563eb"
                  strokeWidth={2}
                  name="Água (bbl/d)"
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Modules Status Grid */}
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-3">Módulos Especializados PetroLúmen</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {modulesStatus.map((m) => (
            <Card key={m.id} className="shadow-sm hover:shadow-md transition">
              <CardHeader className="pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-semibold">{m.name}</CardTitle>
                <Badge variant="default" className="bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-[10px] font-semibold">
                  Ativo
                </Badge>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <p className="text-xs text-muted-foreground">{m.desc}</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs justify-between group"
                  onClick={() => onNavigate(m.id)}
                >
                  <span>Abrir Módulo</span>
                  <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
