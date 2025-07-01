"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle, XCircle, Server, Activity, Brain } from "lucide-react"; // Added more icons for status cards

// Define the status enum to match Rust's ModuleStatusEnum (after serialization)
type ModuleStatusType = "active" | "inactive" | "error";

interface ModuleStatus {
  name: string;
  status: ModuleStatusType; // This will align with the serialized Rust enum
  description: string;
}

export default function DashboardPage() { // Renamed component for clarity
  const [modules, setModules] = useState<ModuleStatus[]>([]);
  const [loading, setLoading] = useState(true);
  // const [tauriVersion, setTauriVersion] = useState<string>(""); // Tauri version can be displayed in Header if needed globally

  useEffect(() => {
    const loadAndInvoke = async () => {
      if (typeof window !== "undefined" && window.__TAURI_IPC__) {
        try {
          const { invoke } = await import('@tauri-apps/api/tauri');

          // Tauri version can be fetched here and passed to a global state/context if needed in Header
          // try {
          //   const version = await invoke('get_version');
          //   // setTauriVersion(version as string); // Example: update global state or context
          // } catch (e) {
          //   console.log('Failed to get Tauri version:', e);
          // }

          console.log("Attempting to invoke get_module_statuses");
          const result = await invoke<ModuleStatus[]>('get_module_statuses');
          console.log("Received from Tauri:", result);
          setModules(result);

        } catch (error) {
          console.error("Failed to interact with Tauri API:", error);
          setModules([
            { name: "Error Initializing Tauri", status: "error", description: "Could not connect or load Tauri API" }
          ]);
        } finally {
          setLoading(false);
        }
      } else {
        console.log('Not running in Tauri or Tauri API not available. Using mock data.');
        setModules([
          { name: "Web: Reservoir Simulation", status: "active", description: "Mock data for web environment" },
          { name: "Web: Production Analysis", status: "inactive", description: "Mock data for web environment" },
          { name: "Web: AI Analytics", status: "error", description: "Mock data for web environment" },
        ]);
        setLoading(false);
      }
    };

    loadAndInvoke();
  }, []);

  const getStatusIcon = (status: ModuleStatusType) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "inactive":
        return <div className="h-4 w-4 rounded-full bg-gray-400 dark:bg-gray-600" />; // Adjusted color for dark mode
      default:
        return <div className="h-4 w-4 rounded-full bg-yellow-400 dark:bg-yellow-600" />;
    }
  };

  const getStatusBadge = (status: ModuleStatusType) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="default" className="bg-green-100 text-green-800 dark:bg-green-700 dark:text-green-100">
            Active
          </Badge>
        );
      case "error":
        return <Badge variant="destructive">Error</Badge>;
      case "inactive":
        return <Badge variant="secondary" className="dark:bg-gray-700 dark:text-gray-300">Inactive</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  return (
    // The main page container. Padding is handled by layout.tsx's <main> tag.
    // Removed min-h-screen and background gradients as they are handled by layout or global styles.
    <div className="space-y-6">
      {/* Page specific title/header - this can be enhanced or made dynamic */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            Dashboard
          </h1>
          <p className="text-muted-foreground">
            Overview of system status and modules.
          </p>
        </div>
        {/* Optional: Add page-specific actions here */}
      </div>

      {/* Status Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sistema Geral</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Operacional</div>
            <p className="text-xs text-muted-foreground">
              Todos os subsistemas funcionando
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Simulações Ativas</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? <Loader2 className="h-6 w-6 animate-spin" /> : modules.filter(m => m.status === 'active').length}
            </div>
            <p className="text-xs text-muted-foreground">
              Módulos atualmente ativos e processando
            </p>
          </CardContent>
        </Card>

        <Card className="shadow-sm hover:shadow-md transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Modelos de IA</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5 / 8</div>
            <p className="text-xs text-muted-foreground">
              Modelos treinados e disponíveis
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Modules Grid */}
      <div>
        <h2 className="text-xl font-semibold text-foreground mb-3">Status dos Módulos</h2>
        {loading ? (
          <div className="col-span-full flex justify-center items-center p-8 bg-card rounded-lg shadow-sm">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Carregando módulos...</span>
          </div>
        ) : modules.length === 0 ? (
           <div className="col-span-full flex justify-center items-center p-8 bg-card rounded-lg shadow-sm">
            <span className="text-muted-foreground">Nenhum módulo encontrado ou falha ao carregar.</span>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {modules.map((module) => (
              <Card key={module.name} className="shadow-sm hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{module.name}</CardTitle>
                    {getStatusBadge(module.status)}
                  </div>
                  <CardDescription>{module.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    {getStatusIcon(module.status)}
                    <span>
                      {module.status === "active" ? "Ativo e operacional" :
                       module.status === "inactive" ? "Inativo no momento" : "Erro detectado"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
