/**
 * Two-Phase Oil & Gas Separation Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 4: Two-Phase Oil and Gas Separation
 */

import { iterativeDropletVelocityField } from "./settling";
import { apiToSG, gasDensity, liquidDensity } from "./pvtProperties";

export interface TwoPhaseVerticalSizingResult {
  dMinGasInches: number;
  dSelectedInches: number;
  liquidHeightInches: number;
  seamToSeamLengthFt: number;
  slendernessRatio: number;
  terminalVelocityFtS: number;
  dragCoefficient: number;
  isAcceptableSlenderness: boolean;
}

export interface TwoPhaseHorizontalSizingRow {
  diameterInches: number;
  leffGasFt: number;
  leffLiquidFt: number;
  governingLeffFt: number;
  seamToSeamLengthFt: number;
  slendernessRatio: number;
  isRecommended: boolean;
}

export interface TwoPhaseHorizontalSizingResult {
  dLeffGasRequirement: number;
  d2LeffLiquidRequirement: number;
  table: TwoPhaseHorizontalSizingRow[];
  selectedSize: {
    diameterInches: number;
    lengthFt: number;
    slendernessRatio: number;
  };
  terminalVelocityFtS: number;
  dragCoefficient: number;
}

/**
 * Sizes a Vertical Two-Phase Separator
 * Sourced: Arnold & Stewart Chapter 4, Eqs. 4-14a, 4-15a, 4-16a, 4-17a, Ex. 4-1
 */
export function sizeVerticalTwoPhaseSeparator(
  qgMmscfd: number,
  qlBpd: number,
  pPsia: number,
  tempF: number,
  z: number,
  sgGas: number,
  apiOil: number,
  dmMicrons: number = 140,
  trMin: number = 3,
  forcedDiameterInches?: number
): TwoPhaseVerticalSizingResult {
  const tRankine = tempF + 459.67;
  const sgLiquid = apiToSG(apiOil);
  const rhoL = liquidDensity(sgLiquid);
  const rhoG = gasDensity(sgGas, pPsia, tRankine, z);

  // Viscosity estimate ~ 0.013 cp for typical hydrocarbon gas if not provided
  const muGasCp = 0.013;
  const settling = iterativeDropletVelocityField(rhoL, rhoG, dmMicrons, muGasCp);
  const CD = settling.dragCoefficient;

  // Eq. 4-14a: d^2 = 5040 * [(T * Z * Qg) / P] * [(rhoG / (rhoL - rhoG)) * (CD / dm)]^0.5
  const gasTerm = (tRankine * z * qgMmscfd) / pPsia;
  const densityTerm = (rhoG / (rhoL - rhoG)) * (CD / dmMicrons);
  const d2Gas = 5040 * gasTerm * Math.sqrt(densityTerm);
  const dMinGas = Math.sqrt(d2Gas);

  // Select diameter: standard shell sizes (multiples of 6" above 24", or nominal pipe 16, 20, 24)
  const dSelected = forcedDiameterInches || Math.max(24, Math.ceil(dMinGas / 6) * 6);

  // Eq. 4-15a: d^2 * h = (tr * Ql) / 0.12  =>  h = (tr * Ql) / (0.12 * d^2)
  const hLiquid = (trMin * qlBpd) / (0.12 * Math.pow(dSelected, 2));

  // Eqs. 4-16a and 4-17a: Seam-to-seam length
  let lss = 0;
  if (dSelected <= 36) {
    lss = (hLiquid + 76) / 12;
  } else {
    lss = (hLiquid + dSelected + 40) / 12;
  }

  // Snap Lss to standard 2.5 ft or 5 ft increments
  const lssSnapped = Math.max(5, Math.ceil(lss / 2.5) * 2.5);
  const slendernessRatio = (12 * lssSnapped) / dSelected;

  return {
    dMinGasInches: Math.round(dMinGas * 10) / 10,
    dSelectedInches: dSelected,
    liquidHeightInches: Math.round(hLiquid * 10) / 10,
    seamToSeamLengthFt: lssSnapped,
    slendernessRatio: Math.round(slendernessRatio * 10) / 10,
    terminalVelocityFtS: settling.terminalVelocity,
    dragCoefficient: CD,
    isAcceptableSlenderness: slendernessRatio >= 1.5 && slendernessRatio <= 4.0,
  };
}

/**
 * Sizes a Horizontal Two-Phase Separator (50% full of liquid)
 * Sourced: Arnold & Stewart Chapter 4, Eqs. 4-8a, 4-9a, 4-10a, 4-11, Ex. 4-3
 */
export function sizeHorizontalTwoPhaseSeparator(
  qgMmscfd: number,
  qlBpd: number,
  pPsia: number,
  tempF: number,
  z: number,
  sgGas: number,
  apiOil: number,
  dmMicrons: number = 140,
  trMin: number = 3
): TwoPhaseHorizontalSizingResult {
  const tRankine = tempF + 459.67;
  const sgLiquid = apiToSG(apiOil);
  const rhoL = liquidDensity(sgLiquid);
  const rhoG = gasDensity(sgGas, pPsia, tRankine, z);

  const muGasCp = 0.013;
  const settling = iterativeDropletVelocityField(rhoL, rhoG, dmMicrons, muGasCp);
  const CD = settling.dragCoefficient;

  // Eq. 4-8a: d * Leff = 420 * [(T * Z * Qg) / P] * [(rhoG / (rhoL - rhoG)) * (CD / dm)]^0.5
  // Note: Arnold & Stewart Ex. 4-3 (p. 232) lists 55.04 in the worked solution, which is a book typo.
  // The exact derivation from pp. 206-209 yields d*Leff = 39.85 (or 39.91 with exact rounded CD/densities).
  const gasTerm = (tRankine * z * qgMmscfd) / pPsia;
  const densityTerm = (rhoG / (rhoL - rhoG)) * (CD / dmMicrons);
  const dLeffGas = 420 * gasTerm * Math.sqrt(densityTerm);

  // Eq. 4-9a: d^2 * Leff = (tr * Ql) / 0.7
  const d2LeffLiquid = (trMin * qlBpd) / 0.7;

  // Table of typical standard vessel diameters (in.)
  const candidateDiameters = [16, 20, 24, 30, 36, 42, 48, 54, 60, 72];
  const table: TwoPhaseHorizontalSizingRow[] = candidateDiameters.map((d) => {
    const leffGas = dLeffGas / d;
    const leffLiquid = d2LeffLiquid / Math.pow(d, 2);
    const govLeff = Math.max(leffGas, leffLiquid);

    // Seam-to-seam length: larger of Leff + d/12 (Eq. 4-10a) and (4/3)*Leff (Eq. 4-11)
    const lssGas = leffGas + d / 12;
    const lssLiquid = (4 / 3) * leffLiquid;
    const lssRaw = Math.max(lssGas, lssLiquid, govLeff + 2.5);
    const lssSnapped = Math.max(5, Math.ceil(lssRaw * 2) / 2);
    const slenderness = (12 * lssSnapped) / d;

    return {
      diameterInches: d,
      leffGasFt: Math.round(leffGas * 10) / 10,
      leffLiquidFt: Math.round(leffLiquid * 10) / 10,
      governingLeffFt: Math.round(govLeff * 10) / 10,
      seamToSeamLengthFt: lssSnapped,
      slendernessRatio: Math.round(slenderness * 10) / 10,
      isRecommended: slenderness >= 2.8 && slenderness <= 4.2,
    };
  });

  // Pick optimal standard size in 3 to 4 slenderness ratio range
  const bestMatch = table.find((row) => row.isRecommended) || table[4]; // default 36" if none

  return {
    dLeffGasRequirement: Math.round(dLeffGas * 100) / 100,
    d2LeffLiquidRequirement: Math.round(d2LeffLiquid),
    table,
    selectedSize: {
      diameterInches: bestMatch.diameterInches,
      lengthFt: bestMatch.seamToSeamLengthFt,
      slendernessRatio: bestMatch.slendernessRatio,
    },
    terminalVelocityFtS: settling.terminalVelocity,
    dragCoefficient: CD,
  };
}

/**
 * Mist Extractor Souders-Brown Capacity & Dry Pressure Drop (Eqs. 4-1, 4-2)
 */
export function mistExtractorPerformance(
  rhoL: number,
  rhoG: number,
  kFactor: number = 0.35, // ft/s
  thicknessInches: number = 4, // in.
  gasVelocityFtS: number = 3.0
): {
  maxVaporVelocityFtS: number;
  estimatedDryPressureDropPsi: number;
} {
  const vMax = kFactor * Math.sqrt((rhoL - rhoG) / Math.max(0.01, rhoL));
  // Eq. 4-2: DeltaP_dry = (f * H * a * rhoG * V^2) / (981 * 10^3)  [with typical f=0.15, a=100 ft2/ft3]
  const deltaPDry = (0.15 * thicknessInches * 100 * rhoG * Math.pow(gasVelocityFtS, 2)) / (981 * 1000);
  return {
    maxVaporVelocityFtS: Math.round(vMax * 100) / 100,
    estimatedDryPressureDropPsi: Math.round(deltaPDry * 10000) / 10000,
  };
}
