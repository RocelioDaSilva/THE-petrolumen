import React, { useState, useEffect, useMemo, useCallback, Suspense, lazy } from "react";
import Header from "@/components/Header";
import Sidebar, { APP_MODULES } from "@/components/Sidebar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import ErrorBoundary from "@/components/ErrorBoundary";
import DocumentationModal from "@/components/DocumentationModal";
import LoadingSkeleton from "@/components/ui/LoadingSkeleton";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { UnitProvider } from "@/lib/unitContext";
import { SessionRegistryProvider } from "@/lib/sessionRegistry";
import { getInitialDarkMode } from "@/lib/theme";
import { AuthProvider } from "@/lib/authContext";
import { SavedSimulation } from "@/lib/api";
import ApiErrorToast from "@/components/ApiErrorToast";

// ---------------------------------------------------------------------------
// Code-split ALL heavy view modules via React.lazy so they are only fetched
// on first visit.  This dramatically reduces the JS parsed at cold start.
// Previously 14 components were eagerly imported, loading 300+ KB upfront.
// ---------------------------------------------------------------------------
const DashboardOverview = lazy(() => import("@/components/visualizations/DashboardOverview"));
const ScenarioComparisonView = lazy(() => import("@/components/visualizations/ScenarioComparisonView"));
const WellControlView = lazy(() => import("@/components/visualizations/WellControlView"));
const DrillingHydraulicsView = lazy(() => import("@/components/visualizations/DrillingHydraulicsView"));
const DrillingFluidsView = lazy(() => import("@/components/visualizations/DrillingFluidsView"));
const CementingView = lazy(() => import("@/components/visualizations/CementingView"));
const CasingAndDirectionalView = lazy(() => import("@/components/visualizations/CasingAndDirectionalView"));
const SurfaceFacilitiesView = lazy(() => import("@/components/visualizations/SurfaceFacilitiesView"));
const ReservoirSimulationView = lazy(() => import("@/components/visualizations/ReservoirSimulationView"));
const BlackOilSimulationView = lazy(() => import("@/components/visualizations/BlackOilSimulationView"));
const ReservoirCompressibilityView = lazy(() => import("@/components/visualizations/ReservoirCompressibilityView"));
const ReservoirGrid3D = lazy(() => import("@/components/visualizations/ReservoirGrid3D"));
const DeclineCurveAnalysis = lazy(() => import("@/components/visualizations/DeclineCurveAnalysis"));
const PVTAnalysisWorkflow = lazy(() => import("@/components/visualizations/PVTAnalysisWorkflow"));
const NodalAnalysisView = lazy(() => import("@/components/visualizations/NodalAnalysisView"));
const FlowingMaterialBalanceView = lazy(() => import("@/components/visualizations/FlowingMaterialBalanceView"));
const EconomicsView = lazy(() => import("@/components/visualizations/EconomicsView"));
const ProductionDataImportView = lazy(() => import("@/components/visualizations/ProductionDataImportView"));
const MLDashboardView = lazy(() => import("@/components/visualizations/MLDashboardView"));
const WellDataViewer = lazy(() => import("@/components/visualizations/WellDataViewer"));
const WellTestAnalysisView = lazy(() => import("@/components/visualizations/WellTestAnalysisView"));
const ReservoirOperationsView = lazy(() => import("@/components/visualizations/ReservoirOperationsView"));
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
const THEME_KEY = "petrolumen_theme";

function MainApp() {
  const { t } = useI18n();

  const [activeModule, setActiveModule] = useState<string>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [compactViewport, setCompactViewport] = useState<boolean>(
    () => typeof window !== "undefined" && window.innerWidth <= 1024,
  );
  const [loadedRun, setLoadedRun] = useState<SavedSimulation | null>(null);
  const [comparisonRuns, setComparisonRuns] = useState<
    [SavedSimulation, SavedSimulation] | null
  >(null);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    try {
      return getInitialDarkMode(localStorage.getItem(THEME_KEY));
    } catch {
      return true;
    }
  });
  const [isDocsOpen, setIsDocsOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateCompactViewport = () => setCompactViewport(window.innerWidth <= 1024);
    window.addEventListener("resize", updateCompactViewport);
    return () => window.removeEventListener("resize", updateCompactViewport);
  }, []);

  // Sync dark class on document root
  useEffect(() => {
    try {
      document.documentElement.classList.toggle("dark", isDarkMode);
      document.documentElement.classList.toggle("light", !isDarkMode);
      localStorage.setItem(THEME_KEY, isDarkMode ? "dark" : "light");
    } catch {
      // safe fallback — localStorage may be unavailable in restricted environments
    }
  }, [isDarkMode]);

  const activeModuleMeta = APP_MODULES.find((m) => m.id === activeModule) || APP_MODULES[0];
  const activeCategory = (t.categories as Record<string, string>)[activeModuleMeta.categoryKey] || activeModuleMeta.defaultCategory;
  const handleLoadSavedRun = useCallback((run: SavedSimulation) => {
    if (run.simulation_type !== "reservoir-simulation") return false;
    setLoadedRun(run);
    setActiveModule("reservoir-simulation");
    return true;
  }, []);
  const handleCompareSavedRuns = useCallback(
    (runs: [SavedSimulation, SavedSimulation]) => {
      setComparisonRuns(runs);
      setActiveModule("scenario-comparison");
    },
    [],
  );
  const handleReturnToSavedRuns = useCallback(() => {
    setActiveModule("dashboard");
  }, []);

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
        return wrap(
          <DashboardOverview
            onNavigate={setActiveModule}
            onLoadSavedRun={handleLoadSavedRun}
            onCompareSavedRuns={handleCompareSavedRuns}
          />,
        );
      case "scenario-comparison":
        return wrap(
          <ScenarioComparisonView
            runs={comparisonRuns}
            onReturnToSavedRuns={handleReturnToSavedRuns}
          />,
        );
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
                <TabsTrigger value="black-oil">Black-oil (backend)</TabsTrigger>
              </TabsList>
              <TabsContent value="impes" className="pt-2">
                <ReservoirSimulationView savedRun={loadedRun} />
              </TabsContent>
              <TabsContent value="grid3d" className="pt-2">
                <ReservoirGrid3D />
              </TabsContent>
              <TabsContent value="black-oil" className="pt-2">
                <BlackOilSimulationView />
              </TabsContent>
            </Tabs>
          </div>
        );
      case "reservoir-compressibility":
        return wrap(<ReservoirCompressibilityView />);
      case "production-dca":
        return wrap(<DeclineCurveAnalysis />);
      case "production-data-import":
        return wrap(<ProductionDataImportView />);
      case "pvt":
        return wrap(<PVTAnalysisWorkflow />);
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
      case "well-test-analysis":
        return wrap(<WellTestAnalysisView />);
      case "reservoir-operations":
        return wrap(<ReservoirOperationsView />);
      case "connectors":
        return wrap(<ConnectorsView />);
      default:
        return wrap(
          <DashboardOverview
            onNavigate={setActiveModule}
            onLoadSavedRun={handleLoadSavedRun}
            onCompareSavedRuns={handleCompareSavedRuns}
          />,
        );
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    activeModule,
    t.loadingModule,
    loadedRun,
    comparisonRuns,
    handleLoadSavedRun,
    handleCompareSavedRuns,
    handleReturnToSavedRuns,
  ]);

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      <ApiErrorToast />
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
          collapsed={sidebarCollapsed || compactViewport}
          compact={compactViewport}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main Content View with Error Boundary */}
        <main className="min-w-0 flex-1 overflow-y-auto bg-background p-4 sm:p-5 lg:p-6">
          <div className="mx-auto max-w-[1600px]">
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
      <AuthProvider>
        <UnitProvider>
          <SessionRegistryProvider>
            <MainApp />
          </SessionRegistryProvider>
        </UnitProvider>
      </AuthProvider>
    </I18nProvider>
  );
}
