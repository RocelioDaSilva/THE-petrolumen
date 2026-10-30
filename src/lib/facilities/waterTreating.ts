/**
 * Produced Water Treating & Water Injection Systems Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 9: Produced Water Treating Systems & Chapter 10: Water Injection Systems
 */

import { apiToSG } from "./pvtProperties";

export interface RegulatoryStandard {
  country: string;
  limitMgL: number;
  notes: string;
}

// Table 9-1: Worldwide Produced Water Effluent Oil Concentration Limitations
export const WORLDWIDE_DISPOSAL_STANDARDS: Record<string, RegulatoryStandard> = {
  "USA-OCS": { country: "USA (OCS Waters)", limitMgL: 29, notes: "Daily max 42 mg/L, monthly avg 29 mg/L; zero inland discharge" },
  "NorthSea": { country: "North Sea / Australia / UK / Norway", limitMgL: 30, notes: "OSPAR 30 mg/L standard for all offshore platforms" },
  "Brazil": { country: "Brazil (IBAMA) / Colombia / Ecuador", limitMgL: 30, notes: "CONAMA standard for offshore exploration & production" },
  "Indonesia": { country: "Indonesia (MIGAS)", limitMgL: 25, notes: "15 mg/L new facilities, 25 mg/L grandfathered facilities" },
  "MiddleEast": { country: "Malaysia / Middle East", limitMgL: 30, notes: "All offshore platforms" },
  "WestAfrica": { country: "Nigeria / Angola / Cameroon / Ivory Coast", limitMgL: 50, notes: "EGASPIN and regional offshore guidelines" },
  "Thailand": { country: "Thailand (PTT)", limitMgL: 50, notes: "Gulf of Thailand offshore standard" },
};

export interface SkimVesselSizingResult {
  horizontal: {
    diameterInches: number;
    effectiveLengthFt: number;
    seamToSeamLengthFt: number;
    slendernessRatio: number;
  };
  vertical: {
    diameterInches: number;
    waterHeightFt: number;
    seamToSeamHeightFt: number;
    slendernessRatio: number;
  };
  oilRiseVelocityFtS: number;
}

/**
 * Sizes Horizontal and Vertical Skim Vessels for Produced Water
 * Sourced: Arnold & Stewart Chapter 9, Eqs. 9-1a, 9-7a, 9-8a, 9-16a, 9-17a, Ex. 9-2
 */
export function sizeSkimVessels(
  qwBwpd: number,
  apiOil: number,
  sgWater: number = 1.07,
  muWaterCp: number = 1.0,
  dmMicrons: number = 210, // microns to remove
  trMin: number = 10
): SkimVesselSizingResult {
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(sgWater - sgOil);

  // Eq. 9-1a: Stokes rising velocity
  const vo = (1.78e-6 * deltaSG * Math.pow(dmMicrons, 2)) / muWaterCp;

  // 1. Horizontal Skimmer:
  // Eq. 9-7a: d * Leff = 1000 * (Qw * mu_w) / (deltaSG * dm^2)  [includes 1.8 short-circuit factor]
  const dLeffGas = (1000 * qwBwpd * muWaterCp) / (deltaSG * Math.pow(dmMicrons, 2));
  // Eq. 9-8a: d^2 * Leff = 1.4 * tr * Qw
  const d2LeffRet = 1.4 * trMin * qwBwpd;

  // Find standard horizontal diameter (e.g. 48, 60, 72, 84, 96 in.)
  let bestDHoriz = 72;
  let bestLeffHoriz = Math.max(dLeffGas / bestDHoriz, d2LeffRet / Math.pow(bestDHoriz, 2));
  let bestLssHoriz = Math.max((4 / 3) * bestLeffHoriz, bestLeffHoriz + 2.5);

  // 2. Vertical Skimmer:
  // Eq. 9-16a (for d > 48 in.): d = 140 * (Qw * mu_w) / (deltaSG * dm^2)
  const dVert = (140 * qwBwpd * muWaterCp) / (deltaSG * Math.pow(dmMicrons, 2));
  const dVertSelected = Math.max(36, Math.ceil(dVert / 6) * 6);
  // Eq. 9-17a: H = 0.7 * (tr * Qw) / d^2
  const hWaterFt = (0.7 * trMin * qwBwpd) / Math.pow(dVertSelected, 2);
  const lssVertFt = hWaterFt + 3.0; // add 3 ft for inlet and collectors

  return {
    horizontal: {
      diameterInches: bestDHoriz,
      effectiveLengthFt: Math.round(bestLeffHoriz * 10) / 10,
      seamToSeamLengthFt: Math.round(bestLssHoriz * 10) / 10,
      slendernessRatio: Math.round(((12 * bestLssHoriz) / bestDHoriz) * 10) / 10,
    },
    vertical: {
      diameterInches: dVertSelected,
      waterHeightFt: Math.round(hWaterFt * 10) / 10,
      seamToSeamHeightFt: Math.round(lssVertFt * 10) / 10,
      slendernessRatio: Math.round(((12 * lssVertFt) / dVertSelected) * 10) / 10,
    },
    oilRiseVelocityFtS: Math.round(vo * 100000) / 100000,
  };
}

/**
 * Calculates Minimum Droplet Cutoff Diameter (dm) given Number of Packs (Npacks)
 * Sourced: Arnold & Stewart Chapter 9, Eq. 9-20a, Ex. 9-1
 * Inverse problem: dm = sqrt[ factor * Qw * mu_w / (deltaSG * Npacks) ]
 */
export function minDropletFromPacks(
  qwBwpd: number,
  muWaterCp: number,
  deltaSG: number,
  numberOfPacks: number = 1,
  plateAngle: 45 | 60 = 45
): number {
  const factor = plateAngle === 45 ? 0.077 : 0.11;
  const dmCutoff = Math.sqrt((factor * qwBwpd * muWaterCp) / (deltaSG * Math.max(1, numberOfPacks)));
  return Math.round(dmCutoff * 10) / 10;
}

/**
 * Corrugated Plate Interceptor (CPI) Plate Pack Sizing
 * Sourced: Arnold & Stewart Chapter 9, Eqs. 9-20a, 9-21a, Ex. 9-1
 * Direct problem: Finds number of packs needed given target droplet cutoff diameter (dm)
 */
export function sizeCPIPlatePacks(
  qwBwpd: number,
  apiOil: number,
  sgWater: number = 1.06,
  muWaterCp: number = 0.65,
  dmMicrons: number = 63.5,
  plateAngle: 45 | 60 = 45
): {
  requiredPacksExact: number;
  recommendedPacks: number;
  removableCutoffMicrons: number;
} {
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(sgWater - sgOil);

  const factor = plateAngle === 45 ? 0.077 : 0.11;
  const packs = (factor * qwBwpd * muWaterCp) / (deltaSG * Math.pow(dmMicrons, 2));
  // Standard engineering margin: if packs is within 5% of integer (e.g. 1.003), do not mandate an extra pack
  const recommendedPacks = Math.max(1, packs - Math.floor(packs) <= 0.05 ? Math.floor(packs) : Math.ceil(packs));

  const dmCutoff = minDropletFromPacks(qwBwpd, muWaterCp, deltaSG, recommendedPacks, plateAngle);

  return {
    requiredPacksExact: Math.round(packs * 100) / 100,
    recommendedPacks,
    removableCutoffMicrons: dmCutoff,
  };
}

/**
 * Eq. 9-6: Induced Gas Flotation (IGF) Multi-Cell Efficiency
 * Et = 1 - (1 - E)^n
 */
export function gasFlotationEfficiency(
  stageEfficiencyFraction: number = 0.5,
  numberOfCells: number = 4
): {
  overallEfficiencyPercent: number;
  cells: { cellNumber: number; inletPpm: number; outletPpm: number; cumulativeRemovalPercent: number }[];
} {
  const n = Math.max(1, numberOfCells);
  const E = Math.min(0.99, Math.max(0.1, stageEfficiencyFraction));
  const etTotal = 1 - Math.pow(1 - E, n);

  let currentPpm = 200; // typical feed ppm
  const cells = [];
  for (let i = 1; i <= n; i++) {
    const outPpm = currentPpm * (1 - E);
    const cumRem = (1 - outPpm / 200) * 100;
    cells.push({
      cellNumber: i,
      inletPpm: Math.round(currentPpm),
      outletPpm: Math.round(outPpm),
      cumulativeRemovalPercent: Math.round(cumRem * 10) / 10,
    });
    currentPpm = outPpm;
  }

  return {
    overallEfficiencyPercent: Math.round(etTotal * 1000) / 10,
    cells,
  };
}

/**
 * Eqs. 9-26a, 9-27a: Offshore Disposal Pile Sizing
 * Handles produced water plus rainwater or deck washdown
 */
export function sizeDisposalPile(
  qwBwpd: number,
  deckAreaSqFt: number = 2500,
  rainfallRateInHr: number = 2.0, // GOM standard
  washdownHoses: number = 2,
  apiOil: number = 30,
  tideRangeFt: number = 5.0,
  stormSurgeFt: number = 10.0
): {
  rainwaterRateBwpd: number;
  washdownRateBwpd: number;
  designDiameterInches: number;
  standardPipeSizeInches: number;
  submergedLengthFt: number;
} {
  const sgOil = apiToSG(apiOil);
  const deltaSG = Math.abs(1.0 - sgOil); // rain / deck water ~ fresh water 1.0

  const rainwaterRate = 0.356 * deckAreaSqFt * rainfallRateInHr;
  const washdownRate = 1500 * washdownHoses;
  const deckFlowBwpd = Math.max(rainwaterRate, washdownRate);

  // Eq. 9-26a: d^2 = 0.3 * (Qw + Q_drain) / deltaSG
  const d2 = (0.3 * (qwBwpd + deckFlowBwpd)) / deltaSG;
  const dCalc = Math.sqrt(d2);

  // Standard disposal pile pipe diameters (typically 24, 30, 36, 42, 48 inches)
  const standardPipes = [24, 30, 36, 42, 48, 54, 60];
  const standardSize = standardPipes.find((p) => p >= dCalc) || 48;

  // Eq. 9-27a: L = [(HT + HS + HA + HSD) * SGo] / deltaSG + 10
  const sumSurge = tideRangeFt + stormSurgeFt + 2.0 + 2.0; // HA=2 ft, HSD=2 ft
  const lengthSubmerged = (sumSurge * sgOil) / deltaSG + 10;

  return {
    rainwaterRateBwpd: Math.round(rainwaterRate),
    washdownRateBwpd: washdownRate,
    designDiameterInches: Math.round(dCalc * 10) / 10,
    standardPipeSizeInches: standardSize,
    submergedLengthFt: Math.round(lengthSubmerged * 10) / 10,
  };
}

/**
 * Chapter 10: Filtration Beta Ratio & Removal Efficiency
 * Beta_x = N_in / N_out
 * % Removal = [(Beta - 1) / Beta] * 100
 */
export function filterBetaEfficiency(betaRatio: number): {
  removalEfficiencyPercent: number;
  isAbsoluteRating: boolean;
} {
  const beta = Math.max(1, betaRatio);
  const eff = ((beta - 1) / beta) * 100;
  return {
    removalEfficiencyPercent: Math.round(eff * 100) / 100,
    isAbsoluteRating: beta >= 5000,
  };
}

/**
 * Eq. 10-19a: Oxygen Chemical Scavenger Injection Rate (lb/day)
 * W_cs = 1.09e-5 * Qw * SGw * C_O2 * R * MW_cs
 * with sodium bisulfite (NaHSO3, MW=104, R=2) or ammonium bisulfite
 */
export function oxygenScavengerRateLbDay(
  qwBwpd: number,
  sgWater: number = 1.05,
  dissolvedOxygenPpm: number = 8.0, // typical 8 ppm in seawater
  reactionRatioR: number = 2.0,
  mwScavenger: number = 104 // Sodium bisulfite
): {
  scavengerRateLbDay: number;
  catalystCobaltRateLbDay: number;
} {
  // Eq. 10-19a
  const wcs = 1.09e-5 * qwBwpd * sgWater * dissolvedOxygenPpm * reactionRatioR * mwScavenger;
  // Eq. 10-20a: Wc = 7.7e-7 * Qw * SGw * C_ca (with C_ca = 0.001 ppm)
  const wc = 7.7e-7 * qwBwpd * sgWater * 0.001;

  return {
    scavengerRateLbDay: Math.round(wcs * 10) / 10,
    catalystCobaltRateLbDay: Math.round(wc * 1000) / 1000,
  };
}

/**
 * Table 10-2 & Fig. 10-4: Langelier Saturation Index (LSI) & Ryznar Stability Index (RSI)
 * RSI = 2 * pHs - pHA
 * LSI = pHA - pHs
 */
export function calculateWaterScalingIndices(
  actualPh: number, // pHA
  calciumHardnessPpm: number,
  mAlkalinityPpm: number,
  totalSolidsPpm: number,
  tempF: number
): {
  pCa: number;
  pAlk: number;
  cFactor: number;
  saturationPhS: number;
  langelierIndexLSI: number;
  ryznarIndexRSI: number;
  scalingTendency: "Severe Scaling" | "Moderate Scaling" | "Stable Water" | "Corrosive";
} {
  // Analytical approximation of Fig. 10-4 nomograph
  const pCa = 5.0 - Math.log10(Math.max(1, calciumHardnessPpm));
  const pAlk = 5.0 - Math.log10(Math.max(1, mAlkalinityPpm));

  // Temperature and TDS C-factor
  const cFactor =
    (Math.log10(Math.max(10, totalSolidsPpm)) - 1) / 10 +
    (tempF > 100 ? 1.5 + (tempF - 100) * 0.008 : 1.2 + (tempF - 50) * 0.006);

  const phS = pCa + pAlk + cFactor;
  const lsi = actualPh - phS;
  const rsi = 2 * phS - actualPh;

  let tendency: "Severe Scaling" | "Moderate Scaling" | "Stable Water" | "Corrosive" = "Stable Water";
  if (rsi < 5.5) {
    tendency = "Severe Scaling";
  } else if (rsi < 6.5) {
    tendency = "Moderate Scaling";
  } else if (rsi <= 7.5) {
    tendency = "Stable Water";
  } else {
    tendency = "Corrosive";
  }

  return {
    pCa: Math.round(pCa * 100) / 100,
    pAlk: Math.round(pAlk * 100) / 100,
    cFactor: Math.round(cFactor * 100) / 100,
    saturationPhS: Math.round(phS * 100) / 100,
    langelierIndexLSI: Math.round(lsi * 100) / 100,
    ryznarIndexRSI: Math.round(rsi * 100) / 100,
    scalingTendency: tendency,
  };
}
