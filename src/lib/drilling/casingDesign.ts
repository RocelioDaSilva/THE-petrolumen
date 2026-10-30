/**
 * Casing Design Engineering Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 7.
 */

import { API_CASING_GRADES, SteelGrade } from '../math/tables';

export interface CasingCollapseRegimeInfo {
  regime: 'yield' | 'plastic' | 'transition' | 'elastic';
  dtRatio: number;
  dtYield: number;
  dtPlastic: number;
  dtTransition: number;
  A: number;
  B: number;
  C: number;
  F: number;
  G: number;
}

export interface CasingPropertiesResult {
  odInches: number;
  idInches: number;
  wallThicknessInches: number;
  dtRatio: number;
  crossSectionAreaSqIn: number;
  pipeBodyYieldLbf: number;
  barlowBurstPressurePsi: number;
  apiCollapsePressurePsi: number;
  collapseRegime: 'yield' | 'plastic' | 'transition' | 'elastic';
  collapseDetails: CasingCollapseRegimeInfo;
  jointStrengthLbf: number;
}

/**
 * Standard API 5C3 / ISO 10400 empirical collapse constants by grade
 * Reference: API Bulletin 5C3 Section 3, Table 1 & Bourgoyne Ch. 7, Table 7.3
 */
export const API_5C3_GRADE_COLLAPSE_FACTORS: Record<string, {
  A: number;
  B: number;
  C: number;
  F: number;
  G: number;
  dtYield: number;
  dtPlastic: number;
  dtTransition: number;
}> = {
  'H-40': { A: 2.950, B: 0.0465, C: 754, F: 2.063, G: 0.0325, dtYield: 16.44, dtPlastic: 27.01, dtTransition: 42.64 },
  'J-55': { A: 2.991, B: 0.0541, C: 1206, F: 1.989, G: 0.0360, dtYield: 14.81, dtPlastic: 25.01, dtTransition: 37.21 },
  'K-55': { A: 2.991, B: 0.0541, C: 1206, F: 1.989, G: 0.0360, dtYield: 14.81, dtPlastic: 25.01, dtTransition: 37.21 },
  'C-75': { A: 3.054, B: 0.0642, C: 1806, F: 1.990, G: 0.0417, dtYield: 13.60, dtPlastic: 22.91, dtTransition: 32.05 },
  'L-80': { A: 3.071, B: 0.0667, C: 1955, F: 1.998, G: 0.0434, dtYield: 13.38, dtPlastic: 22.47, dtTransition: 31.02 },
  'N-80': { A: 3.071, B: 0.0667, C: 1955, F: 1.998, G: 0.0434, dtYield: 13.38, dtPlastic: 22.47, dtTransition: 31.02 },
  'C-90': { A: 3.106, B: 0.0718, C: 2254, F: 2.017, G: 0.0466, dtYield: 13.01, dtPlastic: 21.69, dtTransition: 29.18 },
  'T-95': { A: 3.124, B: 0.0743, C: 2404, F: 2.029, G: 0.0482, dtYield: 12.85, dtPlastic: 21.33, dtTransition: 28.36 },
  'C-95': { A: 3.124, B: 0.0743, C: 2404, F: 2.029, G: 0.0482, dtYield: 12.85, dtPlastic: 21.33, dtTransition: 28.36 },
  'P-110': { A: 3.181, B: 0.0819, C: 2852, F: 2.066, G: 0.0532, dtYield: 12.44, dtPlastic: 20.41, dtTransition: 26.22 },
  'Q-125': { A: 3.239, B: 0.0895, C: 3301, F: 2.106, G: 0.0582, dtYield: 12.11, dtPlastic: 19.63, dtTransition: 24.46 },
};

/**
 * Calculates API 5C3 collapse factors and D/t regime boundaries for any arbitrary or derated yield strength.
 * Sourced: API Bulletin 5C3 Section 3 & ISO 10400 formulas.
 */
export function calculateAPI5C3Coefficients(ypPsi: number) {
  const Yp = Math.max(10000, ypPsi);
  // Empirical coefficients A, B, C (API Bul. 5C3 §3.2.1, Eq. 3.2.1-1 to 3.2.1-3)
  // Notice linear coefficient is 0.10679e-5 (API 5C3), NOT 0.10679e-4
  const A = 2.8762 + 0.10679e-5 * Yp + 0.21301e-10 * Math.pow(Yp, 2);
  const B = 0.026233 + 0.50609e-6 * Yp;
  const C = -465.36 + 0.030867 * Yp - 0.10483e-7 * Math.pow(Yp, 2);

  // Transition parameters F and G (Eq. 3.2.3-1 to 3.2.3-3)
  const m = B / A;
  const dtTransition = (2 + m) / (3 * m);
  const X = (3 * m) / (2 + m);
  const F = (46.95e6 * Math.pow(X, 3)) / (Yp * (X - m) * Math.pow(1 - X, 2));
  const G = F * m;

  // D/t Boundaries (API Bul. 5C3 Table 1 formulas)
  const dtPlastic = (Yp * (A - F)) / (C + Yp * (B - G));
  const bPlusCOverYp = B + C / Yp;
  const dtYield = (Math.sqrt(Math.pow(A - 2, 2) + 8 * bPlusCOverYp) + (A - 2)) / (2 * bPlusCOverYp);

  return { A, B, C, F, G, dtYield, dtPlastic, dtTransition };
}

/**
 * 7.1 API Casing Performance Properties
 * Sourced: API Bulletin 5C3 (6th Ed.) / ISO 10400 and Bourgoyne Ch. 7, Section 7.2
 */
export function calculateCasingProperties(
  odInches: number,
  wallThicknessInches: number,
  gradeKey: string = 'N-80',
  jointType: 'STC' | 'LTC' | 'Buttress' = 'LTC'
): CasingPropertiesResult {
  const grade = API_CASING_GRADES[gradeKey] || API_CASING_GRADES['N-80'];
  const Yp = grade.minYieldPsi;
  const D = odInches;
  const t = wallThicknessInches;
  const d = D - 2 * t;
  const dtRatio = D / t;

  // Cross section area A = pi/4 * (D^2 - d^2)
  const area = (Math.PI / 4) * (Math.pow(D, 2) - Math.pow(d, 2));

  // Pipe body yield strength in lbf: F_y = A * Y_p (Eq. 7.1)
  const pipeBodyYield = area * Yp;

  // Barlow's Burst Equation with API 12.5% wall tolerance factor:
  // p_b = 0.875 * (2 * Y_p * t) / D (Eq. 7.2)
  const burst = (0.875 * 2 * Yp * t) / D;

  // API 4-Region Collapse Formulation (Yield, Plastic, Transition, Elastic)
  // Sourced: API Bulletin 5C3 Section 3 & Bourgoyne Ch. 7, Table 7.3 & Eq. 7.3 - 7.6
  const stdFactors = API_5C3_GRADE_COLLAPSE_FACTORS[gradeKey] || API_5C3_GRADE_COLLAPSE_FACTORS['N-80'];
  const factors = stdFactors || calculateAPI5C3Coefficients(Yp);

  const { A, B, C, F, G, dtYield, dtPlastic, dtTransition } = factors;

  let collapse = 0;
  let regime: 'yield' | 'plastic' | 'transition' | 'elastic';

  if (dtRatio <= dtYield) {
    // 1. Yield Strength Collapse (Lamé thick-wall plastic limit)
    regime = 'yield';
    collapse = 2 * Yp * ((dtRatio - 1) / Math.pow(dtRatio, 2));
  } else if (dtRatio <= dtPlastic) {
    // 2. Plastic Collapse (API empirical regression)
    regime = 'plastic';
    collapse = Yp * (A / dtRatio - B) - C;
  } else if (dtRatio <= dtTransition) {
    // 3. Transition Collapse (Inter-regime tangency bridge)
    regime = 'transition';
    collapse = Yp * (F / dtRatio - G);
  } else {
    // 4. Elastic Collapse (Euler instability independent of yield)
    regime = 'elastic';
    collapse = 46.95e6 / (dtRatio * Math.pow(dtRatio - 1, 2));
  }

  // Joint Strength Estimation
  let jointEff = 0.85; // STC
  if (jointType === 'LTC') jointEff = 0.95;
  if (jointType === 'Buttress') jointEff = 1.0;
  const jointStrength = pipeBodyYield * jointEff;

  const collapseInfo: CasingCollapseRegimeInfo = {
    regime,
    dtRatio: Math.round(dtRatio * 100) / 100,
    dtYield: Math.round(dtYield * 100) / 100,
    dtPlastic: Math.round(dtPlastic * 100) / 100,
    dtTransition: Math.round(dtTransition * 100) / 100,
    A: Math.round(A * 1000) / 1000,
    B: Math.round(B * 10000) / 10000,
    C: Math.round(C),
    F: Math.round(F * 1000) / 1000,
    G: Math.round(G * 10000) / 10000,
  };

  return {
    odInches: D,
    idInches: Math.round(d * 1000) / 1000,
    wallThicknessInches: t,
    dtRatio: Math.round(dtRatio * 10) / 10,
    crossSectionAreaSqIn: Math.round(area * 100) / 100,
    pipeBodyYieldLbf: Math.round(pipeBodyYield),
    barlowBurstPressurePsi: Math.round(burst),
    apiCollapsePressurePsi: Math.round(Math.max(100, collapse)),
    collapseRegime: regime,
    collapseDetails: collapseInfo,
    jointStrengthLbf: Math.round(jointStrength),
  };
}

/**
 * 7.2 Biaxial Stress Correction for Casing Collapse Resistance
 * Sourced: Bourgoyne Ch. 7, Section 7.3, Eq. 7.7 (von Mises ellipse of plasticity)
 * Y_pa / Y_p = sqrt(1 - 0.75 * (sigma_a / Y_p)^2) - 0.5 * (sigma_a / Y_p)
 */
export function biaxialCollapseDerating(
  axialTensileStressPsi: number,
  nominalYieldStrengthPsi: number,
  nominalCollapsePressurePsi: number
): { deratedYieldPsi: number; deratedCollapsePsi: number; deratingFraction: number } {
  const sigmaA = Math.max(0, axialTensileStressPsi);
  const ratio = sigmaA / Math.max(1000, nominalYieldStrengthPsi);

  if (ratio >= 1.0) {
    return { deratedYieldPsi: 0, deratedCollapsePsi: 0, deratingFraction: 0 };
  }

  // Biaxial correction factor
  const factor = Math.sqrt(Math.max(0, 1 - 0.75 * Math.pow(ratio, 2))) - 0.5 * ratio;
  const clampedFactor = Math.max(0.1, Math.min(1.0, factor));

  const deratedCollapse = nominalCollapsePressurePsi * clampedFactor;

  return {
    deratedYieldPsi: Math.round(nominalYieldStrengthPsi * clampedFactor),
    deratedCollapsePsi: Math.round(deratedCollapse),
    deratingFraction: Math.round(clampedFactor * 1000) / 1000,
  };
}

/**
 * 7.3 Casing Design Safety Factors Evaluation
 * Checks Burst, Collapse, and Tension against design limits
 */
export interface CasingDesignCheck {
  burstDesignFactor: number;
  burstPassed: boolean;
  collapseDesignFactor: number;
  collapsePassed: boolean;
  tensionDesignFactor: number;
  tensionPassed: boolean;
  allPassed: boolean;
}

export function evaluateCasingDesignFactors(
  burstRatingPsi: number,
  anticipatedInternalPressurePsi: number,
  collapseRatingPsi: number,
  anticipatedExternalPressurePsi: number,
  jointStrengthLbf: number,
  actualAxialLoadLbf: number,
  minBurstDF: number = 1.10,
  minCollapseDF: number = 1.125,
  minTensionDF: number = 1.60
): CasingDesignCheck {
  const dfBurst = anticipatedInternalPressurePsi > 0
    ? burstRatingPsi / anticipatedInternalPressurePsi
    : 99.0;
  const dfCollapse = anticipatedExternalPressurePsi > 0
    ? collapseRatingPsi / anticipatedExternalPressurePsi
    : 99.0;
  const dfTension = actualAxialLoadLbf > 0
    ? jointStrengthLbf / actualAxialLoadLbf
    : 99.0;

  const burstPassed = dfBurst >= minBurstDF;
  const collapsePassed = dfCollapse >= minCollapseDF;
  const tensionPassed = dfTension >= minTensionDF;

  return {
    burstDesignFactor: Math.round(dfBurst * 100) / 100,
    burstPassed,
    collapseDesignFactor: Math.round(dfCollapse * 100) / 100,
    collapsePassed,
    tensionDesignFactor: Math.round(dfTension * 100) / 100,
    tensionPassed,
    allPassed: burstPassed && collapsePassed && tensionPassed,
  };
}

/**
 * Buoyancy factor for tubular strings in drilling fluid
 * B_f = 1 - (rho_mud / rho_steel) = 1 - (rho_mud / 65.5)
 */
export function casingBuoyancyFactor(mudWeightPpg: number): number {
  return Math.round((1 - mudWeightPpg / 65.5) * 1000) / 1000;
}
