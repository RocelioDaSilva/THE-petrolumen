import React, { useState, useEffect } from "react";
import Header from "@/components/Header";
import Sidebar, { APP_MODULES } from "@/components/Sidebar";
import DashboardOverview from "@/components/visualizations/DashboardOverview";
import WellControlView from "@/components/visualizations/WellControlView";
import DrillingHydraulicsView from "@/components/visualizations/DrillingHydraulicsView";
import SurfaceFacilitiesView from "@/components/visualizations/SurfaceFacilitiesView";
import ReservoirSimulationView from "@/components/visualizations/ReservoirSimulationView";
import ReservoirGrid3D from "@/components/visualizations/ReservoirGrid3D";
import DeclineCurveAnalysis from "@/components/visualizations/DeclineCurveAnalysis";
import PVTCalculator from "@/components/visualizations/PVTCalculator";
import NodalAnalysisView from "@/components/visualizations/NodalAnalysisView";
import FlowingMaterialBalanceView from "@/components/visualizations/FlowingMaterialBalanceView";
import EconomicsView from "@/components/visualizations/EconomicsView";
import MLDashboardView from "@/components/visualizations/MLDashboardView";
import WellDataViewer from "@/components/visualizations/WellDataViewer";
import ConnectorsView from "@/components/visualizations/ConnectorsView";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export default function App() {
  const [activeModule, setActiveModule] = useState<string>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  // Sync dark class on document root
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [isDarkMode]);

  const activeModuleMeta = APP_MODULES.find((m) => m.id === activeModule) || APP_MODULES[0];

  const renderActiveModule = () => {
    switch (activeModule) {
      case "dashboard":
        return <DashboardOverview onNavigate={setActiveModule} />;
      case "well-control":
        return <WellControlView />;
      case "drilling-hydraulics":
        return <DrillingHydraulicsView />;
      case "surface-facilities":
        return <SurfaceFacilitiesView />;
      case "reservoir-simulation":
        return (
          <div className="space-y-6">
            <Tabs defaultValue="impes" className="w-full">
              <TabsList className="bg-muted p-1">
                <TabsTrigger value="impes">Modelo Numérico IMPES 1D</TabsTrigger>
                <TabsTrigger value="grid3d">Malha Geocelular 3D Interativa</TabsTrigger>
              </TabsList>
              <TabsContent value="impes" className="pt-2">
                <ReservoirSimulationView />
              </TabsContent>
              <TabsContent value="grid3d" className="pt-2">
                <ReservoirGrid3D />
              </TabsContent>
            </Tabs>
          </div>
        );
      case "production-dca":
        return <DeclineCurveAnalysis />;
      case "pvt":
        return <PVTCalculator />;
      case "nodal":
        return <NodalAnalysisView />;
      case "rta":
        return <FlowingMaterialBalanceView />;
      case "economics":
        return <EconomicsView />;
      case "ai-analytics":
        return <MLDashboardView />;
      case "well-logs":
        return <WellDataViewer />;
      case "connectors":
        return <ConnectorsView />;
      default:
        return <DashboardOverview onNavigate={setActiveModule} />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      {/* Header */}
      <Header
        activeModuleTitle={`${activeModuleMeta.category} • ${activeModuleMeta.name}`}
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode(!isDarkMode)}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          activeModule={activeModule}
          onSelectModule={setActiveModule}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main Content View */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-slate-50/50 dark:bg-slate-950/40">
          <div className="max-w-7xl mx-auto">{renderActiveModule()}</div>
        </main>
      </div>
    </div>
  );
}
