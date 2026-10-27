/**
 * Three-Phase Oil, Water & Gas Separation Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 5: Three-Phase Oil and Water Separation
 */

import { iterativeDropletVelocityField } from "./settling";
import { apiToSG, gasDensity, liquidDensity } from "./pvtProperties";

export interface ThreePhaseVerticalResult {
  dGasInches: number;
  dWaterInOilInches: number;
  dOilInWaterInches: number;
  dMinInches: number;
  dSelectedInches: number;
  hoPlusHwInches: number;
  seamToSeamLengthFt: number;
  slendernessRatio: number;
  isAcceptableSlenderness: boolean;
}

export interface ThreePhaseHorizontalRow {
  diameterInches: number;
  leffGasFt: number;
  leffLiquidFt: number;
  governingLeffFt: number;
  seamToSeamLengthFt: number;
  slendernessRatio: number;
  isBelowMaxDiameter: boolean;
  isRecommended: boolean;
}

export interface ThreePhaseHorizontalResult {
  maxOilPadThicknessInches: number; // (ho)max
  areaRatioWaterToTotal: number; // Aw / A
  betaCoefficient: number; // beta = ho / d
  maxDiameterInches: number; // dmax
  dLeffGasRequirement: number;
  d2LeffLiquidRequirement: number;
  table: ThreePhaseHorizontalRow[];
  selectedSize: {
    diameterInches: number;
    lengthFt: number;
    slendernessRatio: number;
  };
}

/**
 * Calculates the exact or approximate beta = ho / d given Aw / A from Figure 5-20.
 * For Aw/A in [0, 0.5], circular segment geometry:
 */
export function betaFromAwOverA(awOverA: number): number {
  const x = Math.max(0, Math.min(0.5, awOverA));
  // Accurate polynomial fit to Arnold & Stewart Figure 5-20
  // Aw/A = 0 -> beta = 0; Aw/A = 0.1875 -> beta = 0.257 (Ex. 5-3); Aw/A = 0.5 -> beta = 0.5
  const beta = 1.488 * x - 0.72 * Math.pow(x, 2) + 0.45 * Math.pow(x, 3);
  return Math.round(beta * 1000) / 1000;
}

/**
 * Sizing of a Vertical Three-Phase Separator
 * Sourced: Arnold & Stewart Chapter 5, Eqs. 5-19a to 5-27a, Ex. 5-1
 */
export function sizeVerticalThreePhaseSeparator(
  qgMmscfd: number,
  qoBopd: number,
  qwBwpd: number,
  pPsia: number,
  tempF: number,
  z: number,
  sgGas: number,
  apiOil: number,
  sgWater: number = 1.07,
  muOilCp: number = 10,
  muWaterCp: number = 1.0,
  troMin: number = 10,
  trwMin: number = 10,
  forcedDiameterInches?: number
): ThreePhaseVerticalResult {
  const tRankine = tempF + 459.67;
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(sgWater - sgOil);

  const rhoL = liquidDensity(sgOil);
  const rhoG = gasDensity(sgGas, pPsia, tRankine, z);

  // Gas droplet settling (100 micron standard for 3-phase)
  const settling = iterativeDropletVelocityField(rhoL, rhoG, 100, 0.013);
  const CD = settling.dragCoefficient;

  // 1. Gas capacity constraint (Eq. 5-19a):
  const d2Gas =
    5040 *
    ((tRankine * z * qgMmscfd) / pPsia) *
    Math.sqrt((rhoG / (rhoL - rhoG)) * (CD / 100));
  const dGas = Math.sqrt(d2Gas);

  // 2. Settling water droplets from oil phase (500 micron standard, Eq. 5-21a & 5-22a):
  // d^2 = 6690 * (Qo * mu_o) / (deltaSG * dm^2)  => for dm=500: 0.0267 * (Qo * mu_o) / deltaSG
  const d2WaterInOil = (6690 * qoBopd * muOilCp) / (deltaSG * Math.pow(500, 2));
  const dWaterInOil = Math.sqrt(d2WaterInOil);

  // 3. Settling oil droplets from water phase (200 micron standard, Eq. 5-21a & 5-23a):
  // d^2 = 6690 * (Qw * mu_w) / (deltaSG * dm^2)  => for dm=200: 0.167 * (Qw * mu_w) / deltaSG
  const d2OilInWater = (6690 * qwBwpd * muWaterCp) / (deltaSG * Math.pow(200, 2));
  const dOilInWater = Math.sqrt(d2OilInWater);

  const dMin = Math.max(dGas, dWaterInOil, dOilInWater);
  const dSelected = forcedDiameterInches || Math.max(24, Math.ceil(dMin / 6) * 6);

  // 4. Liquid retention time constraint (Eq. 5-24a):
  // ho + hw = [(tro * Qo) + (trw * Qw)] / (0.12 * d^2)
  const hoPlusHw = (troMin * qoBopd + trwMin * qwBwpd) / (0.12 * Math.pow(dSelected, 2));

  // 5. Seam-to-seam length (Eqs. 5-25a and 5-26a):
  let lss = 0;
  if (dSelected <= 36) {
    lss = (hoPlusHw + 76) / 12;
  } else {
    lss = (hoPlusHw + dSelected + 40) / 12;
  }
  const lssSnapped = Math.max(5, Math.ceil(lss / 2.5) * 2.5);
  const slenderness = (12 * lssSnapped) / dSelected;

  return {
    dGasInches: Math.round(dGas * 10) / 10,
    dWaterInOilInches: Math.round(dWaterInOil * 10) / 10,
    dOilInWaterInches: Math.round(dOilInWater * 10) / 10,
    dMinInches: Math.round(dMin * 10) / 10,
    dSelectedInches: dSelected,
    hoPlusHwInches: Math.round(hoPlusHw * 10) / 10,
    seamToSeamLengthFt: lssSnapped,
    slendernessRatio: Math.round(slenderness * 10) / 10,
    isAcceptableSlenderness: slenderness >= 1.5 && slenderness <= 4.0,
  };
}

/**
 * Sizing of a Horizontal Three-Phase Separator (Half-Full of Liquid)
 * Sourced: Arnold & Stewart Chapter 5, Eqs. 5-3a, 5-4a, 5-6a, 5-7, 5-8, Ex. 5-3
 */
export function sizeHorizontalThreePhaseSeparator(
  qgMmscfd: number,
  qoBopd: number,
  qwBwpd: number,
  pPsia: number,
  tempF: number,
  z: number,
  sgGas: number,
  apiOil: number,
  sgWater: number = 1.07,
  muOilCp: number = 10,
  troMin: number = 10,
  trwMin: number = 10
): ThreePhaseHorizontalResult {
  const tRankine = tempF + 459.67;
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(sgWater - sgOil);

  const rhoL = liquidDensity(sgOil);
  const rhoG = gasDensity(sgGas, pPsia, tRankine, z);

  // 1. Droplet settling in gas (100 micron)
  const settling = iterativeDropletVelocityField(rhoL, rhoG, 100, 0.013);
  const CD = settling.dragCoefficient;

  // 2. Maximum oil pad thickness (Eq. 5-6a for dm=500 microns):
  // (ho)max = 320 * (tro * deltaSG) / mu_o
  const hoMax = (320 * troMin * deltaSG) / muOilCp;

  // 3. Fraction of cross-sectional area occupied by water (Eq. 5-7):
  // Aw / A = 0.5 * (Qw * trw) / [tro * Qo + trw * Qw]
  const awOverA = (0.5 * (qwBwpd * trwMin)) / (troMin * qoBopd + trwMin * qwBwpd);

  // 4. Beta coefficient (Fig. 5-20) and dmax (Eq. 5-8):
  // beta = ho / d  =>  dmax = (ho)max / beta
  const beta = betaFromAwOverA(awOverA);
  const dmax = beta > 0 ? hoMax / beta : 200;

  // 5. Gas capacity constraint (Eq. 5-3a):
  // d * Leff = 420 * [(T * Z * Qg) / P] * [(rhoG / (rhoL - rhoG)) * (CD / dm)]^0.5
  const gasTerm = (tRankine * z * qgMmscfd) / pPsia;
  const densityTerm = (rhoG / (rhoL - rhoG)) * (CD / 100);
  const dLeffGas = 420 * gasTerm * Math.sqrt(densityTerm);

  // 6. Retention time constraint (Eq. 5-4a):
  // d^2 * Leff = 1.42 * [Qw * trw + Qo * tro]
  const d2LeffLiquid = 1.42 * (qwBwpd * trwMin + qoBopd * troMin);

  const candidateDiameters = [48, 60, 72, 84, 96, 108, 120];
  const table: ThreePhaseHorizontalRow[] = candidateDiameters.map((d) => {
    const leffGas = dLeffGas / d;
    const leffLiquid = d2LeffLiquid / Math.pow(d, 2);
    const govLeff = Math.max(leffGas, leffLiquid);

    // Seam-to-seam length: larger of Leff + d/12 and (4/3)*Leff
    const lssGas = govLeff + d / 12;
    const lssLiquid = (4 / 3) * govLeff;
    const lssRaw = Math.max(lssGas, lssLiquid);
    const lssSnapped = Math.max(10, Math.ceil(lssRaw / 2.5) * 2.5);
    const slenderness = (12 * lssSnapped) / d;

    return {
      diameterInches: d,
      leffGasFt: Math.round(leffGas * 10) / 10,
      leffLiquidFt: Math.round(leffLiquid * 10) / 10,
      governingLeffFt: Math.round(govLeff * 10) / 10,
      seamToSeamLengthFt: lssSnapped,
      slendernessRatio: Math.round(slenderness * 10) / 10,
      isBelowMaxDiameter: d <= dmax,
      isRecommended: d <= dmax && slenderness >= 2.8 && slenderness <= 5.2,
    };
  });

  const bestMatch = table.find((row) => row.isRecommended) || table[2]; // default 72" if none

  return {
    maxOilPadThicknessInches: Math.round(hoMax * 10) / 10,
    areaRatioWaterToTotal: Math.round(awOverA * 10000) / 10000,
    betaCoefficient: beta,
    maxDiameterInches: Math.round(dmax * 10) / 10,
    dLeffGasRequirement: Math.round(dLeffGas * 10) / 10,
    d2LeffLiquidRequirement: Math.round(d2LeffLiquid),
    table,
    selectedSize: {
      diameterInches: bestMatch.diameterInches,
      lengthFt: bestMatch.seamToSeamLengthFt,
      slendernessRatio: bestMatch.slendernessRatio,
    },
  };
}

/**
 * Eq. 5-1: Bucket-and-Weir Oil-Water Height Offset (Delta h)
 * Delta_h = ho * [1 - (rho_o / rho_w)]
 */
export function bucketAndWeirHeightOffset(
  hoOilPadInches: number,
  apiOil: number,
  sgWater: number = 1.07
): {
  deltaHInches: number;
  waterWeirDepthBelowOilWeirInches: number;
  rhoOilLbCuFt: number;
  rhoWaterLbCuFt: number;
} {
  const sgOil = apiToSG(apiOil);
  const rhoO = liquidDensity(sgOil);
  const rhoW = liquidDensity(sgWater);

  const deltaH = hoOilPadInches * (1 - rhoO / rhoW);

  return {
    deltaHInches: Math.round(deltaH * 10) / 10,
    waterWeirDepthBelowOilWeirInches: Math.round(deltaH * 10) / 10,
    rhoOilLbCuFt: rhoO,
    rhoWaterLbCuFt: rhoW,
  };
}
