import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { convert, UnitSystem } from "./units";

export interface UnitContextType {
  unitSystem: UnitSystem;
  setUnitSystem: (sys: UnitSystem) => void;
  toggleUnitSystem: () => void;
  isMetric: boolean;
  isField: boolean;
  convertVal: (val: number, from: string, to: string) => number;
  formatPressure: (psi: number) => { value: number; unit: string; display: string };
  formatTemp: (degF: number) => { value: number; unit: string; display: string };
  formatDepth: (ft: number) => { value: number; unit: string; display: string };
  formatRate: (stbd: number) => { value: number; unit: string; display: string };
  formatVolume: (bbl: number) => { value: number; unit: string; display: string };
  formatDensity: (ppg: number) => { value: number; unit: string; display: string };
}

const UnitContext = createContext<UnitContextType | null>(null);

export const UnitProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [unitSystem, setUnitSystemState] = useState<UnitSystem>(() => {
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        const saved = window.localStorage.getItem("petrolumen_unit_system");
        if (saved === "field" || saved === "metric") return saved;
      }
    } catch {
      // ignore
    }
    return "field";
  });

  const setUnitSystem = (sys: UnitSystem) => {
    setUnitSystemState(sys);
    try {
      if (typeof window !== "undefined" && window.localStorage) {
        window.localStorage.setItem("petrolumen_unit_system", sys);
      }
    } catch {
      // ignore
    }
  };

  const toggleUnitSystem = () => {
    setUnitSystem(unitSystem === "field" ? "metric" : "field");
  };

  const isMetric = unitSystem === "metric";
  const isField = unitSystem === "field";

  const convertVal = (val: number, from: string, to: string): number => {
    return convert(val, from, to);
  };

  const formatPressure = (psi: number) => {
    if (isMetric) {
      const bar = Math.round(convert(psi, "psi", "bar") * 10) / 10;
      return { value: bar, unit: "bar", display: `${bar.toLocaleString()} bar` };
    }
    const roundedPsi = Math.round(psi);
    return { value: roundedPsi, unit: "psi", display: `${roundedPsi.toLocaleString()} psi` };
  };

  const formatTemp = (degF: number) => {
    if (isMetric) {
      const c = Math.round(convert(degF, "F", "C") * 10) / 10;
      return { value: c, unit: "°C", display: `${c} °C` };
    }
    const f = Math.round(degF * 10) / 10;
    return { value: f, unit: "°F", display: `${f} °F` };
  };

  const formatDepth = (ft: number) => {
    if (isMetric) {
      const m = Math.round(convert(ft, "ft", "m") * 10) / 10;
      return { value: m, unit: "m", display: `${m.toLocaleString()} m` };
    }
    const roundedFt = Math.round(ft);
    return { value: roundedFt, unit: "ft", display: `${roundedFt.toLocaleString()} ft` };
  };

  const formatRate = (stbd: number) => {
    if (isMetric) {
      const m3d = Math.round(convert(stbd, "STB/d", "m3/d") * 10) / 10;
      return { value: m3d, unit: "m³/d", display: `${m3d.toLocaleString()} m³/d` };
    }
    const roundedStb = Math.round(stbd);
    return { value: roundedStb, unit: "STB/d", display: `${roundedStb.toLocaleString()} STB/d` };
  };

  const formatVolume = (bbl: number) => {
    if (isMetric) {
      const m3 = Math.round(convert(bbl, "bbl", "m3") * 10) / 10;
      return { value: m3, unit: "m³", display: `${m3.toLocaleString()} m³` };
    }
    const roundedBbl = Math.round(bbl * 100) / 100;
    return { value: roundedBbl, unit: "bbl", display: `${roundedBbl.toLocaleString()} bbl` };
  };

  const formatDensity = (ppg: number) => {
    if (isMetric) {
      // 1 ppg ≈ 0.119826 g/cm3 (SG)
      const sg = Math.round((ppg * 0.119826) * 100) / 100;
      return { value: sg, unit: "SG (g/cm³)", display: `${sg} SG` };
    }
    const roundedPpg = Math.round(ppg * 10) / 10;
    return { value: roundedPpg, unit: "ppg", display: `${roundedPpg} ppg` };
  };

  return (
    <UnitContext.Provider
      value={{
        unitSystem,
        setUnitSystem,
        toggleUnitSystem,
        isMetric,
        isField,
        convertVal,
        formatPressure,
        formatTemp,
        formatDepth,
        formatRate,
        formatVolume,
        formatDensity,
      }}
    >
      {children}
    </UnitContext.Provider>
  );
};

export function useUnit(): UnitContextType {
  const context = useContext(UnitContext);
  if (!context) {
    return {
      unitSystem: "field",
      setUnitSystem: () => {},
      toggleUnitSystem: () => {},
      isMetric: false,
      isField: true,
      convertVal: convert,
      formatPressure: (p) => ({ value: p, unit: "psi", display: `${p} psi` }),
      formatTemp: (t) => ({ value: t, unit: "°F", display: `${t} °F` }),
      formatDepth: (d) => ({ value: d, unit: "ft", display: `${d} ft` }),
      formatRate: (r) => ({ value: r, unit: "STB/d", display: `${r} STB/d` }),
      formatVolume: (v) => ({ value: v, unit: "bbl", display: `${v} bbl` }),
      formatDensity: (d) => ({ value: d, unit: "ppg", display: `${d} ppg` }),
    };
  }
  return context;
}
