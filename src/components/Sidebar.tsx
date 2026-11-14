import React, { useState, useMemo, useEffect } from "react";
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
  ChevronDown,
  ShieldAlert,
  Zap,
  Boxes,
  FlaskConical,
  Package,
  Compass,
  Activity,
  Wrench,
  Search,
  FileUp,
  GitCompare,
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
    id: "scenario-comparison",
    nameKey: "Scenario Comparison",
    defaultName: "Scenario Comparison",
    icon: GitCompare,
    descriptionKey: "Compare saved reservoir simulation scenarios",
    defaultDescription: "Compare saved reservoir simulation scenarios",
    categoryKey: "reservoirEng",
    defaultCategory: "Engenharia de Reservatório",
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
    id: "reservoir-compressibility",
    nameKey: "Compressibilidade de Reservatório",
    defaultName: "Compressibilidade de Reservatório",
    icon: Activity,
    descriptionKey: "Compressibilidade da rocha, gás e total com limites explícitos",
    defaultDescription: "Compressibilidade da rocha, gás e total com limites explícitos",
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
    id: "production-data-import",
    nameKey: "Importação de Dados de Produção",
    defaultName: "Importação de Dados de Produção",
    icon: FileUp,
    descriptionKey: "Importar histórico de produção em CSV",
    defaultDescription: "Importar histórico de produção em CSV",
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
    id: "well-test-analysis",
    nameKey: "Análise de Teste de Poço",
    defaultName: "Análise de Teste de Poço",
    icon: Activity,
    descriptionKey: "Drawdown, buildup, permeabilidade e skin",
    defaultDescription: "Drawdown, buildup, permeabilidade e skin",
    categoryKey: "reservoirEng",
    defaultCategory: "Engenharia de Reservatório",
  },
  {
    id: "reservoir-operations",
    nameKey: "Choke, Tubing e Gas-Lift",
    defaultName: "Choke, Tubing e Gas-Lift",
    icon: Zap,
    descriptionKey: "Correlações de choke, esforços de tubing e válvulas de gas-lift",
    defaultDescription: "Correlações de choke, esforços de tubing e válvulas de gas-lift",
    categoryKey: "productionEng",
    defaultCategory: "Engenharia de Produção",
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
}

export default function Sidebar({
  activeModule,
  onSelectModule,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  const { t, isPt } = useI18n();
  const { activeScenario } = useSessionRegistry();
  const [filterQuery, setFilterQuery] = useState("");
  const activeCategoryKey =
    APP_MODULES.find((module) => module.id === activeModule)?.categoryKey ?? "overview";
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    () => new Set([activeCategoryKey]),
  );

  useEffect(() => {
    setExpandedCategories((current) => {
      if (current.has(activeCategoryKey)) return current;
      return new Set(current).add(activeCategoryKey);
    });
  }, [activeCategoryKey]);

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
    const map = new Map<string, { name: string; modules: NavModule[] }>();
    filteredModules.forEach((mod) => {
      const cat = (t.categories as Record<string, string>)[mod.categoryKey] || mod.defaultCategory;
      if (!map.has(mod.categoryKey)) {
        map.set(mod.categoryKey, { name: cat, modules: [] });
      }
      map.get(mod.categoryKey)!.modules.push(mod);
    });
    return Array.from(map.entries());
  }, [filteredModules, t.categories]);

  return (
    <aside
      className={cn(
        "relative flex shrink-0 flex-col border-r border-border bg-card transition-[width] duration-200 ease-out select-none",
        collapsed ? "w-[4.25rem]" : "w-64"
      )}
      aria-label={isPt ? "Navegação principal" : "Primary navigation"}
    >
      {/* Sidebar Header & Collapse Toggle */}
      <div className="flex h-12 items-center justify-between border-b border-border px-3">
        {!collapsed && (
          <span className="px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            {t.modulesTitle}
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="ml-auto h-8 w-8 text-muted-foreground hover:text-foreground"
          title={collapsed ? "Expandir menu" : "Recolher menu"}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Search / Filter Input */}
      {!collapsed && (
        <div className="border-b border-border/60 p-2.5">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              type="text"
              placeholder={t.searchModules}
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="h-9 border-border bg-background pl-8 text-xs"
            />
          </div>
        </div>
      )}

      {/* Navigation List */}
      <nav className="flex-1 space-y-5 overflow-y-auto px-2 py-3">
        {categories.map(([categoryKey, category]) => {
          const isExpanded = Boolean(filterQuery.trim()) || expandedCategories.has(categoryKey);
          const groupId = `sidebar-group-${categoryKey}`;
          return (
            <div key={categoryKey} className="space-y-1">
              {!collapsed && (
                <button
                  type="button"
                  aria-expanded={isExpanded}
                  aria-controls={groupId}
                  onClick={() => {
                    setExpandedCategories((current) => {
                      const next = new Set(current);
                      if (next.has(categoryKey)) next.delete(categoryKey);
                      else next.add(categoryKey);
                      return next;
                    });
                  }}
                  className="mb-1 flex w-full items-center justify-between rounded px-2 py-1 text-left text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground/80 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <span>{category.name}</span>
                  {isExpanded ? (
                    <ChevronDown className="h-3 w-3" aria-hidden="true" />
                  ) : (
                    <ChevronRight className="h-3 w-3" aria-hidden="true" />
                  )}
                </button>
              )}
              <div id={groupId} hidden={!collapsed && !isExpanded}>
                {category.modules.map((mod) => {
                  const Icon = mod.icon;
                  const isActive = activeModule === mod.id;
                  return (
                    <button
                      key={mod.id}
                      onClick={() => onSelectModule(mod.id)}
                      title={collapsed ? `${mod.defaultName} — ${mod.defaultDescription}` : undefined}
                      aria-label={mod.defaultName}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-lg px-2.5 py-2.5 text-left text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        isActive
                          ? "bg-primary/10 font-semibold text-primary ring-1 ring-inset ring-primary/20"
                          : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                      )}
                    >
                      <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground")} />
                      {!collapsed && (
                        <div className="flex-1 overflow-hidden leading-tight">
                          <div className="truncate font-medium">{mod.defaultName}</div>
                          <div className="mt-0.5 truncate text-[10px] text-muted-foreground/80">
                            {mod.defaultDescription}
                          </div>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
        {categories.length === 0 && (
          <p className="px-3 py-4 text-xs text-muted-foreground">{t.noModulesFound}</p>
        )}
      </nav>

      {/* Sidebar Footer with Active Scenario Indicator */}
      {!collapsed && (
        <div className="space-y-1.5 border-t border-border px-4 py-3 text-xs">
          <div className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
            {t.activeScenario}
          </div>
          <div className="truncate text-[11px] font-medium text-foreground" title={activeScenario.name}>
              {activeScenario.name}
          </div>
        </div>
      )}
    </aside>
  );
}
