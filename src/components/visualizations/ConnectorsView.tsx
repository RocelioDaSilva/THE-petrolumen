import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Workflow, Cpu, Database, Server, AlertCircle } from "lucide-react";
import ProvenanceBadge from "@/components/ui/ProvenanceBadge";

interface Connector {
  id: string;
  name: string;
  category: "simulator" | "data_source" | "cloud";
  status: "not_configured";
  version: string;
  description: string;
}

export default function ConnectorsView() {
  const connectors: Connector[] = [
    {
      id: "eclipse",
      name: "Schlumberger ECLIPSE 100/300",
      category: "simulator",
      status: "not_configured",
      version: "2024.1",
      description: "Interface para exportação de malha .DATA e leitura de vetores .RSM de produção.",
    },
    {
      id: "tnavigator",
      name: "Rock Flow Dynamics tNavigator",
      category: "simulator",
      status: "not_configured",
      version: "23.4",
      description: "Conexão de simulação composicional e acoplamento geomecânico em cluster GPU.",
    },
    {
      id: "cmg",
      name: "CMG STARS / IMEX / GEM",
      category: "simulator",
      status: "not_configured",
      version: "2023.2",
      description: "Módulo de recuperação avançada (EOR), injeção de vapor e modelos térmicos.",
    },
    {
      id: "osdu",
      name: "OSDU Open Subsurface Data Universe",
      category: "cloud",
      status: "not_configured",
      version: "R3-M22",
      description: "Repositório corporativo padronizado de dados geológicos, sísmicos e de poço.",
    },
    {
      id: "petrel",
      name: "Petrel Seismic & Static Integration",
      category: "data_source",
      status: "not_configured",
      version: "2023.3",
      description: "Plugin Ocean API para sincronização bidirecional de horizontes e falhas.",
    },
    {
      id: "postgres",
      name: "PostgreSQL Master Reservoir DB",
      category: "data_source",
      status: "not_configured",
      version: "16.2",
      description: "Armazenamento relacional de tabelas PVT, completação e históricos de vazão.",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Workflow className="w-6 h-6 text-primary" />
              Conectores de Dados e Simuladores Comerciais
            </h2>
            <ProvenanceBadge kind="illustrative" source="Definição de Interfaces Externas" />
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Especificação de integração com simuladores externos (Eclipse, tNavigator, CMG) e repositórios OSDU / Petrel.
          </p>
        </div>
        <Badge variant="outline" className="text-xs px-3 py-1 bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30">
          0 / 6 Configurados (Modo Offline)
        </Badge>
      </div>

      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-3">
        <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Arquitetura Desconectada (Client-Side Standalone):</span>
          <p className="mt-0.5 text-muted-foreground dark:text-amber-300/80">
            O PetroLúmen opera localmente no navegador sem conexões de rede em segundo plano para servidores privados. As integrações com simuladores exigem a inicialização de um serviço de mensageria ou backend dedicado com autenticação de licenças de terceiros.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connectors.map((conn) => (
          <Card key={conn.id} className="shadow-sm">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-muted text-muted-foreground">
                  {conn.category === "simulator" ? (
                    <Cpu className="w-5 h-5" />
                  ) : conn.category === "cloud" ? (
                    <Server className="w-5 h-5" />
                  ) : (
                    <Database className="w-5 h-5" />
                  )}
                </div>
                <div>
                  <CardTitle className="text-sm font-semibold">{conn.name}</CardTitle>
                  <p className="text-[11px] text-muted-foreground">Compatibilidade v{conn.version}</p>
                </div>
              </div>
              <Badge variant="outline" className="text-[10px] bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/30">
                Não Configurado
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <p className="text-xs text-muted-foreground leading-relaxed">
                {conn.description}
              </p>
              <div className="p-2 bg-muted/40 rounded text-[11px] font-mono text-muted-foreground truncate">
                Host: [Não configurado — requer backend API]
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
