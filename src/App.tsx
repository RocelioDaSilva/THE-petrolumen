import React, { useState, useEffect, useMemo, Suspense, lazy } from "react";
import Header from "@/components/Header";
import Sidebar, { APP_MODULES } from "@/components/Sidebar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import ErrorBoundary from "@/components/ErrorBoundary";
import DocumentationModal from "@/components/DocumentationModal";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { UnitProvider } from "@/lib/unitContext";
import { SessionRegistryProvider } from "@/lib/sessionRegistry";

// ---------------------------------------------------------------------------
// Code-split ALL heavy view modules via React.lazy so they are only fetched
// on first visit.  This dramatically reduces the JS parsed at cold start.
// Previously 14 components were eagerly imported, loading 300+ KB upfront.
// ---------------------------------------------------------------------------
const DashboardOverview = lazy(() => import("@/components/visualizations/DashboardOverview"));
const WellControlView = lazy(() => import("@/components/visualizations/WellControlView"));
const DrillingHydraulicsView = lazy(() => import("@/components/visualizations/DrillingHydraulicsView"));
const DrillingFluidsView = lazy(() => import("@/components/visualizations/DrillingFluidsView"));
const CementingView = lazy(() => import("@/components/visualizations/CementingView"));
const CasingAndDirectionalView = lazy(() => import("@/components/visualizations/CasingAndDirectionalView"));
const SurfaceFacilitiesView = lazy(() => import("@/components/visualizations/SurfaceFacilitiesView"));
const ReservoirSimulationView = lazy(() => import("@/components/visualizations/ReservoirSimulationView"));
const ReservoirGrid3D = lazy(() => import("@/components/visualizations/ReservoirGrid3D"));
const DeclineCurveAnalysis = lazy(() => import("@/components/visualizations/DeclineCurveAnalysis"));
const PVTCalculator = lazy(() => import("@/components/visualizations/PVTCalculator"));
const NodalAnalysisView = lazy(() => import("@/components/visualizations/NodalAnalysisView"));
const FlowingMaterialBalanceView = lazy(() => import("@/components/visualizations/FlowingMaterialBalanceView"));
const EconomicsView = lazy(() => import("@/components/visualizations/EconomicsView"));
const MLDashboardView = lazy(() => import("@/components/visualizations/MLDashboardView"));
const WellDataViewer = lazy(() => import("@/components/visualizations/WellDataViewer"));
const ConnectorsView = lazy(() => import("@/components/visualizations/ConnectorsView"));
const FieldBasicView = lazy(() => import("@/components/visualizations/FieldBasicView"));
const RigOperationsView = lazy(() => import("@/components/visualizations/RigOperationsView"));
const StuckPipeView = lazy(() => import("@/components/visualizations/StuckPipeView"));
const RigLoadsView = lazy(() => import("@/components/visualizations/RigLoadsView"));
const TonMilesView = lazy(() => import("@/components/visualizations/TonMilesView"));
const TankCapacityView = lazy(() => import("@/components/visualizations/TankCapacityView"));
const AirGasView = lazy(() => import("@/components/visualizations/AirGasView"));
const CompletionsView = lazy(() => import("@/components/visualizations/CompletionsView"));

/** Dark-mode preference localStorage key. */
const DARK_MODE_KEY = "petrolumen_dark_mode";

function MainApp() {
  const { t } = useI18n();

  // Initialise dark mode from persisted user preference
  const [activeModule, setActiveModule] = useState<string>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    try {
      return localStorage.getItem(DARK_MODE_KEY) === "1";
    } catch {
      return false;
    }
  });
  const [isDocsOpen, setIsDocsOpen] = useState<boolean>(false);

  // Sync dark class on document root
  useEffect(() => {
    try {
      if (isDarkMode) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      // Persist preference across page reloads
      localStorage.setItem(DARK_MODE_KEY, isDarkMode ? "1" : "0");
    } catch {
      // safe fallback — localStorage may be unavailable in restricted environments
    }
  }, [isDarkMode]);

  const activeModuleMeta = APP_MODULES.find((m) => m.id === activeModule) || APP_MODULES[0];
  const activeCategory = (t.categories as Record<string, string>)[activeModuleMeta.categoryKey] || activeModuleMeta.defaultCategory;

  /** Shared Suspense loading fallback with skeleton styling. */
  const loadingFallback = <LoadingSkeleton label={t.loadingModule} />;

  /**
   * Resolves the active module JSX.
   * Memoised on `activeModule` so switching modules does not re-instantiate
   * every Suspense boundary on every unrelated render.
   */
  const activeModuleView = useMemo(() => {
    const wrap = (node: React.ReactNode) => (
      <Suspense fallback={loadingFallback}>{node}</Suspense>
    );

    switch (activeModule) {
      case "dashboard":
        return wrap(<DashboardOverview onNavigate={setActiveModule} />);
      case "well-control":
        return wrap(<WellControlView />);
      case "drilling-hydraulics":
        return wrap(<DrillingHydraulicsView />);
      case "drilling-fluids":
        return wrap(<DrillingFluidsView />);
      case "cementing":
        return wrap(<CementingView />);
      case "casing-directional":
        return wrap(<CasingAndDirectionalView />);
      case "field-basic":
        return wrap(<FieldBasicView />);
      case "rig-operations":
        return wrap(<RigOperationsView />);
      case "stuck-pipe":
        return wrap(<StuckPipeView />);
      case "rig-loads":
        return wrap(<RigLoadsView />);
      case "ton-miles":
        return wrap(<TonMilesView />);
      case "tank-capacity":
        return wrap(<TankCapacityView />);
      case "air-gas":
        return wrap(<AirGasView />);
      case "completions":
        return wrap(<CompletionsView />);
      case "surface-facilities":
        return wrap(<SurfaceFacilitiesView />);
      case "reservoir-simulation":
        return wrap(
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
        return wrap(<DeclineCurveAnalysis />);
      case "pvt":
        return wrap(<PVTCalculator />);
      case "nodal":
        return wrap(<NodalAnalysisView />);
      case "rta":
        return wrap(<FlowingMaterialBalanceView />);
      case "economics":
        return wrap(<EconomicsView />);
      case "ai-analytics":
        return wrap(<MLDashboardView />);
      case "well-logs":
        return wrap(<WellDataViewer />);
      case "connectors":
        return wrap(<ConnectorsView />);
      default:
        return wrap(<DashboardOverview onNavigate={setActiveModule} />);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeModule, t.loadingModule]);

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
              retryLabel={t.tryAgain}
              returnLabel={t.returnToDashboard}
              unexpectedFailureMessage={t.unexpectedFailure}
              dataPreservedMessage={t.dataPreserved}
              onReset={() => setActiveModule("dashboard")}
            >
              {activeModuleView}
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
