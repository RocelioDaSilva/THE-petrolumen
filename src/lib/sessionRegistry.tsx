import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export interface ScenarioParameters {
  // Well & Drilling
  wellDepthFt: number;
  casingShoeDepthFt: number;
  casingIdInches: number;
  drillPipeOdInches: number;
  drillPipeIdInches: number;
  currentMudWeightPpg: number;
  sidppPsi: number;
  sicpPsi: number;
  pitGainBbl: number;

  // Reservoir & PVT
  reservoirPressurePsia: number;
  reservoirTempF: number;
  gasSpecificGravity: number;
  oilApiGravity: number;
  solutionGorScfStb: number;
  permeabilityMd: number;
  porosityFraction: number;
  waterCutFraction: number;

  // Economics & DCA
  oilPriceUsd: number;
  capexUsd: number;
  opexUsdPerBbl: number;
  discountRatePercent: number;
  initialRateStbd: number;
  nominalDeclineRate: number;
  arpsBFactor: number;
}

export interface EngineeringScenario {
  id: string;
  name: string;
  field: string;
  basin: string;
  description: string;
  isCustom?: boolean;
  createdAt: string;
  lastModified: string;
  parameters: ScenarioParameters;
}

export const BASELINE_SCENARIOS: EngineeringScenario[] = [
  {
    id: "scen-volve-baseline",
    name: "Campo de Volve - Poço 15/9-F-12",
    field: "Volve",
    basin: "Mar do Norte (Arenito Hugin)",
    description: "Poço de desenvolvimento em arenito jurássico. Alta permeabilidade e bom suporte hidrostático.",
    isCustom: false,
    createdAt: "2024-03-15",
    lastModified: "2024-10-28",
    parameters: {
      wellDepthFt: 10500,
      casingShoeDepthFt: 8500,
      casingIdInches: 8.681,
      drillPipeOdInches: 5.0,
      drillPipeIdInches: 4.276,
      currentMudWeightPpg: 10.5,
      sidppPsi: 450,
      sicpPsi: 650,
      pitGainBbl: 15.0,
      reservoirPressurePsia: 3250,
      reservoirTempF: 195,
      gasSpecificGravity: 0.72,
      oilApiGravity: 35.0,
      solutionGorScfStb: 620,
      permeabilityMd: 85,
      porosityFraction: 0.22,
      waterCutFraction: 0.18,
      oilPriceUsd: 75,
      capexUsd: 2500000,
      opexUsdPerBbl: 18,
      discountRatePercent: 10,
      initialRateStbd: 1200,
      nominalDeclineRate: 0.08,
      arpsBFactor: 0.65,
    },
  },
  {
    id: "scen-santos-presal",
    name: "Bacia de Santos - Pré-Sal 7-SP-04",
    field: "Búzios / Tupi",
    basin: "Bacia de Santos (Carbonatos Barra Velha)",
    description: "Poço marítimo ultra-profundo com lâmina d'água de 2.100m. Carbonatos microbialíticos com alto CO2.",
    isCustom: false,
    createdAt: "2024-05-10",
    lastModified: "2024-10-29",
    parameters: {
      wellDepthFt: 18200,
      casingShoeDepthFt: 14500,
      casingIdInches: 9.625,
      drillPipeOdInches: 5.5,
      drillPipeIdInches: 4.778,
      currentMudWeightPpg: 12.2,
      sidppPsi: 720,
      sicpPsi: 980,
      pitGainBbl: 22.0,
      reservoirPressurePsia: 7400,
      reservoirTempF: 240,
      gasSpecificGravity: 0.82,
      oilApiGravity: 28.5,
      solutionGorScfStb: 1100,
      permeabilityMd: 45,
      porosityFraction: 0.16,
      waterCutFraction: 0.08,
      oilPriceUsd: 75,
      capexUsd: 8500000,
      opexUsdPerBbl: 12,
      discountRatePercent: 12,
      initialRateStbd: 4500,
      nominalDeclineRate: 0.05,
      arpsBFactor: 0.45,
    },
  },
  {
    id: "scen-permian-shale",
    name: "Permian Wolfcamp HZ-108",
    field: "Wolfcamp Shale",
    basin: "Delaware Basin, Texas/NM",
    description: "Poço horizontal não convencional com fraturamento multifásico e comportamento Duong/hiperbólico b > 1.",
    isCustom: false,
    createdAt: "2024-06-20",
    lastModified: "2024-10-29",
    parameters: {
      wellDepthFt: 16500,
      casingShoeDepthFt: 9200,
      casingIdInches: 7.0,
      drillPipeOdInches: 4.5,
      drillPipeIdInches: 3.826,
      currentMudWeightPpg: 11.0,
      sidppPsi: 380,
      sicpPsi: 510,
      pitGainBbl: 12.0,
      reservoirPressurePsia: 4800,
      reservoirTempF: 165,
      gasSpecificGravity: 0.68,
      oilApiGravity: 42.0,
      solutionGorScfStb: 850,
      permeabilityMd: 0.005,
      porosityFraction: 0.09,
      waterCutFraction: 0.35,
      oilPriceUsd: 75,
      capexUsd: 6200000,
      opexUsdPerBbl: 22,
      discountRatePercent: 10,
      initialRateStbd: 1800,
      nominalDeclineRate: 0.18,
      arpsBFactor: 1.15, // b > 1 supported per ENG-28
    },
  },
];

interface SessionRegistryContextType {
  activeScenario: EngineeringScenario;
  scenarios: EngineeringScenario[];
  selectScenario: (id: string) => void;
  createScenario: (name: string, basin?: string) => EngineeringScenario;
  cloneScenario: (id: string, newName?: string) => EngineeringScenario;
  updateActiveParameters: (params: Partial<ScenarioParameters>) => void;
  deleteScenario: (id: string) => boolean;
  exportScenarioJson: () => string;
}

const SessionRegistryContext = createContext<SessionRegistryContextType | null>(null);

const STORAGE_KEY = "petrolumen_saved_scenarios";
const ACTIVE_ID_KEY = "petrolumen_active_scenario_id";

export const SessionRegistryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [scenarios, setScenarios] = useState<EngineeringScenario[]>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const saved = window.localStorage.getItem(STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          if (Array.isArray(parsed) && parsed.length > 0) {
            return parsed;
          }
        }
      }
    } catch {
      // fallback
    }
    return BASELINE_SCENARIOS;
  });

  const [activeId, setActiveId] = useState<string>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const savedId = window.localStorage.getItem(ACTIVE_ID_KEY);
        if (savedId) return savedId;
      }
    } catch {
      // fallback
    }
    return BASELINE_SCENARIOS[0].id;
  });

  // Sync state to local storage safely
  useEffect(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(scenarios));
        window.localStorage.setItem(ACTIVE_ID_KEY, activeId);
      }
    } catch {
      // ignore
    }
  }, [scenarios, activeId]);

  const activeScenario =
    scenarios.find((s) => s.id === activeId) || scenarios[0] || BASELINE_SCENARIOS[0];

  const selectScenario = (id: string) => {
    const target = scenarios.find((s) => s.id === id);
    if (target) {
      setActiveId(id);
    }
  };

  const createScenario = (name: string, basin: string = "Nova Bacia"): EngineeringScenario => {
    const newId = `scen-custom-${Date.now()}`;
    const newScen: EngineeringScenario = {
      id: newId,
      name,
      field: name,
      basin,
      description: "Estudo de engenharia personalizado criado nesta sessão.",
      isCustom: true,
      createdAt: new Date().toISOString().split("T")[0],
      lastModified: new Date().toISOString().split("T")[0],
      parameters: { ...activeScenario.parameters },
    };
    setScenarios((prev) => [...prev, newScen]);
    setActiveId(newId);
    return newScen;
  };

  const cloneScenario = (id: string, newName?: string): EngineeringScenario => {
    const src = scenarios.find((s) => s.id === id) || activeScenario;
    const cloneId = `scen-clone-${Date.now()}`;
    const cloned: EngineeringScenario = {
      id: cloneId,
      name: newName || `${src.name} (Cópia / Sensibilidade)`,
      field: src.field,
      basin: src.basin,
      description: `Cenário derivado de ${src.name} para análise de sensibilidade e isolamento de estado.`,
      isCustom: true,
      createdAt: new Date().toISOString().split("T")[0],
      lastModified: new Date().toISOString().split("T")[0],
      parameters: { ...src.parameters },
    };
    setScenarios((prev) => [...prev, cloned]);
    setActiveId(cloneId);
    return cloned;
  };

  const updateActiveParameters = (params: Partial<ScenarioParameters>) => {
    setScenarios((prev) =>
      prev.map((s) =>
        s.id === activeId
          ? {
              ...s,
              lastModified: new Date().toISOString().split("T")[0],
              parameters: { ...s.parameters, ...params },
            }
          : s
      )
    );
  };

  const deleteScenario = (id: string): boolean => {
    const target = scenarios.find((s) => s.id === id);
    if (!target || !target.isCustom) {
      return false; // protect baseline scenarios
    }
    const filtered = scenarios.filter((s) => s.id !== id);
    setScenarios(filtered);
    if (activeId === id) {
      setActiveId(filtered[0]?.id || BASELINE_SCENARIOS[0].id);
    }
    return true;
  };

  const exportScenarioJson = (): string => {
    return JSON.stringify(activeScenario, null, 2);
  };

  return (
    <SessionRegistryContext.Provider
      value={{
        activeScenario,
        scenarios,
        selectScenario,
        createScenario,
        cloneScenario,
        updateActiveParameters,
        deleteScenario,
        exportScenarioJson,
      }}
    >
      {children}
    </SessionRegistryContext.Provider>
  );
};

export function useSessionRegistry(): SessionRegistryContextType {
  const context = useContext(SessionRegistryContext);
  if (!context) {
    throw new Error(
      "useSessionRegistry must be called inside a <SessionRegistryProvider>. Ensure the provider wraps your component tree (see App.tsx)."
    );
  }
  return context;
}
