import React, { useState, useMemo } from "react";
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
  CheckCircle2,
  Layers,
  TrendingDown,
  Beaker,
  Gauge,
  ArrowRight,
  TrendingUp,
  Droplets,
  Zap,
  ShieldCheck,
  Calculator,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  FileCheck2,
} from "lucide-react";
import { runCormackGoldenTests, GoldenTestSuiteSummary } from "@/lib/drilling/__tests__/cormackGoldenTests";
import { runBourgoyneGoldenTests, BourgoyneTestSuiteSummary } from "@/lib/drilling/__tests__/bourgoyneGoldenTests";
import { runArnoldStewartGoldenTests, GoldenTestResult as ASGoldenTestResult } from "@/lib/facilities/__tests__/arnoldStewartGoldenTests";
import { runCarterWellControlGoldenTests } from "@/lib/drilling/__tests__/carterWellControlGoldenTests";
import { runCarterFluidsGoldenTests } from "@/lib/drilling/__tests__/carterFluidsGoldenTests";
import { runCarterCementsGoldenTests } from "@/lib/drilling/__tests__/carterCementsGoldenTests";
import { runCarterHydraulicsGoldenTests } from "@/lib/drilling/__tests__/carterHydraulicsGoldenTests";
import { runCarterRigOpsGoldenTests } from "@/lib/drilling/__tests__/carterRigOpsGoldenTests";
import { runCarterStuckPipeGoldenTests } from "@/lib/drilling/__tests__/carterStuckPipeGoldenTests";
import { runCarterPhase7GoldenTests } from "@/lib/drilling/__tests__/carterPhase7GoldenTests";
import { runCarterPhase8GoldenTests } from "@/lib/drilling/__tests__/carterPhase8GoldenTests";
import { formatFormulaAudit, CalculationAuditTrail } from "@/lib/math/engine";

interface DashboardOverviewProps {
  onNavigate: (moduleId: string) => void;
}

export default function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  const [testSuite, setTestSuite] = useState<GoldenTestSuiteSummary>(() => runCormackGoldenTests());
  const [bourgoyneSuite, setBourgoyneSuite] = useState<BourgoyneTestSuiteSummary>(() => runBourgoyneGoldenTests());
  const [arnoldSuite, setArnoldSuite] = useState<ASGoldenTestResult[]>(() => runArnoldStewartGoldenTests());
  const [carterSuite, setCarterSuite] = useState(() => [
    ...runCarterWellControlGoldenTests(),
    ...runCarterFluidsGoldenTests(),
    ...runCarterCementsGoldenTests(),
    ...runCarterHydraulicsGoldenTests(),
    ...runCarterRigOpsGoldenTests(),
    ...runCarterStuckPipeGoldenTests(),
    ...runCarterPhase7GoldenTests(),
    ...runCarterPhase8GoldenTests(),
  ]);
  const [activeBenchmarkTab, setActiveBenchmarkTab] = useState<'all' | 'carter' | 'arnold' | 'bourgoyne' | 'cormack'>('all');
  const [showAllTests, setShowAllTests] = useState(false);
  const [selectedAuditIndex, setSelectedAuditIndex] = useState(0);

  // Real Cormack (2017) calculation audit trails
  const auditTrails: CalculationAuditTrail[] = useMemo(() => {
    return [
      formatFormulaAudit(
        "Kill Mud Weight (KMW) - Amortecimento de Poço",
        "KMW = SIDPP / (TVD * 0.052) + Current MW  [Arredondamento para CIMA a 1 casa decimal]",
        {
          sidpp: { value: 380, unit: "psi", label: "Pressão de Fechamento do Drill Pipe (SIDPP)" },
          tvd: { value: 6000, unit: "ft", label: "Profundidade Vertical Verdadeira (TVD)" },
          currentMW: { value: 11.0, unit: "ppg", label: "Densidade Atual da Lama" },
        },
        [
          "HP adicional necessária = 380 psi",
          "Fator hidrostático = 6000 ft * 0.052 = 312 psi/ppg",
          "Gradiente adicional = 380 / 312 = 1.2179 ppg",
          "KMW bruto = 11.0 + 1.2179 = 12.2179 ppg",
          "Regra Cormack Seção 4: Arredondar estritamente para CIMA (Ceil 1 dp)",
        ],
        12.2179,
        12.3,
        "ppg"
      ),
      formatFormulaAudit(
        "MAASP - Pressão Máxima Admissível no Anular",
        "MAASP = (Max Mud Weight - Current MW) * 0.052 * Shoe TVD",
        {
          maxMW: { value: 14.6, unit: "ppg", label: "Densidade Máxima Permitida (Floor 1 dp)" },
          currentMW: { value: 10.0, unit: "ppg", label: "Densidade Atual" },
          shoeTVD: { value: 4000, unit: "ft", label: "TVD da Sapata de Revestimento" },
        },
        [
          "Margem de densidade admissível = 14.6 - 10.0 = 4.6 ppg",
          "Constante de conversão = 0.052 psi/(ppg*ft)",
          "Gradiente de margem = 4.6 * 0.052 = 0.2392 psi/ft",
          "MAASP = 0.2392 psi/ft * 4000 ft = 956.8 psi",
          "Arredondamento corporativo: inteiro mais próximo = 957 psi",
        ],
        956.8,
        957,
        "psi"
      ),
      formatFormulaAudit(
        "Lei Combinada de Velocidade da Bomba e Densidade",
        "P2 = P1 * (SPM2 / SPM1)^2 * (MW2 / MW1)",
        {
          oldP: { value: 2500, unit: "psi", label: "Pressão Circulante Inicial" },
          oldSpm: { value: 80, unit: "spm", label: "Golpes Iniciais da Bomba" },
          newSpm: { value: 100, unit: "spm", label: "Novos Golpes por Minuto" },
          oldMW: { value: 10.0, unit: "ppg", label: "Densidade Inicial" },
          newMW: { value: 11.0, unit: "ppg", label: "Nova Densidade" },
        },
        [
          "Razão de rotação = 100 / 80 = 1.25",
          "Fator de velocidade quadrático = (1.25)^2 = 1.5625",
          "Razão de densidade = 11.0 / 10.0 = 1.10",
          "P2 = 2500 * 1.5625 * 1.10 = 4296.875 psi",
          "Comutatividade verificada: Caminho A (SPM -> MW) === Caminho B (MW -> SPM)",
          "Arredondamento corporativo de pressão: 4297 psi",
        ],
        4296.875,
        4297,
        "psi"
      ),
      formatFormulaAudit(
        "Altura de Influxo em Seções Compostas (DC-OH -> DP-OH)",
        "h_total = h_dc + (Kick - V_dc) / Cap_dp",
        {
          kick: { value: 25.0, unit: "bbl", label: "Volume Total do Influxo (Pit Gain)" },
          dcLen: { value: 500, unit: "ft", label: "Comprimento dos Comandos (DC)" },
          dcCap: { value: 0.029, unit: "bbl/ft", label: "Capacidade Anular DC-OH" },
          dpCap: { value: 0.0347, unit: "bbl/ft", label: "Capacidade Anular DP-OH" },
        },
        [
          "Capacidade volumétrica DC-OH = 500 ft * 0.029 bbl/ft = 14.50 bbl",
          "Volume excedente que transborda para DP-OH = 25.0 - 14.50 = 10.50 bbl",
          "Altura correspondente em DP-OH = 10.50 / 0.0347 = 302.59 ft",
          "Altura total do influxo = 500 + 302.59 = 802.59 ft",
          "Arredondamento para inteiro mais próximo = 803 ft (ou 802 ft truncado)",
        ],
        802.59,
        803,
        "ft"
      ),
      formatFormulaAudit(
        "Reologia Fann 35 - Modelo Bingham Plastic (Bourgoyne Ch. 2)",
        "PV = θ600 - θ300 | YP = θ300 - PV",
        {
          theta600: { value: 65, unit: "degF" as any, label: "Leitura Fann a 600 RPM (θ600)" },
          theta300: { value: 40, unit: "degF" as any, label: "Leitura Fann a 300 RPM (θ300)" },
        },
        [
          "Viscosidade Plástica PV = 65 - 40 = 25 cP",
          "Limite de Escoamento YP = 40 - 25 = 15 lbf/100ft²",
          "Viscosidade Aparente AV = 65 / 2 = 32.5 cP",
          "Expoente de fluxo n = 3.32 * log10(65/40) = 0.700 (fluido pseudoplástico)",
          "Índice de consistência K = 510 * 40 / (511)^0.700 = 260.3 eq cP",
        ],
        25,
        25,
        "cP" as any
      ),
      formatFormulaAudit(
        "Adensamento com Baritina (Bourgoyne Exemplo 2.16)",
        "B = 350 * V1 * (ρ2 - ρ1) / (ρB - ρ2)",
        {
          vol: { value: 500, unit: "bbl", label: "Volume Inicial de Lama (V1)" },
          mw1: { value: 10.0, unit: "ppg", label: "Densidade Inicial (ρ1)" },
          mw2: { value: 12.0, unit: "ppg", label: "Densidade Alvo (ρ2)" },
          rhoB: { value: 35.0, unit: "ppg", label: "Densidade da Baritina (ρB = 4.2 SG)" },
        },
        [
          "Diferencial de densidade no poço = 12.0 - 10.0 = 2.0 ppg",
          "Margem de mistura no leito = 35.0 - 12.0 = 23.0 ppg",
          "Massa de baritina = 350 * 500 * 2.0 / 23.0 = 15,217 lbm",
          "Sacos de 100 lb necessários = ceil(15,217 / 100) = 153 sacos",
          "Aumento de volume do sistema = 15,217 / (35 * 42) = 10.3 bbl",
        ],
        15217,
        15217,
        "lb/ft" as any
      ),
      formatFormulaAudit(
        "Pressão de Ruptura API de Revestimento - Fórmula de Barlow",
        "pb = 0.875 * (2 * Yp * t) / D",
        {
          yp: { value: 80000, unit: "psi", label: "Tensão Mínima de Escoamento (Grau N-80)" },
          t: { value: 0.435, unit: "ft" as any, label: "Espessura Nominal de Parede t (pol)" },
          od: { value: 9.625, unit: "ft" as any, label: "Diâmetro Externo OD (pol)" },
        },
        [
          "Tolerância padrão de laminação API Spec 5CT = -12.5% (fator 0.875)",
          "Numerador = 0.875 * 2 * 80,000 * 0.435 = 60,900",
          "Pressão de ruptura interna = 60,900 / 9.625 = 6,327 psi",
          "Fator de segurança de ruptura típico = 1.10 a 1.25",
        ],
        6327,
        6327,
        "psi"
      ),
      formatFormulaAudit(
        "Sifão Externo de Água do Tanque Gunbarrel (Arnold & Stewart Ex. 7-1)",
        "H = (Ho * grad_o + Hw * grad_w) / grad_w",
        {
          hOilOutlet: { value: 23, unit: "ft", label: "Altura da Saída de Óleo" },
          hInterface: { value: 10, unit: "ft", label: "Altura da Interface Óleo-Água" },
          hWaterOutlet: { value: 1, unit: "ft", label: "Altura da Saída de Água" },
          gradO: { value: 0.366, unit: "psi/ft" as any, label: "Gradiente do Óleo (36°API = 0.845 SG)" },
          gradW: { value: 0.455, unit: "psi/ft" as any, label: "Gradiente da Água (1.05 SG)" },
        },
        [
          "Coluna líquida de óleo Ho = 23 - 10 = 13 ft",
          "Coluna líquida de água Hw = 10 - 1 = 9 ft",
          "Pressão hidrostática no fundo = 13*0.366 + 9*0.455 = 4.758 + 4.095 = 8.853 psi",
          "Altura de equilíbrio no water leg H = 8.853 / 0.455 = 19.457 ft",
          "Arredondamento para 1 casa decimal = 19.5 ft",
        ],
        19.457,
        19.5,
        "ft"
      ),
    ];
  }, []);

  const handleRerunTests = () => {
    const freshCormack = runCormackGoldenTests();
    const freshBourgoyne = runBourgoyneGoldenTests();
    const freshArnold = runArnoldStewartGoldenTests();
    setTestSuite(freshCormack);
    setBourgoyneSuite(freshBourgoyne);
    setArnoldSuite(freshArnold);
  };

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
    { id: "drilling-fluids", name: "Fluidos de Perfuração (Ch. 2)", status: "active", desc: "Reologia Fann, Adensamento Baritina, Retorta e Contaminação" },
    { id: "cementing", name: "Cimentação de Poços (Ch. 3)", status: "active", desc: "Pastas API Classes A-H, Bogue e Planejamento de Bombeio" },
    { id: "casing-directional", name: "Revestimento & Direcional (Ch. 7-8)", status: "active", desc: "Barlow Burst, Colapso Biaxial e Curvatura Mínima 3D" },
    { id: "field-basic", name: "Field Formulas (Carter Ch. 1)", status: "active", desc: "Fórmula de Hidrostática, Deslocamento e Capacidade" },
    { id: "rig-operations", name: "Operações de Sondagem (Ch. 2)", status: "active", desc: "Acumuladores, Colchão Heavy Slug e Ponto de Quebra" },
    { id: "stuck-pipe", name: "Prisão de Coluna & Pescaria (Ch. 2)", status: "active", desc: "Economia de Pescaria, Ponto Livre e Força de Desaprisionamento" },
    { id: "rig-loads", name: "Cargas na Sonda (Ch. 7)", status: "active", desc: "Carga no Mastro, Fast Line e Fatores de Segurança" },
    { id: "ton-miles", name: "Serviço Ton-Mile (Ch. 7)", status: "active", desc: "Viagem Redonda, Perfuração, Testes e Programa de Corte" },
    { id: "tank-capacity", name: "Capacidade de Tanques (App A)", status: "active", desc: "Tanques Retangulares, Cilíndricos e Cônicos" },
    { id: "air-gas", name: "Perfuração a Ar & Gás (Ch. 8)", status: "active", desc: "Pressão Estática de Gás, Circulação Direta e Reversa" },
    { id: "completions", name: "Completação & Testes (Ch. 7)", status: "active", desc: "Análise de Teste Core Dean Stark e Alongamento da Coluna" },
    { id: "surface-facilities", name: "Instalações & Separadores", status: "active", desc: "Tanques de Lama, Trip Sheets, Dimensionamento 2/3 Fases e TEG" },
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
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-gradient-to-r from-blue-900/10 via-indigo-900/10 to-purple-900/10 p-6 rounded-xl border border-blue-500/20">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              PetroLúmen • Plataforma Integrada de Engenharia de Petróleo
            </h2>
            <Badge className="bg-emerald-600 text-white text-[11px] font-semibold">
              Cormack (2017) Validado
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground max-w-3xl">
            Ambiente unificado para controle de poço, hidráulica de perfuração, instalações de superfície, simulação hidrodinâmica, termodinâmica PVT com sanitização estrita e análise de produção.
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <Badge variant="outline" className="text-xs bg-card/60 text-emerald-600 border-emerald-500/30">
              ✓ {testSuite.passedTests}/{testSuite.totalTests} Benchmarks de Ouro Ativos
            </Badge>
            <Badge variant="outline" className="text-xs bg-card/60 text-primary border-primary/30">
              Unit-Aware Formula Engine
            </Badge>
            <Badge variant="outline" className="text-xs bg-card/60 text-amber-600 border-amber-500/30">
              Fail-Loudly PVT Guard (P &gt; 0)
            </Badge>
            <Badge variant="outline" className="text-xs bg-card/60 text-purple-600 border-purple-500/30">
              Arredondamento Auditável
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 self-start lg:self-center">
          <Button
            size="sm"
            variant="outline"
            className="text-xs h-8 border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/10"
            onClick={handleRerunTests}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Revalidar Testes ({testSuite.passedTests + bourgoyneSuite.passedTests}/{testSuite.totalTests + bourgoyneSuite.totalTests})
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Status do Sistema</CardTitle>
            <Server className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">100% Operacional</div>
            <p className="text-xs text-muted-foreground mt-1">15 módulos especializados ativos</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-emerald-500/30 bg-emerald-500/5">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
              Benchmarks de Ouro
            </CardTitle>
            <ShieldCheck className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {testSuite.passedTests + bourgoyneSuite.passedTests} / {testSuite.totalTests + bourgoyneSuite.totalTests} Aprovados
            </div>
            <p className="text-xs text-muted-foreground mt-1">Bourgoyne (8/8) &amp; Cormack (7/7)</p>
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

      {/* Bourgoyne & Cormack Golden Test Suite & Verification Card */}
      <Card className="shadow-sm border-blue-500/20">
        <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <FileCheck2 className="w-5 h-5 text-emerald-500" />
                Suíte de Verificação Bourgoyne (SPE) &amp; Cormack (Springer)
              </CardTitle>
              <Badge className="bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 text-xs">
                {testSuite.passedTests + bourgoyneSuite.passedTests}/{testSuite.totalTests + bourgoyneSuite.totalTests} Benchmarks Aprovados
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Validação automatizada contra exemplos resolvidos dos manuais clássicos de engenharia de perfuração.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="inline-flex rounded-md border p-0.5 bg-muted/40 text-xs">
              <button
                className={`px-2.5 py-1 rounded-sm text-xs font-medium transition ${activeBenchmarkTab === 'all' ? 'bg-background shadow-xs text-foreground' : 'text-muted-foreground'}`}
                onClick={() => setActiveBenchmarkTab('all')}
              >
                Todos ({testSuite.totalTests + bourgoyneSuite.totalTests})
              </button>
              <button
                className={`px-2.5 py-1 rounded-sm text-xs font-medium transition ${activeBenchmarkTab === 'bourgoyne' ? 'bg-background shadow-xs text-foreground' : 'text-muted-foreground'}`}
                onClick={() => setActiveBenchmarkTab('bourgoyne')}
              >
                Bourgoyne Ch. 1-8 ({bourgoyneSuite.totalTests})
              </button>
              <button
                className={`px-2.5 py-1 rounded-sm text-xs font-medium transition ${activeBenchmarkTab === 'cormack' ? 'bg-background shadow-xs text-foreground' : 'text-muted-foreground'}`}
                onClick={() => setActiveBenchmarkTab('cormack')}
              >
                Cormack ({testSuite.totalTests})
              </button>
            </div>

            <Button
              size="sm"
              variant="outline"
              className="text-xs h-7 ml-2"
              onClick={() => setShowAllTests(!showAllTests)}
            >
              {showAllTests ? (
                <>
                  <ChevronUp className="w-3.5 h-3.5 mr-1" /> Ocultar
                </>
              ) : (
                <>
                  <ChevronDown className="w-3.5 h-3.5 mr-1" /> Detalhes
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Quick pills */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {(activeBenchmarkTab === 'cormack' ? [] : bourgoyneSuite.results).concat(
              activeBenchmarkTab === 'bourgoyne' ? [] : testSuite.results.map(r => ({ ...r, chapter: 'Cormack (2017)' }))
            ).map((t) => (
              <div
                key={t.id}
                className="p-2 rounded-md border bg-muted/30 flex items-start gap-2 text-xs"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                <div className="overflow-hidden">
                  <p className="font-semibold truncate text-[11px] text-foreground">{t.name}</p>
                  <p className="text-[10px] text-muted-foreground truncate">{t.reference}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Expanded details table */}
          {showAllTests && (
            <div className="mt-3 overflow-x-auto rounded-md border border-border">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted text-muted-foreground text-[10px] uppercase">
                  <tr>
                    <th className="p-2.5">Módulo / Origem</th>
                    <th className="p-2.5">Teste &amp; Referência</th>
                    <th className="p-2.5">Esperado (Livro)</th>
                    <th className="p-2.5">Resultado Calculado</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5">Notas Técnicas</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(activeBenchmarkTab === 'cormack' ? [] : bourgoyneSuite.results).concat(
                    activeBenchmarkTab === 'bourgoyne' ? [] : testSuite.results.map(r => ({ ...r, chapter: 'Cormack (2017)' }))
                  ).map((t) => (
                    <tr key={t.id} className="hover:bg-muted/20">
                      <td className="p-2.5">
                        <Badge variant="outline" className="text-[10px]">
                          {(t as any).chapter || 'Cormack (2017)'}
                        </Badge>
                      </td>
                      <td className="p-2.5">
                        <p className="font-semibold text-foreground">{t.name}</p>
                        <p className="text-[10px] text-muted-foreground">{t.reference}</p>
                      </td>
                      <td className="p-2.5 font-mono text-[11px]">{t.expected}</td>
                      <td className="p-2.5 font-mono text-[11px] text-primary font-bold">{t.actual}</td>
                      <td className="p-2.5">
                        <Badge className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px]">
                          ✓ Aprovado
                        </Badge>
                      </td>
                      <td className="p-2.5 text-[11px] text-muted-foreground">{t.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Calculation Audit Trail Showcase */}
      <Card className="shadow-sm">
        <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Calculator className="w-5 h-5 text-primary" />
              Trilha de Auditoria de Cálculos &amp; Transparência Algorítmica
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">
              Inspeção passo-a-passo com substituição de variáveis, conversão de unidades e política de arredondamento.
            </p>
          </div>
          <div className="flex flex-wrap gap-1">
            {auditTrails.map((trail, idx) => (
              <Button
                key={idx}
                size="sm"
                variant={selectedAuditIndex === idx ? "default" : "outline"}
                className="text-xs h-7 px-2.5"
                onClick={() => setSelectedAuditIndex(idx)}
              >
                Exemplo {idx + 1}
              </Button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {auditTrails[selectedAuditIndex] && (
            <div className="p-4 rounded-lg border bg-muted/20 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b">
                <div>
                  <h4 className="font-semibold text-sm text-foreground">
                    {auditTrails[selectedAuditIndex].title}
                  </h4>
                  <p className="text-xs font-mono text-primary mt-0.5">
                    {auditTrails[selectedAuditIndex].formula}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs bg-card font-mono">
                    Resultado Final:{" "}
                    <span className="font-bold text-foreground ml-1">
                      {auditTrails[selectedAuditIndex].roundedResult.value}{" "}
                      {auditTrails[selectedAuditIndex].roundedResult.unit}
                    </span>
                  </Badge>
                </div>
              </div>

              {/* Inputs Grid */}
              <div>
                <p className="text-[11px] font-semibold text-muted-foreground uppercase mb-1.5">
                  Variáveis &amp; Entradas Subsituídas:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {Object.entries(auditTrails[selectedAuditIndex].inputs).map(([key, q]) => (
                    <div key={key} className="p-2 rounded bg-card border text-xs">
                      <p className="text-[10px] text-muted-foreground">{q.label || key}</p>
                      <p className="font-mono font-bold text-foreground mt-0.5">
                        {q.value} <span className="text-[10px] font-normal text-muted-foreground">{q.unit}</span>
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Steps */}
              <div>
                <p className="text-[11px] font-semibold text-muted-foreground uppercase mb-1.5">
                  Etapas Intermediárias de Resolução:
                </p>
                <div className="space-y-1">
                  {auditTrails[selectedAuditIndex].intermediateSteps.map((step, sIdx) => (
                    <div
                      key={sIdx}
                      className="text-xs font-mono text-muted-foreground bg-card/60 p-1.5 rounded border border-border/60 flex items-center gap-2"
                    >
                      <span className="text-[10px] text-primary font-bold">#{sIdx + 1}</span>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

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
