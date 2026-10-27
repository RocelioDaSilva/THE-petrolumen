import React from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface NavModule {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  category: string;
}

export const APP_MODULES: NavModule[] = [
  {
    id: "dashboard",
    name: "Dashboard Geral",
    icon: LayoutDashboard,
    description: "Visão integrada e status dos módulos",
    category: "Visão Geral",
  },
  {
    id: "well-control",
    name: "Controle de Poço & Kick Sheet",
    icon: ShieldAlert,
    description: "KMW, ICP/FCP, MAASP & W&W Method",
    category: "Perfuração & Poço",
  },
  {
    id: "drilling-hydraulics",
    name: "Hidráulica & Operações",
    icon: Zap,
    description: "ECD, Jatos na Broca, HHP & Teste LOT",
    category: "Perfuração & Poço",
  },
  {
    id: "surface-facilities",
    name: "Instalações de Superfície",
    icon: Boxes,
    description: "Separadores 2/3 Fases & Coluna TEG",
    category: "Engenharia de Superfície",
  },
  {
    id: "reservoir-simulation",
    name: "Simulação de Reservatórios",
    icon: Layers,
    description: "Modelo 1D IMPES & Malha 3D",
    category: "Engenharia de Reservatório",
  },
  {
    id: "production-dca",
    name: "Curvas de Declínio (DCA)",
    icon: TrendingDown,
    description: "Modelos Arps, Duong & EUR",
    category: "Engenharia de Produção",
  },
  {
    id: "pvt",
    name: "Cálculos PVT & Fases",
    icon: Beaker,
    description: "Fator Z, Bo, Bg, Rs e Envelope P-T",
    category: "Engenharia de Reservatório",
  },
  {
    id: "nodal",
    name: "Análise Nodal",
    icon: Gauge,
    description: "Curvas IPR vs VLP e Ponto Ótimo",
    category: "Engenharia de Produção",
  },
  {
    id: "rta",
    name: "RTA & Balanço Materiais",
    icon: Target,
    description: "Flowing Material Balance (FMB)",
    category: "Engenharia de Reservatório",
  },
  {
    id: "economics",
    name: "Avaliação Econômica",
    icon: DollarSign,
    description: "VPL, TIR, Payback e Fluxo de Caixa",
    category: "Economia e Decisão",
  },
  {
    id: "ai-analytics",
    name: "IA & Machine Learning",
    icon: Brain,
    description: "Previsão com XGBoost, SVR e LSTM",
    category: "Inteligência Artificial",
  },
  {
    id: "well-logs",
    name: "Perfis de Poço (LAS)",
    icon: Database,
    description: "Visualizador de Raio Gama e RT",
    category: "Dados e Geologia",
  },
  {
    id: "connectors",
    name: "Conectores & Eclipse",
    icon: Workflow,
    description: "Integração Eclipse, CMG e OSDU",
    category: "Infraestrutura",
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
  return (
    <aside
      className={cn(
        "relative flex flex-col bg-card border-r border-border transition-all duration-300 ease-in-out select-none",
        collapsed ? "w-16" : "w-72"
      )}
    >
      {/* Collapse Toggle Button */}
      <div className="flex items-center justify-between p-3 border-b border-border">
        {!collapsed && (
          <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-2">
            Módulos PetroLúmen
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

      {/* Navigation List */}
      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {APP_MODULES.map((item) => {
          const Icon = item.icon;
          const isActive = activeModule === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectModule(item.id)}
              className={cn(
                "w-full flex items-center rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-all group relative",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
              title={collapsed ? `${item.name} - ${item.description}` : undefined}
            >
              <Icon
                className={cn(
                  "w-5 h-5 flex-shrink-0 transition-colors",
                  isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-primary",
                  !collapsed && "mr-3"
                )}
              />
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-xs truncate leading-tight">{item.name}</div>
                  <div
                    className={cn(
                      "text-[10px] truncate leading-tight mt-0.5",
                      isActive ? "text-primary-foreground/80" : "text-muted-foreground/70"
                    )}
                  >
                    {item.description}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Info */}
      {!collapsed && (
        <div className="p-3 border-t border-border text-[11px] text-muted-foreground bg-muted/20">
          <p className="font-medium text-foreground">Ambiente de Simulação</p>
          <p className="text-[10px] text-muted-foreground">Petróleo & Gás Natural • 2026</p>
        </div>
      )}
    </aside>
  );
}
