/**
 * Casing Design Engineering Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 7.
 */

import { API_CASING_GRADES, SteelGrade } from '../math/tables';

export interface CasingPropertiesResult {
  odInches: number;
  idInches: number;
  wallThicknessInches: number;
  dtRatio: number;
  crossSectionAreaSqIn: number;
  pipeBodyYieldLbf: number;
  barlowBurstPressurePsi: number;
  apiCollapsePressurePsi: number;
  jointStrengthLbf: number;
}

/**
 * 7.1 API Casing Performance Properties
 * Sourced: Bourgoyne Ch. 7, Section 7.2, Eq. 7.1 - 7.6
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
  // Sourced: Bourgoyne Ch. 7, Table 7.3 & Eq. 7.3 - 7.6
  let collapse = 0;
  // Plastic collapse constants A, B, C based on Yp (API Bul. 5C3)
  const YpPsi = Yp;
  const A = 2.876 + 0.10679e-4 * YpPsi + 0.21301e-10 * Math.pow(YpPsi, 2);
  const B = 0.026233 + 0.50609e-6 * YpPsi;
  const C = -465.36 + 0.030867 * YpPsi - 0.10483e-7 * Math.pow(YpPsi, 2);

  // Region boundaries:
  const dtYield = (Math.sqrt(Math.pow(A - 2, 2) + 8 * (B + C / YpPsi)) + (A - 2)) / (2 * B);
  const dtPlastic = (YpPsi * (A - F_factor(YpPsi))) / (C + YpPsi * B);
  const dtTransition = (B - G_factor(YpPsi)) / (2 * (A - 2));

  if (dtRatio <= 14) {
    // 1. Yield Strength Collapse
    collapse = 2 * Yp * ((dtRatio - 1) / Math.pow(dtRatio, 2));
  } else if (dtRatio <= 25) {
    // 2. Plastic Collapse
    collapse = Yp * (A / dtRatio - B) - C;
  } else if (dtRatio <= 37) {
    // 3. Transition Collapse
    collapse = Yp * (2.063 / dtRatio - 0.0546);
  } else {
    // 4. Elastic Collapse (Euler)
    collapse = (46.95e6) / (dtRatio * Math.pow(dtRatio - 1, 2));
  }

  // Joint Strength Estimation
  let jointEff = 0.85; // STC
  if (jointType === 'LTC') jointEff = 0.95;
  if (jointType === 'Buttress') jointEff = 1.0;
  const jointStrength = pipeBodyYield * jointEff;

  return {
    odInches: D,
    idInches: Math.round(d * 1000) / 1000,
    wallThicknessInches: t,
    dtRatio: Math.round(dtRatio * 10) / 10,
    crossSectionAreaSqIn: Math.round(area * 100) / 100,
    pipeBodyYieldLbf: Math.round(pipeBodyYield),
    barlowBurstPressurePsi: Math.round(burst),
    apiCollapsePressurePsi: Math.round(Math.max(100, collapse)),
    jointStrengthLbf: Math.round(jointStrength),
  };
}

function F_factor(yp: number): number {
  return 3.14 * Math.sqrt(yp / 10000);
}
function G_factor(yp: number): number {
  return 0.01 * (yp / 10000);
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
