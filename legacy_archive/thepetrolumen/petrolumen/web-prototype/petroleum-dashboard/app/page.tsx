"use client"

import { useState } from "react"
import {
  Brain,
  BarChart3,
  TrendingUp,
  Layers,
  Target,
  Gauge,
  Database,
  Activity,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Download,
  Bell,
  User,
  Search,
  AlertTriangle,
  CheckCircle,
  TrendingDown,
  PieChart,
  LineChart,
  BarChart,
  Cpu,
  Wifi,
  WifiOff,
  Droplets,
  Flame,
  Beaker,
  Zap,
  Map,
  FileText,
  Upload,
  Eye,
  Calculator,
  DollarSign,
  GitBranch,
  Box,
  Workflow,
  Microscope,
  Mountain,
  Waves,
  Filter,
  Network,
  Shuffle,
  Play,
  Pause,
  RotateCcw,
} from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import ReservoirVisualization3D from "./components/visualizations/ReservoirVisualization3D"
import ProductionCharts from "./components/visualizations/ProductionCharts"
import DeclineCurveAnalysis from "./components/visualizations/DeclineCurveAnalysis"
import MLModelDashboard from "./components/visualizations/MLModelDashboard"
import WellPerformanceComparison from "./components/visualizations/WellPerformanceComparison"

// Comprehensive module definitions based on the specifications
const modules = [
  {
    id: "reservoir-simulation",
    name: "Simulação de Reservatórios",
    icon: Layers,
    description: "Simulação completa de reservatórios",
    subModules: [
      { id: "black-oil", name: "Simulação Black Oil", icon: Droplets },
      { id: "compositional", name: "Simulação Composicional", icon: Beaker },
      { id: "thermal", name: "Simulação Térmica", icon: Flame },
      { id: "eor", name: "Simulação EOR", icon: Zap },
      { id: "rock-fluid-props", name: "Propriedades Rocha/Fluido", icon: Mountain },
      { id: "drive-mechanisms", name: "Mecanismos de Drive", icon: Waves },
    ],
  },
  {
    id: "production-analysis",
    name: "Análise de Produção",
    icon: TrendingUp,
    description: "Análise completa de dados de produção",
    subModules: [
      { id: "data-upload", name: "Upload de Dados", icon: Upload },
      { id: "decline-analysis", name: "Análise de Declínio (DCA)", icon: TrendingDown },
      { id: "material-balance", name: "Balanço de Materiais", icon: BarChart3 },
      { id: "production-forecast", name: "Previsão de Produção", icon: LineChart },
      { id: "uncertainty-analysis", name: "Análise de Incerteza", icon: PieChart },
    ],
  },
  {
    id: "optimization",
    name: "Otimização e Ajuste",
    icon: Target,
    description: "Otimização e ajuste de histórico",
    subModules: [
      { id: "history-matching", name: "Ajuste de Histórico", icon: Target },
      { id: "production-optimization", name: "Otimização de Produção", icon: Zap },
      { id: "scenario-analysis", name: "Análise de Cenários", icon: Shuffle },
    ],
  },
  {
    id: "modeling",
    name: "Modelagem Estática/Dinâmica",
    icon: Box,
    description: "Modelagem de reservatórios",
    subModules: [
      { id: "static-modeling", name: "Modelagem Estática", icon: Map },
      { id: "dynamic-modeling", name: "Modelagem Dinâmica", icon: Activity },
      { id: "facies-classification", name: "Classificação de Fácies", icon: Filter },
      { id: "seismic-integration", name: "Integração Sísmica", icon: Waves },
    ],
  },
  {
    id: "uncertainty",
    name: "Análise de Incertezas",
    icon: PieChart,
    description: "Análise de incertezas e sensitividade",
    subModules: [
      { id: "monte-carlo", name: "Monte Carlo", icon: Shuffle },
      { id: "sensitivity", name: "Análise de Sensitividade", icon: BarChart },
    ],
  },
  {
    id: "well-testing",
    name: "Teste de Poços",
    icon: Gauge,
    description: "Análise de testes de poços",
    subModules: [
      { id: "pressure-buildup", name: "Pressure Buildup", icon: TrendingUp },
      { id: "derivative-analysis", name: "Análise Derivativa", icon: LineChart },
    ],
  },
  {
    id: "economic-analysis",
    name: "Análise Econômica",
    icon: DollarSign,
    description: "Avaliação econômica e de reservas",
    subModules: [
      { id: "reserves-evaluation", name: "Avaliação de Reservas", icon: Database },
      { id: "economic-evaluation", name: "Avaliação Econômica", icon: DollarSign },
      { id: "economic-scenarios", name: "Cenários Econômicos", icon: PieChart },
    ],
  },
  {
    id: "visualization",
    name: "Visualização",
    icon: Eye,
    description: "Visualização 3D e exportação",
    subModules: [
      { id: "3d-visualization", name: "Visualização 3D", icon: Box },
      { id: "property-maps", name: "Mapas de Propriedades", icon: Map },
      { id: "export-reports", name: "Exportação e Relatórios", icon: FileText },
    ],
  },
  {
    id: "advanced-analytics",
    name: "Analytics Avançado e IA",
    icon: Brain,
    description: "Machine Learning e IA",
    subModules: [
      { id: "production-analytics", name: "Analytics de Produção", icon: TrendingUp },
      { id: "well-clustering", name: "Clusterização de Poços", icon: Network },
      { id: "spatial-patterns", name: "Padrões Espaciais", icon: Map },
      { id: "ml-forecasting", name: "Previsão com ML", icon: Brain },
      { id: "dimensionality-reduction", name: "Redução de Dimensionalidade", icon: Shuffle },
      { id: "correlation-analysis", name: "Análise de Correlações", icon: GitBranch },
      { id: "seismic-ai", name: "Sísmica com IA", icon: Waves },
      { id: "property-prediction", name: "Previsão de Propriedades", icon: Target },
    ],
  },
  {
    id: "integration",
    name: "Integração e Automação",
    icon: Workflow,
    description: "Integração de dados e automação",
    subModules: [
      { id: "data-integration", name: "Integração de Dados", icon: GitBranch },
      { id: "workflow-automation", name: "Automação de Workflows", icon: Workflow },
    ],
  },
]

// Mock AI insights data for different modules
const aiInsights = {
  "reservoir-simulation": {
    title: "Simulação de Reservatórios - Análise IA",
    summary: "IA identifica oportunidade de 18% de aumento na recuperação com estratégia EOR otimizada",
    confidence: 89,
    recommendations: [
      "Implementar injeção de polímero no setor norte",
      "Otimizar padrão de injeção para 5-spot",
      "Considerar perfuração horizontal em zonas de baixa permeabilidade",
    ],
    metrics: [
      { label: "Fator de Recuperação", value: "45.2%", change: "+3.1%", trend: "up" },
      { label: "EUR", value: "142.8 MMbbl", change: "+12.4%", trend: "up" },
      { label: "Tempo de Breakthrough", value: "8.2 anos", change: "+1.3 anos", trend: "up" },
    ],
  },
  "production-analysis": {
    title: "Análise de Produção - Insights IA",
    summary: "Anomalia detectada em 3 poços. IA recomenda intervenção imediata para evitar perda de 15% na produção",
    confidence: 94,
    recommendations: [
      "Workover urgente no Poço NS-003",
      "Aumentar frequência de monitoramento nos Poços NS-001, NS-004",
      "Otimizar taxas de gas lift no setor norte",
    ],
    metrics: [
      { label: "Produção Diária", value: "14,250 bbl/d", change: "-2.8%", trend: "down" },
      { label: "Water Cut", value: "28.3%", change: "+2.1%", trend: "up" },
      { label: "GOR", value: "920 scf/bbl", change: "+1.2%", trend: "up" },
    ],
  },
  "advanced-analytics": {
    title: "Analytics Avançado - Machine Learning",
    summary: "Modelos de ML identificam padrões complexos e preveem produção com 96% de acurácia",
    confidence: 96,
    recommendations: [
      "Aplicar modelo XGBoost para previsão de curto prazo",
      "Implementar clustering DBSCAN para otimização de grupos",
      "Usar CNN para análise automática de fácies sísmicas",
    ],
    metrics: [
      { label: "Acurácia do Modelo", value: "96.2%", change: "+1.8%", trend: "up" },
      { label: "R² Score", value: "0.94", change: "+0.03", trend: "up" },
      { label: "RMSE", value: "125 bbl/d", change: "-18 bbl/d", trend: "up" },
    ],
  },
}

export default function ComprehensiveReservoirInterface() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeModule, setActiveModule] = useState("reservoir-simulation")
  const [activeSubModule, setActiveSubModule] = useState("black-oil")
  const [aiProcessing, setAiProcessing] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState("connected")

  // Simulate AI processing
  const runAIAnalysis = () => {
    setAiProcessing(true)
    setTimeout(() => setAiProcessing(false), 3000)
  }

  // Get current AI insights
  const currentInsights = aiInsights[activeModule] || aiInsights["reservoir-simulation"]

  // Get current module and submodules
  const currentModule = modules.find((m) => m.id === activeModule)
  const subModules = currentModule?.subModules || []

  const renderModuleContent = () => {
    switch (activeModule) {
      case "reservoir-simulation":
        return <ReservoirSimulationContent activeSubModule={activeSubModule} />
      case "production-analysis":
        return <ProductionAnalysisContent activeSubModule={activeSubModule} />
      case "advanced-analytics":
        return <AdvancedAnalyticsContent activeSubModule={activeSubModule} />
      default:
        return <DefaultModuleContent module={currentModule} activeSubModule={activeSubModule} />
    }
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm z-10">
        <div className="flex items-center justify-between px-6 py-4">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              {sidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
            </Button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <Microscope className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                  Gaia Genesis
                </h1>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Plataforma Integrada de Engenharia de Reservatórios
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {connectionStatus === "connected" ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {connectionStatus === "connected" ? "IA Conectada" : "IA Offline"}
              </span>
            </div>
            <Button variant="ghost" size="sm">
              <Search className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Bell className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <User className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={cn(
            "bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-all duration-300 ease-in-out shadow-lg",
            sidebarCollapsed ? "w-16" : "w-80",
          )}
        >
          <div className="p-4 space-y-2 h-full overflow-y-auto">
            {modules.map((module) => {
              const IconComponent = module.icon
              const isActive = activeModule === module.id
              return (
                <div key={module.id}>
                  <Button
                    variant={isActive ? "default" : "ghost"}
                    className={cn(
                      "w-full justify-start transition-all duration-200",
                      sidebarCollapsed ? "px-3" : "px-4",
                      isActive
                        ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                        : "hover:bg-slate-100 dark:hover:bg-slate-700",
                    )}
                    onClick={() => setActiveModule(module.id)}
                  >
                    <IconComponent className={cn("h-5 w-5", sidebarCollapsed ? "" : "mr-3")} />
                    {!sidebarCollapsed && (
                      <div className="flex-1 text-left">
                        <div className="font-medium text-sm">{module.name}</div>
                        <div className="text-xs opacity-70">{module.description}</div>
                      </div>
                    )}
                  </Button>

                  {/* Sub-modules */}
                  {!sidebarCollapsed && isActive && module.subModules && (
                    <div className="mt-2 ml-4 space-y-1">
                      {module.subModules.map((subModule) => {
                        const SubIconComponent = subModule.icon
                        const isSubActive = activeSubModule === subModule.id
                        return (
                          <Button
                            key={subModule.id}
                            variant={isSubActive ? "secondary" : "ghost"}
                            size="sm"
                            className={cn(
                              "w-full justify-start text-xs",
                              isSubActive ? "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300" : "",
                            )}
                            onClick={() => setActiveSubModule(subModule.id)}
                          >
                            <SubIconComponent className="h-3 w-3 mr-2" />
                            {subModule.name}
                          </Button>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </aside>

        {/* Main Content - AI Analysis Area */}
        <main className="flex-1 overflow-auto">
          <div className="p-6 space-y-6">
            {/* AI Analysis Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{currentInsights.title}</h2>
                <p className="text-slate-600 dark:text-slate-400 mt-1">
                  Análise inteligente com IA para tomada de decisão otimizada
                </p>
              </div>
              <div className="flex items-center space-x-3">
                <Button
                  onClick={runAIAnalysis}
                  disabled={aiProcessing}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  {aiProcessing ? (
                    <>
                      <Cpu className="h-4 w-4 mr-2 animate-spin" />
                      Processando...
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4 mr-2" />
                      Executar Análise IA
                    </>
                  )}
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Exportar
                </Button>
              </div>
            </div>

            {/* AI Insights Summary */}
            <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-blue-200 dark:border-blue-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    <Sparkles className="h-5 w-5 text-purple-600" />
                    <span>Resumo de Insights IA</span>
                  </CardTitle>
                  <Badge variant="outline" className="bg-white/50">
                    Confiança: {currentInsights.confidence}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-lg text-slate-700 dark:text-slate-300">{currentInsights.summary}</p>
              </CardContent>
            </Card>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {currentInsights.metrics.map((metric, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm font-medium text-slate-600 dark:text-slate-400">
                      {metric.label}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="text-2xl font-bold text-slate-900 dark:text-white">{metric.value}</div>
                      <div
                        className={cn(
                          "flex items-center space-x-1 text-sm font-medium",
                          metric.trend === "up" ? "text-green-600" : "text-red-600",
                        )}
                      >
                        {metric.trend === "up" ? (
                          <TrendingUp className="h-4 w-4" />
                        ) : (
                          <TrendingDown className="h-4 w-4" />
                        )}
                        <span>{metric.change}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Module-specific Content */}
            {renderModuleContent()}
          </div>
        </main>
      </div>
    </div>
  )
}

// Reservoir Simulation Content Component
function ReservoirSimulationContent({ activeSubModule }) {
  return (
    <Tabs defaultValue="configuration" className="space-y-6">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="configuration">Configuração</TabsTrigger>
        <TabsTrigger value="simulation">Simulação</TabsTrigger>
        <TabsTrigger value="results">Resultados</TabsTrigger>
        <TabsTrigger value="analysis">Análise IA</TabsTrigger>
        <TabsTrigger value="3d">3D Grid</TabsTrigger>
      </TabsList>

      <TabsContent value="configuration" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Mountain className="h-5 w-5 text-blue-600" />
                <span>Propriedades da Rocha</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Porosidade (%)</Label>
                  <Input defaultValue="18.5" />
                </div>
                <div>
                  <Label>Permeabilidade (mD)</Label>
                  <Input defaultValue="125" />
                </div>
                <div>
                  <Label>Saturação de Água (%)</Label>
                  <Input defaultValue="25" />
                </div>
                <div>
                  <Label>Compressibilidade (1/psi)</Label>
                  <Input defaultValue="3.5e-6" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Droplets className="h-5 w-5 text-green-600" />
                <span>Propriedades do Fluido</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>API Gravity (°API)</Label>
                  <Input defaultValue="32" />
                </div>
                <div>
                  <Label>Viscosidade (cp)</Label>
                  <Input defaultValue="1.8" />
                </div>
                <div>
                  <Label>Bo (rb/stb)</Label>
                  <Input defaultValue="1.25" />
                </div>
                <div>
                  <Label>Rs (scf/stb)</Label>
                  <Input defaultValue="450" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Box className="h-5 w-5 text-purple-600" />
                <span>Configuração do Grid</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Dimensão X</Label>
                  <Input defaultValue="50" />
                </div>
                <div>
                  <Label>Dimensão Y</Label>
                  <Input defaultValue="50" />
                </div>
                <div>
                  <Label>Dimensão Z</Label>
                  <Input defaultValue="10" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="simulation" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Controles de Simulação</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div>
                  <Label>Tipo de Simulação</Label>
                  <Select defaultValue="black-oil">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="black-oil">Black Oil</SelectItem>
                      <SelectItem value="compositional">Composicional</SelectItem>
                      <SelectItem value="thermal">Térmica</SelectItem>
                      <SelectItem value="eor">EOR</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Tempo de Simulação (anos)</Label>
                  <Input defaultValue="20" />
                </div>
                <div>
                  <Label>Timestep Inicial (dias)</Label>
                  <Input defaultValue="1" />
                </div>
              </div>
              <div className="flex space-x-2">
                <Button className="flex-1">
                  <Play className="h-4 w-4 mr-2" />
                  Iniciar Simulação
                </Button>
                <Button variant="outline">
                  <Pause className="h-4 w-4 mr-2" />
                  Pausar
                </Button>
                <Button variant="outline">
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Reset
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Status da Simulação</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Progresso</span>
                  <span>65%</span>
                </div>
                <Progress value={65} className="h-2" />
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Tempo Decorrido</span>
                  <span>2h 15m</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Tempo Estimado</span>
                  <span>1h 20m</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Timestep Atual</span>
                  <span>4,750 / 7,300</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="results" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Produção Acumulada</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <LineChart className="h-12 w-12 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">Gráfico de produção acumulada</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Distribuição de Pressão</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Map className="h-12 w-12 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">Mapa de pressão do reservatório</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="analysis" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Brain className="h-5 w-5 text-purple-600" />
              <span>Análise IA dos Resultados</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
              <h4 className="font-medium mb-2">Otimização de Recuperação</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                A IA identificou que a implementação de injeção de água no setor norte pode aumentar a recuperação em
                15-20%. O modelo sugere um padrão de injeção 5-spot com taxa otimizada de 2,500 bbl/d por poço injetor.
              </p>
            </div>
            <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
              <h4 className="font-medium mb-2">Análise de Sensitividade</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Os parâmetros mais sensíveis identificados são: permeabilidade vertical (±25% impacto), heterogeneidade
                do reservatório (±18% impacto) e propriedades de molhabilidade (±12% impacto).
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="3d" className="space-y-6">
        <ReservoirVisualization3D />
      </TabsContent>
    </Tabs>
  )
}

// Production Analysis Content Component
function ProductionAnalysisContent({ activeSubModule }) {
  return (
    <Tabs defaultValue="data-upload" className="space-y-6">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="data-upload">Upload de Dados</TabsTrigger>
        <TabsTrigger value="decline-analysis">Análise de Declínio</TabsTrigger>
        <TabsTrigger value="forecasting">Previsão</TabsTrigger>
        <TabsTrigger value="ai-insights">Insights IA</TabsTrigger>
        <TabsTrigger value="charts">Charts</TabsTrigger>
      </TabsList>

      <TabsContent value="data-upload" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Upload className="h-5 w-5 text-blue-600" />
              <span>Upload de Dados de Produção</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center">
              <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
                Arraste arquivos aqui ou clique para selecionar
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">Suporte para CSV, Excel, LAS, SEG-Y</p>
              <Button>Selecionar Arquivos</Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                <div className="text-sm text-green-700 dark:text-green-300">Dados de Produção</div>
                <div className="text-lg font-bold text-green-900 dark:text-green-100">production_data.csv</div>
                <div className="text-xs text-green-600 dark:text-green-400">2.3 MB • Processado</div>
              </div>
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="text-sm text-blue-700 dark:text-blue-300">Dados PVT</div>
                <div className="text-lg font-bold text-blue-900 dark:text-blue-100">pvt_analysis.xlsx</div>
                <div className="text-xs text-blue-600 dark:text-blue-400">1.8 MB • Processado</div>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                <div className="text-sm text-purple-700 dark:text-purple-300">Dados Sísmicos</div>
                <div className="text-lg font-bold text-purple-900 dark:text-purple-100">seismic_3d.segy</div>
                <div className="text-xs text-purple-600 dark:text-purple-400">125 MB • Processando...</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="decline-analysis" className="space-y-6">
        <DeclineCurveAnalysis />
      </TabsContent>

      <TabsContent value="forecasting" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Previsão de Produção</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 bg-gradient-to-br from-green-50 to-blue-100 dark:from-green-900/20 dark:to-blue-800/20 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <TrendingUp className="h-16 w-16 text-green-500 mx-auto mb-4" />
                <p className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Previsão de Produção - 10 Anos
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Combinando análise de declínio e machine learning
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="ai-insights" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <span>Anomalias Detectadas</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-red-700 dark:text-red-300">Poço NS-003</span>
                  <Badge variant="destructive">Crítico</Badge>
                </div>
                <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                  Queda abrupta de 35% na produção detectada
                </p>
              </div>
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Poço NS-001</span>
                  <Badge variant="outline" className="border-yellow-500 text-yellow-700">
                    Atenção
                  </Badge>
                </div>
                <p className="text-xs text-yellow-600 dark:text-yellow-400 mt-1">
                  Aumento gradual do water cut observado
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span>Recomendações IA</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-sm font-medium text-green-700 dark:text-green-300 mb-1">
                  Otimização de Gas Lift
                </div>
                <p className="text-xs text-green-600 dark:text-green-400">
                  Ajustar taxa para 1.2 MMscf/d no Poço NS-002
                </p>
              </div>
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-1">Workover Programado</div>
                <p className="text-xs text-blue-600 dark:text-blue-400">Agendar limpeza de parafina no Poço NS-004</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="charts" className="space-y-6">
        <ProductionCharts />
      </TabsContent>
    </Tabs>
  )
}

// Advanced Analytics Content Component
function AdvancedAnalyticsContent({ activeSubModule }) {
  return (
    <Tabs defaultValue="ml-models" className="space-y-6">
      <TabsList className="grid w-full grid-cols-6">
        <TabsTrigger value="ml-models">Modelos ML</TabsTrigger>
        <TabsTrigger value="clustering">Clustering</TabsTrigger>
        <TabsTrigger value="seismic-ai">Sísmica IA</TabsTrigger>
        <TabsTrigger value="predictions">Predições</TabsTrigger>
        <TabsTrigger value="ml-dashboard">ML Dashboard</TabsTrigger>
        <TabsTrigger value="well-comparison">Well Comparison</TabsTrigger>
      </TabsList>

      <TabsContent value="ml-models" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">XGBoost</CardTitle>
              <CardDescription>Previsão de produção</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Acurácia</span>
                  <span className="font-medium">96.2%</span>
                </div>
                <Progress value={96.2} className="h-2" />
                <div className="flex justify-between text-sm">
                  <span>R² Score</span>
                  <span className="font-medium">0.94</span>
                </div>
                <Progress value={94} className="h-2" />
                <Button size="sm" className="w-full">
                  Treinar Modelo
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Redes Neurais</CardTitle>
              <CardDescription>Análise de padrões</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Acurácia</span>
                  <span className="font-medium">94.8%</span>
                </div>
                <Progress value={94.8} className="h-2" />
                <div className="flex justify-between text-sm">
                  <span>Loss</span>
                  <span className="font-medium">0.032</span>
                </div>
                <Progress value={85} className="h-2" />
                <Button size="sm" className="w-full">
                  Treinar Modelo
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Random Forest</CardTitle>
              <CardDescription>Classificação de fácies</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Acurácia</span>
                  <span className="font-medium">91.5%</span>
                </div>
                <Progress value={91.5} className="h-2" />
                <div className="flex justify-between text-sm">
                  <span>F1-Score</span>
                  <span className="font-medium">0.89</span>
                </div>
                <Progress value={89} className="h-2" />
                <Button size="sm" className="w-full">
                  Treinar Modelo
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="clustering" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Clustering DBSCAN</CardTitle>
              <CardDescription>Agrupamento de poços por similaridade</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-purple-50 to-pink-100 dark:from-purple-900/20 dark:to-pink-800/20 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Network className="h-12 w-12 text-purple-500 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">Visualização de clusters de poços</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resultados do Clustering</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-sm text-blue-700 dark:text-blue-300">Cluster 1 - Alto Desempenho</div>
                  <div className="text-lg font-bold text-blue-900 dark:text-blue-100">8 poços</div>
                  <div className="text-xs text-blue-600 dark:text-blue-400">Produção média: 1,200 bbl/d</div>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-sm text-green-700 dark:text-green-300">Cluster 2 - Desempenho Médio</div>
                  <div className="text-lg font-bold text-green-900 dark:text-green-100">12 poços</div>
                  <div className="text-xs text-green-600 dark:text-green-400">Produção média: 750 bbl/d</div>
                </div>
                <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                  <div className="text-sm text-orange-700 dark:text-orange-300">Cluster 3 - Baixo Desempenho</div>
                  <div className="text-lg font-bold text-orange-900 dark:text-orange-100">5 poços</div>
                  <div className="text-xs text-orange-600 dark:text-orange-400">Produção média: 320 bbl/d</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="seismic-ai" className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Waves className="h-5 w-5 text-blue-600" />
              <span>Análise Sísmica com IA</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label>Tipo de Análise</Label>
                  <Select defaultValue="facies">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="facies">Classificação de Fácies</SelectItem>
                      <SelectItem value="attributes">Extração de Atributos</SelectItem>
                      <SelectItem value="geobodies">Detecção de Geobodies</SelectItem>
                      <SelectItem value="autoencoder">Autoencoder</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Modelo CNN</Label>
                  <Select defaultValue="resnet">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="resnet">ResNet-50</SelectItem>
                      <SelectItem value="unet">U-Net</SelectItem>
                      <SelectItem value="vgg">VGG-16</SelectItem>
                      <SelectItem value="custom">Modelo Customizado</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button className="w-full">
                  <Brain className="h-4 w-4 mr-2" />
                  Executar Análise IA
                </Button>
              </div>
              <div className="h-64 bg-gradient-to-br from-blue-50 to-cyan-100 dark:from-blue-900/20 dark:to-cyan-800/20 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <Waves className="h-12 w-12 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Visualização de dados sísmicos processados
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="predictions" className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Previsão de Propriedades</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-sm text-blue-700 dark:text-blue-300">Porosidade Predita</div>
                  <div className="text-xl font-bold text-blue-900 dark:text-blue-100">19.2% ± 1.5%</div>
                  <div className="text-xs text-blue-600 dark:text-blue-400">Confiança: 94%</div>
                </div>
                <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-sm text-green-700 dark:text-green-300">Permeabilidade Predita</div>
                  <div className="text-xl font-bold text-green-900 dark:text-green-100">145 mD ± 25 mD</div>
                  <div className="text-xs text-green-600 dark:text-green-400">Confiança: 89%</div>
                </div>
                <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="text-sm text-purple-700 dark:text-purple-300">Saturação de Água</div>
                  <div className="text-xl font-bold text-purple-900 dark:text-purple-100">22.8% ± 3.2%</div>
                  <div className="text-xs text-purple-600 dark:text-purple-400">Confiança: 91%</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Análise de Correlações</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-800/20 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <GitBranch className="h-12 w-12 text-green-500 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">Matriz de correlação entre poços</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>

      <TabsContent value="ml-dashboard" className="space-y-6">
        <MLModelDashboard />
      </TabsContent>

      <TabsContent value="well-comparison" className="space-y-6">
        <WellPerformanceComparison />
      </TabsContent>
    </Tabs>
  )
}

// Default Module Content Component
function DefaultModuleContent({ module, activeSubModule }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          {module?.icon && <module.icon className="h-5 w-5 text-blue-600" />}
          <span>{module?.name || "Módulo"}</span>
        </CardTitle>
        <CardDescription>{module?.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
            {module?.icon && <module.icon className="h-8 w-8 text-slate-400" />}
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
            {module?.name} - Em Desenvolvimento
          </h3>
          <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
            Este módulo está sendo desenvolvido e estará disponível em breve. Submódulo ativo: {activeSubModule}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
