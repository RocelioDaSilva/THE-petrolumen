import React, { useState, useMemo } from "react";
import {
  LayoutDashboard,
  Layers,
  TrendingDown,
  Beaker,
  Gauge,
  Target,
  DollarSign,
  Brain,
  Database,
  Workflow,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Zap,
  Boxes,
  FlaskConical,
  Package,
  Compass,
  Activity,
  Wrench,
  Search,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";
import { useSessionRegistry } from "@/lib/sessionRegistry";

export interface NavModule {
  id: string;
  nameKey: string;
  defaultName: string;
  icon: React.ComponentType<{ className?: string }>;
  descriptionKey: string;
  defaultDescription: string;
  categoryKey: string;
  defaultCategory: string;
}

export const APP_MODULES: NavModule[] = [
  {
    id: "dashboard",
    nameKey: "Dashboard Geral",
    defaultName: "Dashboard Geral",
    icon: LayoutDashboard,
    descriptionKey: "Visão integrada e status dos módulos",
    defaultDescription: "Visão integrada e status dos módulos",
    categoryKey: "overview",
    defaultCategory: "Visão Geral",
  },
  {
    id: "well-control",
    nameKey: "Controle de Poço & Kick Sheet",
    defaultName: "Controle de Poço & Kick Sheet",
    icon: ShieldAlert,
    descriptionKey: "KMW, ICP/FCP, MAASP & W&W Method",
    defaultDescription: "KMW, ICP/FCP, MAASP & W&W Method",
    categoryKey: "drillingWell",
    defaultCategory: "Perfuração & Poço",
  },
  {
    id: "drilling-hydraulics",
    nameKey: "Hidráulica & Operações",
    defaultName: "Hidráulica & Operações",
    icon: Zap,
    descriptionKey: "ECD, Jatos na Broca, HHP & Teste LOT",
    defaultDescription: "ECD, Jatos na Broca, HHP & Teste LOT",
    categoryKey: "drillingWell",
    defaultCategory: "Perfuração & Poço",
  },
  {
    id: "drilling-fluids",
    nameKey: "Fluidos de Perfuração (Ch. 2)",
    defaultName: "Fluidos de Perfuração (Ch. 2)",
    icon: FlaskConical,
    descriptionKey: "Reologia Fann, Adensamento & Retorta",
    defaultDescription: "Reologia Fann, Adensamento & Retorta",
    categoryKey: "drillingWell",
    defaultCategory: "Perfuração & Poço",
  },
  {
    id: "cementing",
    nameKey: "Cimentação & Pastas API (Ch. 3)",
    defaultName: "Cimentação & Pastas API (Ch. 3)",
    icon: Package,
    descriptionKey: "Formulação API, Bogue & Tempos",
    defaultDescription: "Formulação API, Bogue & Tempos",
    categoryKey: "drillingWell",
    defaultCategory: "Perfuração & Poço",
  },
  {
    id: "casing-directional",
    nameKey: "Revestimento & Direcional (Ch. 7-8)",
    defaultName: "Revestimento & Direcional (Ch. 7-8)",
    icon: Compass,
    descriptionKey: "Barlow, Colapso Biaxial & Curvatura 3D",
    defaultDescription: "Barlow, Colapso Biaxial & Curvatura 3D",
    categoryKey: "drillingWell",
    defaultCategory: "Perfuração & Poço",
  },
  {
    id: "field-basic",
    nameKey: "Fórmulas de Campo (Ch. 1)",
    defaultName: "Fórmulas de Campo (Ch. 1)",
    icon: Wrench,
    descriptionKey: "Hidrostática, Gradientes & Capacidades",
    defaultDescription: "Hidrostática, Gradientes & Capacidades",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "rig-operations",
    nameKey: "Operações de Sonda (Ch. 2)",
    defaultName: "Operações de Sonda (Ch. 2)",
    icon: Gauge,
    descriptionKey: "Acumulador BOP, Tampão Pesado & Pílulas",
    defaultDescription: "Acumulador BOP, Tampão Pesado & Pílulas",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "stuck-pipe",
    nameKey: "Prisão de Coluna & Pescaria (Ch. 4)",
    defaultName: "Prisão de Coluna & Pescaria (Ch. 4)",
    icon: ShieldAlert,
    descriptionKey: "Ponto Livre, Força de Tração & Economia",
    defaultDescription: "Ponto Livre, Força de Tração & Economia",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "rig-loads",
    nameKey: "Cargas no Mastro (Ch. 5)",
    defaultName: "Cargas no Mastro (Ch. 5)",
    icon: Boxes,
    descriptionKey: "Tensão Linha Rápida & Fatores de Segurança",
    defaultDescription: "Tensão Linha Rápida & Fatores de Segurança",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "ton-miles",
    nameKey: "Serviço de Cabo Ton-Mile (Ch. 7)",
    defaultName: "Serviço de Cabo Ton-Mile (Ch. 7)",
    icon: Activity,
    descriptionKey: "Manobra Completa & Programa de Corte",
    defaultDescription: "Manobra Completa & Programa de Corte",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "tank-capacity",
    nameKey: "Capacidade de Tanques (Ch. 8)",
    defaultName: "Capacidade de Tanques (Ch. 8)",
    icon: Package,
    descriptionKey: "Tanques Cilíndricos, Cônicos & Retangulares",
    defaultDescription: "Tanques Cilíndricos, Cônicos & Retangulares",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "air-gas",
    nameKey: "Perfuração com Ar & Gás (Ch. 11)",
    defaultName: "Perfuração com Ar & Gás (Ch. 11)",
    icon: FlaskConical,
    descriptionKey: "Injeção Compressível & Pressões Anulares",
    defaultDescription: "Injeção Compressível & Pressões Anulares",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "completions",
    nameKey: "Completação & Testemunho (Ch. 12)",
    defaultName: "Completação & Testemunho (Ch. 12)",
    icon: Layers,
    descriptionKey: "Dean-Stark, Alongamento da Coluna & Core",
    defaultDescription: "Dean-Stark, Alongamento da Coluna & Core",
    categoryKey: "fieldOps",
    defaultCategory: "Operações de Campo",
  },
  {
    id: "surface-facilities",
    nameKey: "Instalações de Superfície",
    defaultName: "Instalações de Superfície",
    icon: Boxes,
    descriptionKey: "Separadores 2/3 Fases & Coluna TEG",
    defaultDescription: "Separadores 2/3 Fases & Coluna TEG",
    categoryKey: "surfaceFacilities",
    defaultCategory: "Engenharia de Superfície",
  },
  {
    id: "reservoir-simulation",
    nameKey: "Simulação de Reservatórios",
    defaultName: "Simulação de Reservatórios",
    icon: Layers,
    descriptionKey: "Modelo 1D IMPES & Malha 3D",
    defaultDescription: "Modelo 1D IMPES & Malha 3D",
    categoryKey: "reservoirEng",
    defaultCategory: "Engenharia de Reservatório",
  },
  {
    id: "production-dca",
    nameKey: "Curvas de Declínio (DCA)",
    defaultName: "Curvas de Declínio (DCA)",
    icon: TrendingDown,
    descriptionKey: "Modelos Arps, Duong & EUR",
    defaultDescription: "Modelos Arps, Duong & EUR",
    categoryKey: "productionEng",
    defaultCategory: "Engenharia de Produção",
  },
  {
    id: "pvt",
    nameKey: "Cálculos PVT & Fases",
    defaultName: "Cálculos PVT & Fases",
    icon: Beaker,
    descriptionKey: "Fator Z, Bo, Bg, Rs e Envelope P-T",
    defaultDescription: "Fator Z, Bo, Bg, Rs e Envelope P-T",
    categoryKey: "reservoirEng",
    defaultCategory: "Engenharia de Reservatório",
  },
  {
    id: "nodal",
    nameKey: "Análise Nodal",
    defaultName: "Análise Nodal",
    icon: Gauge,
    descriptionKey: "Curvas IPR vs VLP e Ponto Ótimo",
    defaultDescription: "Curvas IPR vs VLP e Ponto Ótimo",
    categoryKey: "productionEng",
    defaultCategory: "Engenharia de Produção",
  },
  {
    id: "rta",
    nameKey: "RTA & Balanço Materiais",
    defaultName: "RTA & Balanço Materiais",
    icon: Target,
    descriptionKey: "Flowing Material Balance (FMB)",
    defaultDescription: "Flowing Material Balance (FMB)",
    categoryKey: "reservoirEng",
    defaultCategory: "Engenharia de Reservatório",
  },
  {
    id: "economics",
    nameKey: "Avaliação Econômica",
    defaultName: "Avaliação Econômica",
    icon: DollarSign,
    descriptionKey: "VPL, TIR, Payback e Fluxo de Caixa",
    defaultDescription: "VPL, TIR, Payback e Fluxo de Caixa",
    categoryKey: "economicsDecision",
    defaultCategory: "Economia e Decisão",
  },
  {
    id: "ai-analytics",
    nameKey: "IA & Machine Learning",
    defaultName: "IA & Machine Learning",
    icon: Brain,
    descriptionKey: "Previsão com XGBoost, SVR e LSTM",
    defaultDescription: "Previsão com XGBoost, SVR e LSTM",
    categoryKey: "artificialIntelligence",
    defaultCategory: "Inteligência Artificial",
  },
  {
    id: "well-logs",
    nameKey: "Perfis de Poço (LAS)",
    defaultName: "Perfis de Poço (LAS)",
    icon: Database,
    descriptionKey: "Visualizador de Raio Gama e RT",
    defaultDescription: "Visualizador de Raio Gama e RT",
    categoryKey: "dataGeology",
    defaultCategory: "Dados e Geologia",
  },
  {
    id: "connectors",
    nameKey: "Conectores & Eclipse",
    defaultName: "Conectores & Eclipse",
    icon: Workflow,
    descriptionKey: "Integração Eclipse, CMG e OSDU",
    defaultDescription: "Integração Eclipse, CMG e OSDU",
    categoryKey: "infrastructure",
    defaultCategory: "Infraestrutura",
  },
];

interface SidebarProps {
  activeModule: string;
  onSelectModule: (id: string) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onOpenDocs?: () => void;
}

export default function Sidebar({
  activeModule,
  onSelectModule,
  collapsed,
  onToggleCollapse,
  onOpenDocs,
}: SidebarProps) {
  const { t, isPt } = useI18n();
  const { activeScenario } = useSessionRegistry();
  const [filterQuery, setFilterQuery] = useState("");

  const filteredModules = useMemo(() => {
    if (!filterQuery.trim()) return APP_MODULES;
    const q = filterQuery.toLowerCase();
    return APP_MODULES.filter(
      (m) =>
        m.defaultName.toLowerCase().includes(q) ||
        m.defaultDescription.toLowerCase().includes(q)
    );
  }, [filterQuery]);

  // Group modules by category
  const categories = useMemo(() => {
    const map = new Map<string, typeof APP_MODULES>();
    filteredModules.forEach((mod) => {
      const cat = (t.categories as Record<string, string>)[mod.categoryKey] || mod.defaultCategory;
      if (!map.has(cat)) {
        map.set(cat, []);
      }
      map.get(cat)!.push(mod);
    });
    return Array.from(map.entries());
  }, [filteredModules, t.categories]);

  return (
    <aside
      className={cn(
        "relative flex flex-col bg-card border-r border-border transition-all duration-300 ease-in-out select-none",
        collapsed ? "w-16" : "w-72"
      )}
    >
      {/* Sidebar Header & Collapse Toggle */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        {!collapsed && (
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-2">
            {t.modulesTitle}
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="h-7 w-7 text-muted-foreground ml-auto"
          title={collapsed ? "Expandir menu" : "Recolher menu"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Search / Filter Input */}
      {!collapsed && (
        <div className="p-2 border-b border-border/60">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              type="text"
              placeholder={t.searchModules}
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="h-8 pl-8 text-xs bg-muted/40 border-border"
            />
          </div>
        </div>
      )}

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {categories.map(([catName, mods]) => (
          <div key={catName} className="space-y-1">
            {!collapsed && (
              <h3 className="px-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/80 mb-1">
                {catName}
              </h3>
            )}
            {mods.map((mod) => {
              const Icon = mod.icon;
              const isActive = activeModule === mod.id;
              return (
                <button
                  key={mod.id}
                  onClick={() => onSelectModule(mod.id)}
                  title={collapsed ? `${mod.defaultName} — ${mod.defaultDescription}` : undefined}
                  className={cn(
                    "w-full flex items-center space-x-3 px-2.5 py-2 rounded-lg text-xs font-medium transition-colors text-left",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-xs font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-primary-foreground" : "text-muted-foreground")} />
                  {!collapsed && (
                    <div className="flex-1 overflow-hidden leading-tight">
                      <div className="truncate font-medium">{mod.defaultName}</div>
                      <div className={cn("text-[10px] truncate mt-0.5", isActive ? "text-primary-foreground/80" : "text-muted-foreground/70")}>
                        {mod.defaultDescription}
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      {/* Sidebar Footer with Active Scenario Indicator */}
      {!collapsed && (
        <div className="p-3 border-t border-border bg-muted/20 text-xs space-y-2">
          <div className="flex items-center justify-between text-[11px] text-muted-foreground">
            <span className="font-semibold uppercase tracking-wider text-[10px]">{t.activeScenario}</span>
            <span className="text-[10px] text-indigo-500 font-medium truncate max-w-[120px]">
              {activeScenario.name}
            </span>
          </div>
          {onOpenDocs && (
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenDocs}
              className="w-full text-xs h-7.5 gap-1.5 border-border bg-card hover:bg-muted font-medium"
            >
              <BookOpen className="w-3.5 h-3.5 text-primary" />
              {t.docsButton} (32/32)
            </Button>
          )}
        </div>
      )}
    </aside>
  );
}
