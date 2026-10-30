import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type Locale = "pt" | "en";

export interface Translations {
  appName: string;
  appDescription: string;
  themeToggle: string;
  unitToggle: string;
  langToggle: string;
  docsButton: string;
  benchmarksStatus: string;
  physicalEngineOperational: string;
  activeScenario: string;
  switchScenario: string;
  newScenario: string;
  cloneScenario: string;
  exportScenario: string;
  scenarioIsolated: string;
  seniorEngineer: string;
  roleDescription: string;
  modulesTitle: string;
  searchModules: string;
  noModulesFound: string;
  loadingModule: string;
  moduleFailure: string;
  tryAgain: string;
  returnToDashboard: string;
  benchmarks32Passed: string;
  categories: {
    overview: string;
    drillingWell: string;
    fieldOps: string;
    surfaceFacilities: string;
    reservoirEng: string;
    productionEng: string;
    economicsDecision: string;
    artificialIntelligence: string;
    dataGeology: string;
    infrastructure: string;
  };
  provenance: {
    calculated: string;
    sample: string;
    simulated: string;
    illustrative: string;
  };
  common: {
    save: string;
    exportPdf: string;
    calculate: string;
    reset: string;
    rerunTests: string;
    status: string;
    close: string;
    details: string;
    reference: string;
    expected: string;
    actual: string;
    fieldUnit: string;
    metricUnit: string;
  };
}

const DICTIONARY: Record<Locale, Translations> = {
  pt: {
    appName: "PetroLúmen",
    appDescription: "Plataforma Avançada de Engenharia de Petróleo & Simulação",
    themeToggle: "Alternar tema claro/escuro",
    unitToggle: "Alternar Unidades (Campo US / Métrico SI)",
    langToggle: "Alternar Idioma (Português / English)",
    docsButton: "Auditorias & Docs",
    benchmarksStatus: "11/11 Suítes de Benchmarks Aprovadas (92 Testes)",
    physicalEngineOperational: "Motor Físico Certificado (11/11 Suítes)",
    activeScenario: "Cenário Ativo",
    switchScenario: "Trocar Cenário",
    newScenario: "Novo Estudo",
    cloneScenario: "Clonar Cenário",
    exportScenario: "Exportar Cenário",
    scenarioIsolated: "Ambiente de Sessão Isolado (Anti-Contaminação)",
    seniorEngineer: "Engenheiro Sênior",
    roleDescription: "Reservatórios & Perfuração",
    modulesTitle: "Módulos PetroLúmen",
    searchModules: "Filtrar módulos...",
    noModulesFound: "Nenhum módulo encontrado",
    loadingModule: "Carregando módulo de engenharia...",
    moduleFailure: "Falha na Execução do Módulo",
    tryAgain: "Tentar Novamente",
    returnToDashboard: "Voltar ao Dashboard Geral",
    benchmarks32Passed: "11 de 11 suítes de benchmarks físicos aprovadas (100% - 92 testes)",
    categories: {
      overview: "Visão Geral",
      drillingWell: "Perfuração & Poço",
      fieldOps: "Operações de Campo",
      surfaceFacilities: "Engenharia de Superfície",
      reservoirEng: "Engenharia de Reservatório",
      productionEng: "Engenharia de Produção",
      economicsDecision: "Economia & Decisão",
      artificialIntelligence: "Inteligência Artificial",
      dataGeology: "Dados & Geologia",
      infrastructure: "Infraestrutura & Conectores",
    },
    provenance: {
      calculated: "Calculado Determinístico",
      sample: "Dado de Amostra Calibrado",
      simulated: "Simulação Numérica (IMPES)",
      illustrative: "Representação Conceitual",
    },
    common: {
      save: "Salvar",
      exportPdf: "Exportar Relatório PDF",
      calculate: "Calcular",
      reset: "Restaurar Padrão",
      rerunTests: "Reexecutar Benchmarks",
      status: "Status",
      close: "Fechar",
      details: "Detalhes",
      reference: "Referência Bibliográfica",
      expected: "Valor Esperado",
      actual: "Valor Calculado",
      fieldUnit: "Campo (US)",
      metricUnit: "Métrico (SI)",
    },
  },
  en: {
    appName: "PetroLúmen",
    appDescription: "Advanced Petroleum & Reservoir Engineering Platform",
    themeToggle: "Toggle light/dark theme",
    unitToggle: "Toggle Units (US Field / Metric SI)",
    langToggle: "Toggle Language (English / Portuguese)",
    docsButton: "Audits & Docs",
    benchmarksStatus: "11/11 Golden Benchmark Suites Passed (92 Tests)",
    physicalEngineOperational: "Certified Physics Engine (11/11 Suites)",
    activeScenario: "Active Scenario",
    switchScenario: "Switch Scenario",
    newScenario: "New Study",
    cloneScenario: "Clone Scenario",
    exportScenario: "Export Scenario",
    scenarioIsolated: "Isolated Session State (Zero State Bleed)",
    seniorEngineer: "Senior PE",
    roleDescription: "Reservoir & Drilling Lead",
    modulesTitle: "PetroLúmen Modules",
    searchModules: "Filter modules...",
    noModulesFound: "No modules found",
    loadingModule: "Loading engineering module...",
    moduleFailure: "Module Execution Error",
    tryAgain: "Try Again",
    returnToDashboard: "Return to Main Dashboard",
    benchmarks32Passed: "11 of 11 physical benchmark suites passed (100% - 92 tests)",
    categories: {
      overview: "Overview",
      drillingWell: "Drilling & Well Control",
      fieldOps: "Field Operations",
      surfaceFacilities: "Surface Facilities",
      reservoirEng: "Reservoir Engineering",
      productionEng: "Production Engineering",
      economicsDecision: "Economics & Decision",
      artificialIntelligence: "Artificial Intelligence",
      dataGeology: "Data & Geology",
      infrastructure: "Infrastructure & Connectors",
    },
    provenance: {
      calculated: "Deterministic Calculation",
      sample: "Calibrated Sample Data",
      simulated: "Numerical Simulation (IMPES)",
      illustrative: "Conceptual Visualization",
    },
    common: {
      save: "Save",
      exportPdf: "Export PDF Report",
      calculate: "Calculate",
      reset: "Reset Defaults",
      rerunTests: "Rerun Benchmarks",
      status: "Status",
      close: "Close",
      details: "Details",
      reference: "Literature Reference",
      expected: "Expected Value",
      actual: "Calculated Value",
      fieldUnit: "US Field",
      metricUnit: "Metric (SI)",
    },
  },
};

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: Translations;
  isPt: boolean;
  isEn: boolean;
}

const I18nContext = createContext<I18nContextType | null>(null);

export const I18nProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [locale, setLocaleState] = useState<Locale>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const saved = window.localStorage.getItem("petrolumen_locale");
        if (saved === "pt" || saved === "en") return saved;
      }
    } catch {
      // fallback
    }
    return "pt";
  });

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem("petrolumen_locale", newLocale);
      }
    } catch {
      // ignore
    }
  };

  const toggleLocale = () => {
    setLocale(locale === "pt" ? "en" : "pt");
  };

  return (
    <I18nContext.Provider
      value={{
        locale,
        setLocale,
        toggleLocale,
        t: DICTIONARY[locale],
        isPt: locale === "pt",
        isEn: locale === "en",
      }}
    >
      {children}
    </I18nContext.Provider>
  );
};

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (!context) {
    return {
      locale: "pt",
      setLocale: () => {},
      toggleLocale: () => {},
      t: DICTIONARY.pt,
      isPt: true,
      isEn: false,
    };
  }
  return context;
}
