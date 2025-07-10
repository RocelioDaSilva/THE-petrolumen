"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, XCircle, Server, Activity, Brain } from "lucide-react";
import WellDataDemo from "@/app/components/WellDataDemo"; // Import the new component

// Define the status enum to match Rust's ModuleStatusEnum (after serialization)
type ModuleStatusType = "active" | "inactive" | "error";

// More specific type for the module status received from Tauri
interface TauriModuleStatus {
  name: string;
  status: ModuleStatusType;
  description: string;
}

export default function DashboardPage() { // Renamed component for clarity
  const [modules, setModules] = useState<TauriModuleStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null); // Added error state

  const fetchModuleStatuses = async () => {
    setLoading(true);
    setError(null);
    console.log("[Frontend] fetchModuleStatuses: Initiating fetch.");

    if (typeof window !== "undefined" && window.__TAURI_IPC__) {
      console.log("[Frontend] fetchModuleStatuses: Tauri environment detected.");
      try {
        const { invoke } = await import('@tauri-apps/api/core');
        console.log("[Frontend] fetchModuleStatuses: Attempting to invoke 'get_module_statuses'.");
        // Since the backend now returns Result<Vec<TauriModuleStatus>, String>,
        // the type expected from invoke should match this structure if invoke transparently handles Results,
        // or we might need to adjust how we process `e` in catch.
        // For now, assuming invoke still gives direct array on Ok, or throws error which is caught.
        // If `invoke` itself forwards the Rust `Err` content as part of the JS error, `e` might contain it.
        const result = await invoke<TauriModuleStatus[]>('get_module_statuses');
        console.log("[Frontend] fetchModuleStatuses: Successfully received data from Tauri:", result);
        setModules(result);
      } catch (e: any) { // Added ': any' to type 'e' for accessing its properties.
        console.error("[Frontend] fetchModuleStatuses: Failed to interact with Tauri API. Error:", e);
        // Try to extract a more specific message if 'e' is a string or has a message property.
        // TODO: Verify the exact error structure from Tauri invoke for more precise error messages.
        const errorMessage = typeof e === 'string' ? e : (e instanceof Error ? e.message : "Erro desconhecido ao buscar dados dos módulos.");
        setError(`Falha ao carregar dados dos módulos: ${errorMessage} Verifique a conexão com o backend ou tente novamente.`);
        console.warn("[Frontend] fetchModuleStatuses: Setting error state:", errorMessage);
        setModules([]); // Clear modules on error
      } finally {
        setLoading(false);
        console.log("[Frontend] fetchModuleStatuses: Fetch attempt finished.");
      }
    } else {
      console.warn('[Frontend] fetchModuleStatuses: Not running in Tauri or Tauri API not available. Using mock data.');
      // Simulating a delay for mock data loading
      await new Promise(resolve => setTimeout(resolve, 500));
      console.log("[Frontend] fetchModuleStatuses: Mock data timer complete.");
      setModules([
        { name: "Web: Reservoir Simulation", status: "active", description: "Mock data for web environment" },
        { name: "Web: Production Analysis", status: "inactive", description: "Mock data for web environment" },
        { name: "Web: AI Analytics", status: "error", description: "Mock data for web environment" },
      ]);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModuleStatuses();
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
    // Padding for the main page container is handled by layout.tsx's <main> tag.
    <div className="space-y-6">
      {/* Page specific title/header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">
            Dashboard
          </h1>
          <p className="text-muted-foreground">
            Overview of system status and modules.
          </p>
        </div>
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
            {/* // TODO: Replace hardcoded "5 / 8" with dynamic data from backend/store */}
            <div className="text-2xl font-bold">5 / 8</div>
            <p className="text-xs text-muted-foreground">
              Modelos treinados e disponíveis
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Modules Grid */}
      <div aria-live="polite">
        <h2 className="text-xl font-semibold text-foreground mb-3">Status dos Módulos</h2>
        {loading && (
          <div className="col-span-full flex justify-center items-center p-8 bg-card rounded-lg shadow-sm" role="status">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <span className="ml-2 text-muted-foreground">Carregando módulos...</span>
          </div>
        )}
        {!loading && error && (
          <div className="col-span-full flex flex-col justify-center items-center p-8 bg-destructive/10 border border-destructive rounded-lg shadow-sm">
            <XCircle className="w-10 h-10 text-destructive mb-3" />
            <p className="text-destructive font-medium text-center mb-1">{error}</p>
            <p className="text-sm text-muted-foreground text-center mb-4">
              Por favor, verifique sua conexão ou tente novamente mais tarde.
            </p>
            <Button onClick={fetchModuleStatuses} variant="destructive" className="gap-2">
              <Loader2 className={`mr-2 h-4 w-4 ${!loading ? 'hidden' : 'animate-spin'}`} /> {/* Show loader when retrying */}
              Tentar Novamente
            </Button>
          </div>
        )}
        {!loading && !error && modules.length === 0 && (
           <div className="col-span-full flex justify-center items-center p-8 bg-card rounded-lg shadow-sm">
            <span className="text-muted-foreground">Nenhum módulo encontrado.</span>
          </div>
        )}
        {!loading && !error && modules.length > 0 && (
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

      {/* Section for Well Data API Demo */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-foreground mb-3">Demonstração API de Dados de Poços</h2>
        <Card className="shadow-sm">
          <CardContent className="pt-6">
            {/* WellDataDemo component is client-side only, ensure it's correctly imported */}
            {/* TODO: If WellDataDemo is heavy or causes layout shifts, consider Suspense or a loading placeholder. */}
            {typeof window !== "undefined" && <WellDataDemo />}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
