import React from "react";
import { Badge } from "@/components/ui/badge";
import { Calculator, Database, Cpu, Eye, ShieldCheck } from "lucide-react";

export type ProvenanceKind =
  | "calculated"
  | "sample"
  | "simulated"
  | "illustrative";

export interface ProvenanceBadgeProps {
  kind: ProvenanceKind;
  source?: string;
  className?: string;
  size?: "sm" | "default";
}

const CONFIG: Record<
  ProvenanceKind,
  {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    className: string;
    description: string;
  }
> = {
  calculated: {
    label: "Calculado",
    icon: Calculator,
    className: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30",
    description: "Resultado determinístico calculado por fórmula ou modelo de engenharia certificado.",
  },
  sample: {
    label: "Dado de Amostra",
    icon: Database,
    className: "bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30",
    description: "Curva ou dataset de referência padrão calibrado — não representa dados reais do poço em campo.",
  },
  simulated: {
    label: "Simulado",
    icon: Cpu,
    className: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/30",
    description: "Saída gerada por solver numérico ou simulação mecanística sob condições de contorno.",
  },
  illustrative: {
    label: "Ilustrativo",
    icon: Eye,
    className: "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/30",
    description: "Representação conceitual / esquemática para visualização didática — não utilizar em projeto de campo.",
  },
};

export function ProvenanceBadge({
  kind,
  source,
  className = "",
  size = "sm",
}: ProvenanceBadgeProps) {
  const meta = CONFIG[kind] || CONFIG.illustrative;
  const Icon = meta.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md border font-medium transition-colors ${meta.className} ${
        size === "sm" ? "text-[11px]" : "text-xs"
      } ${className}`}
      title={`${meta.label}: ${meta.description}${source ? ` (${source})` : ""}`}
    >
      <Icon className={size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5"} />
      <span>{meta.label}</span>
      {source && (
        <>
          <span className="opacity-40">•</span>
          <span className="font-normal opacity-85 truncate max-w-[200px]">{source}</span>
        </>
      )}
    </span>
  );
}

export default ProvenanceBadge;

