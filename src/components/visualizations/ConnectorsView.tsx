import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Workflow, CheckCircle, XCircle, RefreshCw, Cpu, Database, Server, GitBranch } from "lucide-react";

interface Connector {
  id: string;
  name: string;
  category: "simulator" | "data_source" | "cloud";
  status: "connected" | "disconnected" | "testing";
  version: string;
  host: string;
}

export default function ConnectorsView() {
  const [connectors, setConnectors] = useState<Connector[]>([
    { id: "eclipse", name: "Schlumberger ECLIPSE 100/300", category: "simulator", status: "connected", version: "2024.1", host: "sim-cluster-01.internal:8090" },
    { id: "tnavigator", name: "Rock Flow Dynamics tNavigator", category: "simulator", status: "connected", version: "23.4", host: "tnav-node-gpu.internal:8080" },
    { id: "cmg", name: "CMG STARS / IMEX / GEM", category: "simulator", status: "connected", version: "2023.2", host: "cmg-license.internal:27000" },
    { id: "osdu", name: "OSDU Open Subsurface Data Universe", category: "cloud", status: "connected", version: "R3-M22", host: "api.osdu.energy.cloud:443" },
    { id: "petrel", name: "Petrel Seismic & Static Integration", category: "data_source", status: "connected", version: "2023.3", host: "ocean-plugin.internal:9000" },
    { id: "postgres", name: "PostgreSQL Master Reservoir DB", category: "data_source", status: "connected", version: "16.2", host: "pg-reservoir.internal:5432" },
  ]);

  const testConnection = (id: string) => {
    setConnectors((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "testing" } : c))
    );
    setTimeout(() => {
      setConnectors((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "connected" } : c))
      );
    }, 600);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Workflow className="w-6 h-6 text-primary" />
            Conectores de Dados e Simuladores Comerciais
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Gerenciamento de interfaces de comunicação com simuladores externos (Eclipse, tNavigator, CMG) e repositórios OSDU / Petrel.
          </p>
        </div>
        <Badge variant="outline" className="text-xs px-3 py-1 bg-emerald-500/10 text-emerald-600 border-emerald-500/30">
          6 Conectores Ativos
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connectors.map((conn) => (
          <Card key={conn.id} className="shadow-sm hover:shadow-md transition">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-primary/10 text-primary">
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
                  <p className="text-[11px] text-muted-foreground">v{conn.version}</p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={`text-[10px] ${
                  conn.status === "connected"
                    ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/30"
                    : conn.status === "testing"
                    ? "bg-amber-500/10 text-amber-600 border-amber-500/30"
                    : "bg-destructive/10 text-destructive border-destructive/30"
                }`}
              >
                {conn.status === "connected" ? "Ativo" : conn.status === "testing" ? "Testando..." : "Desconectado"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3 pt-0">
              <div className="p-2 bg-muted/40 rounded text-[11px] font-mono text-muted-foreground truncate">
                {conn.host}
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-muted-foreground">Latência: ~14 ms</span>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs h-7"
                  disabled={conn.status === "testing"}
                  onClick={() => testConnection(conn.id)}
                >
                  <RefreshCw className={`w-3 h-3 mr-1.5 ${conn.status === "testing" ? "animate-spin" : ""}`} />
                  Testar Ping
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
