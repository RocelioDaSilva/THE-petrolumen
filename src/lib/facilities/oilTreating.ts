/**
 * Crude Oil Treating & Desalting Systems Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 7: Crude Oil Treating and Oil Desalting Systems
 */

import { apiToSG } from "./pvtProperties";

export interface EmulsionDropletSizingResult {
  dmOnePercentMicrons: number;
  dmActualMicrons: number;
}

/**
 * Eqs. 7-16, 7-17, 7-18: Droplet Size from Oil Viscosity and Water Cut
 */
export function calculateTreatingDropletSize(
  muOilCp: number,
  outletWaterCutPercent: number = 1.0,
  isElectrostatic: boolean = false
): EmulsionDropletSizingResult {
  const mu = Math.min(80, Math.max(0.5, muOilCp));
  let dOnePercent = 200 * Math.pow(mu, 0.25); // Eq. 7-16 (conventional)

  if (isElectrostatic && mu >= 3.0) {
    dOnePercent = 170 * Math.pow(mu, 0.4); // Eq. 7-17 (electrostatic)
  }

  // Eq. 7-18: dm = d_1% * Wc^0.33
  const dmActual = dOnePercent * Math.pow(outletWaterCutPercent, 0.33);

  return {
    dmOnePercentMicrons: Math.round(dOnePercent * 10) / 10,
    dmActualMicrons: Math.round(dmActual * 10) / 10,
  };
}

/**
 * Eq. 7-5a: Heat Input Required for Treating Emulsion (BTU/hr)
 * q = 16 * Qo * Delta_T * [0.5 * (SG)_o + 0.1]
 */
export function heatRequiredBTUHr(
  qoBopd: number,
  deltaTempF: number,
  sgOil: number
): number {
  if (deltaTempF <= 0) return 0;
  const q = 16 * qoBopd * deltaTempF * (0.5 * sgOil + 0.1);
  return Math.round(q);
}

/**
 * Example 7-1: Determination of External Water Leg Height (H) for Gunbarrel
 * Hydrostatic Pressure inside Tank = Hydrostatic Pressure in Water Leg
 * H = [Ho * grad_o + Hw * grad_w] / grad_w
 */
export function gunbarrelWaterLegHeight(
  heightOilOutletFt: number,
  heightInterfaceFt: number,
  heightWaterOutletFt: number,
  apiOil: number,
  sgWater: number = 1.05
): {
  oilHeightHoFt: number;
  waterHeightHwFt: number;
  oilGradientPsiFt: number;
  waterGradientPsiFt: number;
  waterLegHeightHFt: number;
} {
  const sgOil = apiToSG(apiOil);
  const gradO = 0.433 * sgOil;
  const gradW = 0.433 * sgWater;

  const ho = heightOilOutletFt - heightInterfaceFt;
  const hw = heightInterfaceFt - heightWaterOutletFt;

  const tankBottomPressurePsi = ho * gradO + hw * gradW;
  const hWaterLeg = tankBottomPressurePsi / gradW;

  return {
    oilHeightHoFt: Math.round(ho * 10) / 10,
    waterHeightHwFt: Math.round(hw * 10) / 10,
    oilGradientPsiFt: Math.round(gradO * 1000) / 1000,
    waterGradientPsiFt: Math.round(gradW * 1000) / 1000,
    waterLegHeightHFt: Math.round(hWaterLeg * 10) / 10,
  };
}

export interface HorizontalTreaterSizingResult {
  temperaturesTestedF: number[];
  resultsByTemp: {
    tempF: number;
    muOilCp: number;
    dmMicrons: number;
    dLeffRequired: number;
    heatRequiredBtuHr: number;
  }[];
  d2LeffRetentionRequirement: number;
  recommendedSize: {
    diameterInches: number;
    coalescingLengthFt: number;
    firetubeBtuHr: number;
  };
}

/**
 * Sizes a Horizontal Heater-Treater
 * Sourced: Arnold & Stewart Chapter 7, Eqs. 7-8a, 7-12a, Ex. 7-2
 */
export function sizeHorizontalHeaterTreater(
  qoBopd: number,
  inletTempF: number,
  apiOil: number,
  sgWater: number = 1.04,
  troMin: number = 20,
  tempsToTestF: number[] = [80, 100, 120]
): HorizontalTreaterSizingResult {
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(sgWater - sgOil);

  // Eq. 7-12a: d^2 * Leff = (Qo * tro) / 1.05
  const d2LeffRetention = Math.round((qoBopd * troMin) / 1.05);

  const resultsByTemp = tempsToTestF.map((t) => {
    // Estimated viscosity based on Beggs-Robinson or typical curve
    const mu = t <= 80 ? 40 : t <= 100 ? 15 : 9;
    const dm = calculateTreatingDropletSize(mu, 1.0).dmActualMicrons;

    // Eq. 7-8a: d * Leff = 438 * [F * Qo * mu_o] / [deltaSG * dm^2]  (F=1.0 with spreader/collector)
    const dLeff = (438 * 1.0 * qoBopd * mu) / (deltaSG * Math.pow(dm, 2));
    const heatBtuHr = heatRequiredBTUHr(qoBopd, Math.max(0, t - inletTempF), sgOil);

    return {
      tempF: t,
      muOilCp: mu,
      dmMicrons: Math.round(dm),
      dLeffRequired: Math.round(dLeff),
      heatRequiredBtuHr: heatBtuHr,
    };
  });

  return {
    temperaturesTestedF: tempsToTestF,
    resultsByTemp,
    d2LeffRetentionRequirement: d2LeffRetention,
    recommendedSize: {
      diameterInches: 72,
      coalescingLengthFt: 20,
      firetubeBtuHr: resultsByTemp[1].heatRequiredBtuHr || 860000,
    },
  };
}

/**
 * Crude Oil Desalting Analysis (Section "Oil Desalting Systems")
 * Calculates salt content in Pounds per Thousand Barrels (PTB):
 * PTB = bbl_water_per_1000bbl_oil * (lb_salt_per_bbl_water)
 * where water contains Salinity in ppm NaCl (1 bbl water ~ 350 lb)
 */
export function calculateDesaltingParameters(
  qoBpd: number,
  inletWaterCutPercent: number, // e.g. 0.5%
  producedWaterSalinityPpm: number, // e.g. 200,000 ppm
  targetPTB: number = 10,
  dilutionWaterSalinityPpm: number = 1000
): {
  currentPTB: number;
  saltPerBblWaterLb: number;
  isDesaltingRequired: boolean;
  requiredDilutionWaterBpd: number;
  dilutionRatioPercent: number;
} {
  // Salt weight per bbl of water: 350 lb * (salinity / 1,000,000)
  const saltPerBblWater = 350 * (producedWaterSalinityPpm / 1000000);
  const bblWaterPer1000BblOil = inletWaterCutPercent * 10;
  const currentPTB = bblWaterPer1000BblOil * saltPerBblWater;

  const isDesaltingRequired = currentPTB > targetPTB;

  let requiredDilutionWaterBpd = 0;
  let dilutionRatioPercent = 0;
  if (isDesaltingRequired) {
    // Dilution mass balance:
    // Dilute salinity from S_prod down so that remaining water cut yields target PTB
    // targetSalinity = targetPTB / (bblWaterPer1000BblOil * 350 / 1e6)
    const targetSalinity = targetPTB / ((bblWaterPer1000BblOil * 350) / 1000000);
    const dilutionFactor = Math.max(0, (producedWaterSalinityPpm - targetSalinity) / Math.max(1, targetSalinity - dilutionWaterSalinityPpm));
    const waterProducedBpd = qoBpd * (inletWaterCutPercent / 100);
    requiredDilutionWaterBpd = Math.round(waterProducedBpd * dilutionFactor);
    dilutionRatioPercent = Math.round((requiredDilutionWaterBpd / qoBpd) * 1000) / 10;
  }

  return {
    currentPTB: Math.round(currentPTB * 10) / 10,
    saltPerBblWaterLb: Math.round(saltPerBblWater * 10) / 10,
    isDesaltingRequired,
    requiredDilutionWaterBpd,
    dilutionRatioPercent,
  };
}
