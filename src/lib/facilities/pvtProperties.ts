/**
 * Fluid Properties and PVT Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 3: Basic Principles & Chapter 8: Crude Stabilization
 */

export interface Component {
  name: string;
  formula: string;
  mw: number;
  tcR: number; // Critical Temperature (°R)
  pcPsia: number; // Critical Pressure (psia)
  acentricFactor?: number;
}

// Table 3-5 and Table 3-8: Physical Properties of Pure Components
export const PURE_COMPONENTS: Record<string, Component> = {
  CO2: { name: "Carbon Dioxide", formula: "CO2", mw: 44.01, tcR: 547.5, pcPsia: 1070.2, acentricFactor: 0.224 },
  H2S: { name: "Hydrogen Sulfide", formula: "H2S", mw: 34.08, tcR: 672.4, pcPsia: 1306.5, acentricFactor: 0.094 },
  N2: { name: "Nitrogen", formula: "N2", mw: 28.01, tcR: 227.0, pcPsia: 492.2, acentricFactor: 0.037 },
  C1: { name: "Methane", formula: "CH4", mw: 16.04, tcR: 343.2, pcPsia: 673.1, acentricFactor: 0.011 },
  C2: { name: "Ethane", formula: "C2H6", mw: 30.07, tcR: 549.9, pcPsia: 708.3, acentricFactor: 0.099 },
  C3: { name: "Propane", formula: "C3H8", mw: 44.10, tcR: 666.0, pcPsia: 617.4, acentricFactor: 0.152 },
  iC4: { name: "i-Butane", formula: "C4H10", mw: 58.12, tcR: 734.6, pcPsia: 529.1, acentricFactor: 0.183 },
  nC4: { name: "n-Butane", formula: "C4H10", mw: 58.12, tcR: 765.7, pcPsia: 550.1, acentricFactor: 0.200 },
  iC5: { name: "i-Pentane", formula: "C5H12", mw: 72.15, tcR: 829.6, pcPsia: 483.5, acentricFactor: 0.227 },
  nC5: { name: "n-Pentane", formula: "C5H12", mw: 72.15, tcR: 846.2, pcPsia: 489.8, acentricFactor: 0.252 },
  C6: { name: "Hexane", formula: "C6H14", mw: 86.18, tcR: 914.2, pcPsia: 440.1, acentricFactor: 0.301 },
  C7plus: { name: "Heptanes Plus", formula: "C7+", mw: 142.3, tcR: 1050.0, pcPsia: 380.0, acentricFactor: 0.400 },
};

/**
 * Eq. 3-5: Apparent Molecular Weight of a Gas Mixture
 * MW_g = sum(y_i * MW_i)
 */
export function apparentMolecularWeight(composition: { moleFraction: number; mw: number }[]): number {
  const sum = composition.reduce((acc, c) => acc + c.moleFraction * c.mw, 0);
  return Math.round(sum * 100) / 100;
}

/**
 * Eq. 3-7: Gas Specific Gravity relative to air (MW_air = 28.966 or 29 in book)
 */
export function gasSpecificGravity(mwGas: number, mwAir: number = 29): number {
  return Math.round((mwGas / mwAir) * 1000) / 1000;
}

/**
 * Eq. 3-8: Gas Density at P and T
 * rho_g = 2.70 * S * P / (T * Z)  [lb/ft3]
 * where P is in psia, T is in °R, S is gas specific gravity (air=1.0)
 */
export function gasDensity(sg: number, pPsia: number, tRankine: number, z: number): number {
  if (tRankine <= 0 || z <= 0) return 0;
  const rho = (2.70 * sg * pPsia) / (tRankine * z);
  return Math.round(rho * 100) / 100;
}

/**
 * Eq. 3-9: Gas Density from Molecular Weight
 * rho_g = 0.093 * MW * P / (T * Z)
 */
export function gasDensityFromMW(mw: number, pPsia: number, tRankine: number, z: number): number {
  if (tRankine <= 0 || z <= 0) return 0;
  const rho = (0.093 * mw * pPsia) / (tRankine * z);
  return Math.round(rho * 100) / 100;
}

/**
 * Eqs. 3-18 and 3-19: Pseudo-Critical Temperature & Pressure
 */
export function pseudoCriticalProperties(composition: { moleFraction: number; tcR: number; pcPsia: number }[]): {
  tpcR: number;
  ppcPsia: number;
} {
  let tpc = 0;
  let ppc = 0;
  let totalMoles = 0;
  for (const c of composition) {
    tpc += c.moleFraction * c.tcR;
    ppc += c.moleFraction * c.pcPsia;
    totalMoles += c.moleFraction;
  }
  if (totalMoles > 0) {
    tpc /= totalMoles;
    ppc /= totalMoles;
  }
  return {
    tpcR: Math.round(tpc * 10) / 10,
    ppcPsia: Math.round(ppc * 10) / 10,
  };
}

/**
 * Eqs. 3-22 & 3-23: Wichert and Aziz Correction for Sour Gases (H2S and CO2)
 * A = y_H2S + y_CO2
 * B = y_H2S
 * epsilon = 120 * (A^0.9 - A^1.6) + 15 * (B^0.5 - B^4)
 * T''pc = T'pc - epsilon
 * P''pc = (P'pc * T''pc) / [T'pc + B * (1 - B) * epsilon]
 */
export function wichertAzizCorrection(
  tpcR: number,
  ppcPsia: number,
  yH2S: number,
  yCO2: number
): {
  epsilon: number;
  tpcAdjustedR: number;
  ppcAdjustedPsia: number;
} {
  const A = Math.max(0, yH2S + yCO2);
  const B = Math.max(0, yH2S);

  if (A === 0) {
    return { epsilon: 0, tpcAdjustedR: tpcR, ppcAdjustedPsia: ppcPsia };
  }

  const epsilon = 120 * (Math.pow(A, 0.9) - Math.pow(A, 1.6)) + 15 * (Math.pow(B, 0.5) - Math.pow(B, 4.0));
  const tpcAdj = tpcR - epsilon;
  const denom = tpcR + B * (1 - B) * epsilon;
  const ppcAdj = (ppcPsia * tpcAdj) / Math.max(1, denom);

  return {
    epsilon: Math.round(epsilon * 10) / 10,
    tpcAdjustedR: Math.round(tpcAdj * 10) / 10,
    ppcAdjustedPsia: Math.round(ppcAdj * 10) / 10,
  };
}

/**
 * Standing-Katz Compressibility Factor Z(Pr, Tr)
 * Evaluated using Hall-Yarborough / Dranchuk-Abou-Kassem equation of state
 */
export function gasCompressibilityFactor(pr: number, tr: number): number {
  if (pr <= 0.01) return 1.0;
  if (tr < 1.05) tr = 1.05;

  // Hall-Yarborough correlation
  const t = 1 / tr;
  const A = 0.06125 * t * Math.exp(-1.2 * Math.pow(1 - t, 2));
  const B = t * (14.76 - 9.76 * t + 4.58 * Math.pow(t, 2));
  const C = t * (90.7 - 242.2 * t + 42.4 * Math.pow(t, 2));
  const D = 2.18 + 2.82 * t;

  let y = 0.0125 * pr * t * Math.exp(-1.2 * Math.pow(1 - t, 2));
  for (let i = 0; i < 30; i++) {
    const f =
      -A * pr +
      (y + Math.pow(y, 2) + Math.pow(y, 3) - Math.pow(y, 4)) / Math.pow(1 - y, 3) -
      B * Math.pow(y, 2) +
      C * Math.pow(y, D);
    const df =
      (1 + 4 * y + 4 * Math.pow(y, 2) - 4 * Math.pow(y, 3) + Math.pow(y, 4)) / Math.pow(1 - y, 4) -
      2 * B * y +
      C * D * Math.pow(y, D - 1);
    const dy = f / df;
    y -= dy;
    if (Math.abs(dy) < 1e-6) break;
  }

  const z = (A * pr) / y;
  return Math.round(Math.max(0.2, Math.min(2.0, z)) * 1000) / 1000;
}

/**
 * Lee-Gonzalez-Eakin Gas Viscosity Correlation (cp)
 * Fig. 3-17 / GPSA Engineering Data Book
 */
export function gasViscosity(sg: number, pPsia: number, tRankine: number, z: number): number {
  const mw = sg * 28.966;
  const rho = (2.7 * sg * pPsia) / (tRankine * z * 62.4); // g/cm3 (using density in lb/ft3 / 62.4)
  const T = tRankine;

  const K = ((9.4 + 0.02 * mw) * Math.pow(T, 1.5)) / (209 + 19 * mw + T);
  const X = 3.5 + 986 / T + 0.01 * mw;
  const Y = 2.4 - 0.2 * X;

  const mu = 1e-4 * K * Math.exp(X * Math.pow(rho, Y));
  return Math.round(mu * 10000) / 10000;
}

/**
 * Eq. 3-26: API to Specific Gravity
 * SG = 141.5 / (131.5 + API)
 */
export function apiToSG(api: number): number {
  return Math.round((141.5 / (131.5 + api)) * 1000) / 1000;
}

/**
 * Eq. 3-27: Specific Gravity to API
 * API = 141.5 / SG - 131.5
 */
export function sgToApi(sg: number): number {
  if (sg <= 0) return 0;
  return Math.round((141.5 / sg - 131.5) * 10) / 10;
}

/**
 * Liquid density in lb/ft3
 * rho_L = 62.4 * SG
 */
export function liquidDensity(sg: number): number {
  return Math.round(62.4 * sg * 100) / 100;
}

/**
 * Eq. 3-29: Beggs-Robinson Oil Viscosity Correlation (cp)
 * mu_od = 10^x - 1
 * x = y * T^(-1.163)
 * y = 10^z
 * z = 3.0324 - 0.02023 * API
 */
export function beggsRobinsonViscosity(api: number, tempF: number): number {
  const safeT = Math.max(40, tempF);
  const z = 3.0324 - 0.02023 * api;
  const y = Math.pow(10, z);
  const x = y * Math.pow(safeT, -1.163);
  const mu = Math.pow(10, x) - 1;
  return Math.round(Math.max(0.1, mu) * 10) / 10;
}

/**
 * Eq. 3-30: Modified Vand's Equation for Oil-Water Emulsion Viscosity (cp)
 * mu_eff = (1 + 2.5 * phi + 10 * phi^2) * mu_c
 * where phi is volume fraction of the discontinuous phase (water cut up to 0.70 inversion)
 */
export function oilWaterMixtureViscosity(
  muOil: number,
  muWater: number,
  waterCutFraction: number // 0.0 to 1.0
): { effectiveViscosity: number; continuousPhase: "Oil" | "Water"; isEmulsionInverted: boolean } {
  const phi = Math.min(1.0, Math.max(0, waterCutFraction));
  if (phi <= 0.70) {
    // Oil is continuous, water is dispersed
    const factor = 1 + 2.5 * phi + 10 * Math.pow(phi, 2);
    return {
      effectiveViscosity: Math.round(muOil * factor * 10) / 10,
      continuousPhase: "Oil",
      isEmulsionInverted: false,
    };
  } else {
    // Water is continuous, oil is dispersed (1 - phi is discontinuous)
    const phiDiscontinuous = 1 - phi;
    const factor = 1 + 2.5 * phiDiscontinuous + 10 * Math.pow(phiDiscontinuous, 2);
    return {
      effectiveViscosity: Math.round(muWater * factor * 10) / 10,
      continuousPhase: "Water",
      isEmulsionInverted: true,
    };
  }
}

/**
 * Fluid Classification based on Section 3 Phase Behavior
 */
export function classifyReservoirFluid(
  gorScfStb: number,
  api: number,
  c7plusMolPercent: number
): "Black Oil" | "Volatile Oil" | "Retrograde Gas Condensate" | "Wet Gas" | "Dry Gas" {
  if (gorScfStb <= 2000 && c7plusMolPercent >= 20) {
    return "Black Oil";
  } else if (gorScfStb > 2000 && gorScfStb <= 3300 && api >= 40) {
    return "Volatile Oil";
  } else if (gorScfStb > 3300 && gorScfStb <= 50000 && c7plusMolPercent < 12.5) {
    return "Retrograde Gas Condensate";
  } else if (gorScfStb > 50000 && c7plusMolPercent < 4) {
    return "Wet Gas";
  }
  return "Dry Gas";
}

/**
 * Rachford-Rice Flash Equilibrium Solver (Eqs. 3-32, 3-33, 3-34)
 * Solves: sum [ z_i * (K_i - 1) / (1 + (V/L) * (K_i - 1) / (1 + V/L)) ] = 0
 * Returns V, L, vapor mole fractions y_i, liquid mole fractions x_i
 */
export interface FlashResult {
  vaporFraction: number; // V / F
  liquidFraction: number; // L / F
  vOverL: number; // V / L ratio
  gasFlowRateMmscfd: number;
  liquidFlowRateBpd: number;
  gasMolecularWeight: number;
  gasSpecificGravity: number;
  liquidMolecularWeight: number;
  liquidSpecificGravity: number;
  liquidApi: number;
  components: {
    name: string;
    feedMoles: number;
    kValue: number;
    vaporMoles: number;
    liquidMoles: number;
    yFraction: number;
    xFraction: number;
  }[];
}

export function performFlashCalculation(
  feedMolesPerDay: number,
  feedComposition: { name: string; moleFraction: number; mw: number; kValue: number; sgLiquid?: number }[]
): FlashResult {
  const F = Math.max(1, feedMolesPerDay);

  // Rachford-Rice root finding for alpha = V/F in [0, 1]
  let alpha = 0.5;
  for (let iter = 0; iter < 40; iter++) {
    let f = 0;
    let df = 0;
    for (const c of feedComposition) {
      const z = c.moleFraction;
      const K = c.kValue;
      const denom = 1 + alpha * (K - 1);
      f += (z * (K - 1)) / denom;
      df -= (z * Math.pow(K - 1, 2)) / Math.pow(denom, 2);
    }
    const delta = f / df;
    alpha -= delta;
    alpha = Math.max(0.001, Math.min(0.999, alpha));
    if (Math.abs(delta) < 1e-6) break;
  }

  const V = F * alpha;
  const L = F * (1 - alpha);
  const vOverL = V / Math.max(0.001, L);

  let totalGasWeight = 0;
  let totalLiquidWeight = 0;
  let totalLiquidVolumeTerm = 0;

  const comps = feedComposition.map((c) => {
    const K = c.kValue;
    const z = c.moleFraction;
    const x = z / (1 + alpha * (K - 1));
    const y = K * x;
    const vMoles = V * y;
    const lMoles = L * x;
    totalGasWeight += vMoles * c.mw;
    totalLiquidWeight += lMoles * c.mw;
    const sg = c.sgLiquid || (c.mw > 80 ? 0.85 : 0.5);
    totalLiquidVolumeTerm += (lMoles * c.mw) / sg;

    return {
      name: c.name,
      feedMoles: Math.round(z * F * 10) / 10,
      kValue: c.kValue,
      vaporMoles: Math.round(vMoles * 10) / 10,
      liquidMoles: Math.round(lMoles * 10) / 10,
      yFraction: Math.round(y * 1000) / 1000,
      xFraction: Math.round(x * 1000) / 1000,
    };
  });

  const mwGas = V > 0 ? totalGasWeight / V : 20;
  const sgGas = mwGas / 29;
  const mwLiquid = L > 0 ? totalLiquidWeight / L : 120;
  const sgLiquid = totalLiquidVolumeTerm > 0 ? totalLiquidWeight / totalLiquidVolumeTerm : 0.8;
  const apiLiquid = sgToApi(sgLiquid);

  // Eq. 3-37: Qg = (380 * V) / 1,000,000 MMscfd
  const gasFlowRateMmscfd = Math.round(((380 * V) / 1000000) * 100) / 100;
  // Eq. 3-40: Ql = (L * MW_L) / (350 * SG_L) BPD
  const liquidFlowRateBpd = Math.round((L * mwLiquid) / (350 * sgLiquid));

  return {
    vaporFraction: Math.round(alpha * 1000) / 1000,
    liquidFraction: Math.round((1 - alpha) * 1000) / 1000,
    vOverL: Math.round(vOverL * 100) / 100,
    gasFlowRateMmscfd,
    liquidFlowRateBpd,
    gasMolecularWeight: Math.round(mwGas * 100) / 100,
    gasSpecificGravity: Math.round(sgGas * 1000) / 1000,
    liquidMolecularWeight: Math.round(mwLiquid * 10) / 10,
    liquidSpecificGravity: Math.round(sgLiquid * 1000) / 1000,
    liquidApi: Math.round(apiLiquid * 10) / 10,
    components: comps,
  };
}

/**
 * Fig. 3-49 & Fig. 8-10: Reid Vapor Pressure (RVP) to True Vapor Pressure (TVP)
 * Correlation based on ASTM D323 at 100°F:
 * TVP ~ 1.05 * RVP + 0.15 (for RVP < 15 psia)
 */
export function rvpToTrueVaporPressure(rvpPsia: number, tempF: number = 100): number {
  const tvp100 = 1.045 * rvpPsia + 0.15;
  if (tempF === 100) return Math.round(tvp100 * 10) / 10;
  // Antoine / Clausius-Clapeyron temperature scaling
  const B = 2200;
  const tvpT = tvp100 * Math.exp(B * (1 / 560 - 1 / (tempF + 460)));
  return Math.round(tvpT * 10) / 10;
}
