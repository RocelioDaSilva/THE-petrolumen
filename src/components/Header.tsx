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
  Check,
  ShieldCheck,
  Settings2,
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
  const { toggleUnitSystem, isMetric } = useUnit();
  const { activeScenario, scenarios, selectScenario, cloneScenario } = useSessionRegistry();

  const [isScenarioDropdownOpen, setIsScenarioDropdownOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleSelectScenario = (id: string) => {
    selectScenario(id);
    setIsScenarioDropdownOpen(false);
  };

  const handleCloneCurrent = (e: React.MouseEvent) => {
    e.stopPropagation();
    cloneScenario(activeScenario.id);
    setIsScenarioDropdownOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/90 backdrop-blur-xl select-none">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 sm:px-6">
        {/* Brand & Active Module Breadcrumb */}
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 text-primary">
            <Microscope className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold tracking-tight text-foreground">
                PetroLúmen
              </h1>
              <Badge variant="outline" className="hidden h-4 border-primary/25 px-1.5 py-0 font-mono text-[9px] text-primary sm:inline-flex">
                ENGINEERING
              </Badge>
            </div>
            <p className="hidden max-w-[320px] truncate text-[11px] font-medium text-muted-foreground md:block">
              {activeModuleTitle}
            </p>
          </div>
        </div>

        {/* Central: Active Scenario / Study Selector (Session Isolation) */}
        <div className="relative hidden min-w-0 sm:block">
          <button
            type="button"
            aria-haspopup="dialog"
            aria-expanded={isScenarioDropdownOpen}
            onClick={() => setIsScenarioDropdownOpen(!isScenarioDropdownOpen)}
            className="flex max-w-[280px] items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-left text-xs transition-colors hover:border-primary/40 hover:bg-accent/50"
            title={t.scenarioIsolated}
          >
            <Layers className="h-4 w-4 shrink-0 text-primary" />
            <div className="min-w-0">
              <div className="text-[9px] font-semibold uppercase leading-none tracking-wider text-muted-foreground">
                {t.activeScenario}
              </div>
              <div className="mt-1 truncate text-xs font-semibold leading-tight text-foreground">
                {activeScenario.name}
              </div>
            </div>
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>

          {/* Scenario Dropdown */}
          {isScenarioDropdownOpen && (
            <>
              <button
                type="button"
                aria-label={isPt ? "Fechar seletor de cenário" : "Close scenario selector"}
                className="fixed inset-0 z-40 cursor-default"
                onClick={() => setIsScenarioDropdownOpen(false)}
              />
              <div role="dialog" aria-label={t.switchScenario} className="absolute left-0 z-50 mt-2 w-72 space-y-1 rounded-xl border border-border bg-popover p-2 shadow-2xl sm:left-auto sm:right-0 sm:w-80">
                <div className="flex items-center justify-between border-b border-border px-2 pb-2 pt-1 text-[11px] font-bold text-muted-foreground">
                  <span>{t.switchScenario}</span>
                  <Badge variant="outline" className="border-primary/30 text-[9px] text-primary">
                    {isPt ? "Estado isolado" : "Isolated state"}
                  </Badge>
                </div>

                <div className="max-h-56 overflow-y-auto space-y-1 py-1">
                  {scenarios.map((scen) => {
                    const isSelected = scen.id === activeScenario.id;
                    return (
                      <button
                        type="button"
                        key={scen.id}
                        onClick={() => handleSelectScenario(scen.id)}
                        className={`flex w-full items-start justify-between rounded-lg p-2 text-left text-xs transition-colors ${
                          isSelected
                            ? "bg-primary/10 font-semibold text-primary"
                            : "text-foreground hover:bg-accent/60"
                        }`}
                      >
                        <div className="space-y-0.5 pr-2 overflow-hidden">
                          <div className="truncate font-medium">{scen.name}</div>
                          <div className="text-[10px] text-muted-foreground truncate">{scen.basin}</div>
                        </div>
                        {isSelected && <Check className="w-4 h-4 text-primary shrink-0 mt-0.5" />}
                      </button>
                    );
                  })}
                </div>

                <div className="flex items-center justify-between gap-2 border-t border-border pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCloneCurrent}
                    className="h-8 w-full gap-1 text-[11px]"
                  >
                    <Copy className="w-3 h-3 text-muted-foreground" />
                    {t.cloneScenario}
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Frequently used actions */}
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={onOpenDocs}
            className="h-9 w-9 border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-primary"
            title={t.docsButton}
            aria-label={t.docsButton}
          >
            <ShieldCheck className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={onToggleTheme}
            className="h-9 w-9 border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground"
            title={t.themeToggle}
            aria-label={t.themeToggle}
          >
            {isDarkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4" />}
          </Button>

          <div className="relative">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsSettingsOpen(!isSettingsOpen)}
              className="h-9 w-9 border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground"
              title={isPt ? "Configurações" : "Settings"}
              aria-label={isPt ? "Configurações" : "Settings"}
              aria-haspopup="dialog"
              aria-expanded={isSettingsOpen}
            >
              <Settings2 className="h-4 w-4" />
            </Button>
            {isSettingsOpen && (
              <>
                <button
                  type="button"
                  aria-label={isPt ? "Fechar configurações" : "Close settings"}
                  className="fixed inset-0 z-40 cursor-default"
                  onClick={() => setIsSettingsOpen(false)}
                />
                <div role="dialog" aria-label={isPt ? "Configurações" : "Settings"} className="absolute right-0 z-50 mt-2 w-64 space-y-2 rounded-xl border border-border bg-popover p-3 shadow-2xl">
                  <div className="border-b border-border px-1 pb-2">
                    <p className="text-xs font-semibold text-foreground">{isPt ? "Preferências" : "Preferences"}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{isPt ? "Unidades e idioma" : "Units and language"}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      toggleUnitSystem();
                      setIsSettingsOpen(false);
                    }}
                    className="h-9 w-full justify-start gap-2 text-xs"
                    title={t.unitToggle}
                  >
                    <Gauge className="h-4 w-4 text-primary" />
                    <span>{isMetric ? t.common.metricUnit : t.common.fieldUnit}</span>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      toggleLocale();
                      setIsSettingsOpen(false);
                    }}
                    className="h-9 w-full justify-start gap-2 text-xs"
                    title={t.langToggle}
                  >
                    <Globe className="h-4 w-4 text-primary" />
                    <span>{locale.toUpperCase()}</span>
                  </Button>
                </div>
              </>
            )}
          </div>

          {/* User Avatar */}
          <div className="hidden items-center gap-2 border-l border-border pl-2 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-xs font-bold text-primary">
              PE
            </div>
            <div className="hidden text-left text-xs leading-none xl:block">
              <p className="font-semibold text-foreground">{t.seniorEngineer}</p>
              <p className="mt-1 text-[10px] text-muted-foreground">{t.roleDescription}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
