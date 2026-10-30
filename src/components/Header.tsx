import React, { useState } from "react";
import {
  Microscope,
  Moon,
  Sun,
  BookOpen,
  Globe,
  Gauge,
  Layers,
  ChevronDown,
  Copy,
  Plus,
  Check,
  ShieldCheck,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/lib/i18n";
import { useUnit } from "@/lib/unitContext";
import { useSessionRegistry } from "@/lib/sessionRegistry";

interface HeaderProps {
  activeModuleTitle: string;
  isDarkMode: boolean;
  onToggleTheme: () => void;
  onOpenDocs: () => void;
}

export default function Header({
  activeModuleTitle,
  isDarkMode,
  onToggleTheme,
  onOpenDocs,
}: HeaderProps) {
  const { t, locale, toggleLocale, isPt } = useI18n();
  const { unitSystem, toggleUnitSystem, isMetric } = useUnit();
  const { activeScenario, scenarios, selectScenario, cloneScenario } = useSessionRegistry();

  const [isScenarioDropdownOpen, setIsScenarioDropdownOpen] = useState(false);

  const handleSelectScenario = (id: string) => {
    selectScenario(id);
    setIsScenarioDropdownOpen(false);
  };

  const handleCloneCurrent = (e: React.MouseEvent) => {
    e.stopPropagation();
    const cloned = cloneScenario(activeScenario.id);
    setIsScenarioDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 bg-card/95 backdrop-blur-md border-b border-border shadow-xs select-none">
      <div className="flex items-center justify-between px-4 sm:px-6 py-2.5 gap-2">
        {/* Brand & Active Module Breadcrumb */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-sm shadow-blue-500/20">
            <Microscope className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                PetroLúmen
              </h1>
              <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 font-mono text-muted-foreground border-border hidden sm:inline-flex">
                v1.1 Certified
              </Badge>
            </div>
            <p className="text-[11px] text-muted-foreground font-medium truncate max-w-[220px] sm:max-w-xs md:max-w-md hidden md:block">
              {activeModuleTitle}
            </p>
          </div>
        </div>

        {/* Central: Active Scenario / Study Selector (Session Isolation) */}
        <div className="relative">
          <div
            onClick={() => setIsScenarioDropdownOpen(!isScenarioDropdownOpen)}
            className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg border border-border/80 bg-muted/40 hover:bg-muted/70 transition-colors cursor-pointer text-xs"
            title={t.scenarioIsolated}
          >
            <Layers className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            <div className="text-left hidden sm:block">
              <div className="text-[9px] uppercase tracking-wider text-muted-foreground font-semibold leading-none">
                {t.activeScenario}
              </div>
              <div className="font-semibold text-foreground text-xs leading-tight truncate max-w-[150px] md:max-w-[200px]">
                {activeScenario.name}
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          </div>

          {/* Scenario Dropdown */}
          {isScenarioDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setIsScenarioDropdownOpen(false)}
              />
              <div className="absolute left-0 sm:left-auto sm:right-0 mt-1.5 w-72 sm:w-80 rounded-xl bg-card border border-border shadow-xl z-50 p-2 space-y-1 animate-in fade-in zoom-in-95 duration-100">
                <div className="flex items-center justify-between px-2 py-1 text-[11px] font-bold text-muted-foreground border-b border-border pb-1.5">
                  <span>{t.switchScenario}</span>
                  <Badge variant="outline" className="text-[9px] text-indigo-500 border-indigo-500/30">
                    State Isolated
                  </Badge>
                </div>

                <div className="max-h-56 overflow-y-auto space-y-1 py-1">
                  {scenarios.map((scen) => {
                    const isSelected = scen.id === activeScenario.id;
                    return (
                      <div
                        key={scen.id}
                        onClick={() => handleSelectScenario(scen.id)}
                        className={`flex items-start justify-between p-2 rounded-lg cursor-pointer text-xs transition-colors ${
                          isSelected
                            ? "bg-primary/10 text-primary font-semibold"
                            : "hover:bg-muted/60 text-foreground"
                        }`}
                      >
                        <div className="space-y-0.5 pr-2 overflow-hidden">
                          <div className="truncate font-medium">{scen.name}</div>
                          <div className="text-[10px] text-muted-foreground truncate">{scen.basin}</div>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />}
                      </div>
                    );
                  })}
                </div>

                <div className="pt-1.5 border-t border-border flex items-center justify-between gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCloneCurrent}
                    className="w-full text-[11px] h-7 gap-1"
                  >
                    <Copy className="w-3 h-3 text-muted-foreground" />
                    {t.cloneScenario}
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Right Actions: Units, Language, Audits, Theme, User */}
        <div className="flex items-center space-x-1 sm:space-x-2 shrink-0">
          {/* Unit System Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleUnitSystem}
            className="h-8 px-2 sm:px-2.5 text-xs font-semibold gap-1.5 border-border bg-background"
            title={t.unitToggle}
          >
            <Gauge className="w-3.5 h-3.5 text-blue-500" />
            <span className="hidden sm:inline">
              {isMetric ? t.common.metricUnit : t.common.fieldUnit}
            </span>
            <span className="sm:hidden font-mono text-[11px]">
              {isMetric ? "SI" : "US"}
            </span>
          </Button>

          {/* Language Toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={toggleLocale}
            className="h-8 px-2 text-xs font-semibold gap-1 border-border bg-background"
            title={t.langToggle}
          >
            <Globe className="w-3.5 h-3.5 text-emerald-500" />
            <span className="font-mono text-[11px]">{locale.toUpperCase()}</span>
          </Button>

          {/* Docs & Audit Center Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenDocs}
            className="h-8 px-2 sm:px-2.5 text-xs font-semibold gap-1.5 border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20"
            title="Abrir Central de Auditorias e Benchmarks"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span className="hidden md:inline">{t.docsButton}</span>
            <span className="text-[10px] font-mono bg-emerald-500/20 px-1 rounded hidden sm:inline">
              32/32
            </span>
          </Button>

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleTheme}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
            title={t.themeToggle}
          >
            {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* User Avatar */}
          <div className="flex items-center space-x-2 pl-1 sm:pl-2 border-l border-border">
            <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold">
              PE
            </div>
            <div className="hidden xl:block text-left text-xs leading-none">
              <p className="font-semibold text-foreground">{t.seniorEngineer}</p>
              <p className="text-[10px] text-muted-foreground">{t.roleDescription}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
