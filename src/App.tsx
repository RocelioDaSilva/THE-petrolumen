import React, { useState, useEffect, Suspense, lazy } from "react";
import Header from "@/components/Header";
import Sidebar, { APP_MODULES } from "@/components/Sidebar";
import DashboardOverview from "@/components/visualizations/DashboardOverview";
import WellControlView from "@/components/visualizations/WellControlView";
import DrillingHydraulicsView from "@/components/visualizations/DrillingHydraulicsView";
import DrillingFluidsView from "@/components/visualizations/DrillingFluidsView";
import CementingView from "@/components/visualizations/CementingView";
import CasingAndDirectionalView from "@/components/visualizations/CasingAndDirectionalView";
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
import ErrorBoundary from "@/components/ErrorBoundary";
import DocumentationModal from "@/components/DocumentationModal";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { UnitProvider } from "@/lib/unitContext";
import { SessionRegistryProvider } from "@/lib/sessionRegistry";

const FieldBasicView = lazy(() => import("@/components/visualizations/FieldBasicView"));
const RigOperationsView = lazy(() => import("@/components/visualizations/RigOperationsView"));
const StuckPipeView = lazy(() => import("@/components/visualizations/StuckPipeView"));
const RigLoadsView = lazy(() => import("@/components/visualizations/RigLoadsView"));
const TonMilesView = lazy(() => import("@/components/visualizations/TonMilesView"));
const TankCapacityView = lazy(() => import("@/components/visualizations/TankCapacityView"));
const AirGasView = lazy(() => import("@/components/visualizations/AirGasView"));
const CompletionsView = lazy(() => import("@/components/visualizations/CompletionsView"));

function MainApp() {
  const { t } = useI18n();
  const [activeModule, setActiveModule] = useState<string>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);
  const [isDocsOpen, setIsDocsOpen] = useState<boolean>(false);

  // Sync dark class on document root
  useEffect(() => {
    try {
      if (isDarkMode) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    } catch {
      // safe fallback
    }
  }, [isDarkMode]);

  const activeModuleMeta = APP_MODULES.find((m) => m.id === activeModule) || APP_MODULES[0];
  const activeCategory = (t.categories as Record<string, string>)[activeModuleMeta.categoryKey] || activeModuleMeta.defaultCategory;

  const renderActiveModule = () => {
    switch (activeModule) {
      case "dashboard":
        return <DashboardOverview onNavigate={setActiveModule} />;
      case "well-control":
        return <WellControlView />;
      case "drilling-hydraulics":
        return <DrillingHydraulicsView />;
      case "drilling-fluids":
        return <DrillingFluidsView />;
      case "cementing":
        return <CementingView />;
      case "casing-directional":
        return <CasingAndDirectionalView />;
      case "field-basic":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <FieldBasicView />
          </Suspense>
        );
      case "rig-operations":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <RigOperationsView />
          </Suspense>
        );
      case "stuck-pipe":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <StuckPipeView />
          </Suspense>
        );
      case "rig-loads":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <RigLoadsView />
          </Suspense>
        );
      case "ton-miles":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <TonMilesView />
          </Suspense>
        );
      case "tank-capacity":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <TankCapacityView />
          </Suspense>
        );
      case "air-gas":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <AirGasView />
          </Suspense>
        );
      case "completions":
        return (
          <Suspense fallback={<div className="p-6 text-xs text-muted-foreground">{t.loadingModule}</div>}>
            <CompletionsView />
          </Suspense>
        );
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
      {/* Enhanced Header with i18n, Units, Scenario Selector, and Audits */}
      <Header
        activeModuleTitle={`${activeCategory} • ${activeModuleMeta.defaultName}`}
        isDarkMode={isDarkMode}
        onToggleTheme={() => setIsDarkMode(!isDarkMode)}
        onOpenDocs={() => setIsDocsOpen(true)}
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar with search and i18n */}
        <Sidebar
          activeModule={activeModule}
          onSelectModule={setActiveModule}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          onOpenDocs={() => setIsDocsOpen(true)}
        />

        {/* Main Content View with Error Boundary */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 bg-slate-50/50 dark:bg-slate-950/40">
          <div className="max-w-7xl mx-auto">
            <ErrorBoundary
              key={activeModule}
              fallbackTitle={`${t.moduleFailure}: ${activeModuleMeta.defaultName}`}
              onReset={() => setActiveModule("dashboard")}
            >
              {renderActiveModule()}
            </ErrorBoundary>
          </div>
        </main>
      </div>

      {/* Technical Audits & Documentation Modal */}
      <DocumentationModal isOpen={isDocsOpen} onClose={() => setIsDocsOpen(false)} />
    </div>
  );
}

export default function App() {
  return (
    <I18nProvider>
      <UnitProvider>
        <SessionRegistryProvider>
          <MainApp />
        </SessionRegistryProvider>
      </UnitProvider>
    </I18nProvider>
  );
}
