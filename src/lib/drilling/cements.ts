/**
 * Cementing Engineering Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 3.
 */

import { CAPACITY_CONSTANT } from '../math/constants';
import { API_CEMENT_CLASSES, CementClass } from '../math/tables';

export interface BogueComposition {
  c3s: number;  // Tricalcium Silicate (alite) - early strength
  c2s: number;  // Dicalcium Silicate (belite) - final strength
  c3a: number;  // Tricalcium Aluminate - hydration rate & sulfate susceptibility
  c4af: number; // Tetracalcium Aluminoferrite - flux & heat of hydration reducer
}

/**
 * 3.1 Bogue Equations for Compound Composition from Oxides (wt %)
 * Sourced: Bourgoyne Ch. 3, Eq. 3.1 - 3.4
 */
export function bogueCompoundsFromOxides(
  caoPct: number,
  sio2Pct: number,
  al2o3Pct: number,
  fe2o3Pct: number,
  so3Pct: number
): BogueComposition {
  const c3s = 4.07 * caoPct - 7.60 * sio2Pct - 6.72 * al2o3Pct - 1.43 * fe2o3Pct - 2.85 * so3Pct;
  const c2s = 2.87 * sio2Pct - 0.754 * c3s;
  const c3a = 2.65 * al2o3Pct - 1.69 * fe2o3Pct;
  const c4af = 3.04 * fe2o3Pct;

  return {
    c3s: Math.round(Math.max(0, c3s) * 10) / 10,
    c2s: Math.round(Math.max(0, c2s) * 10) / 10,
    c3a: Math.round(Math.max(0, c3a) * 10) / 10,
    c4af: Math.round(Math.max(0, c4af) * 10) / 10,
  };
}

/**
 * 3.2 Consistency in Bearden units (Bc) from Consistometer torque (g-cm)
 * Sourced: Bourgoyne Ch. 3, Eq. 3.5: Bc = (Torque - 78.2) / 20.02
 */
export function slurryConsistencyBc(torqueGCm: number): number {
  const bc = (torqueGCm - 78.2) / 20.02;
  return Math.round(Math.max(0, bc) * 10) / 10;
}

/**
 * Permeability of set cement core via Darcy equation (md)
 * Sourced: Bourgoyne Ch. 3, Eq. 3.6
 * k = (14700 * q * mu * L) / (A * deltaP)
 */
export function cementPermeabilityDarcy(
  flowRateMlPerSec: number,
  viscosityCp: number,
  coreLengthCm: number,
  coreAreaCm2: number,
  pressureDropPsi: number
): number {
  if (coreAreaCm2 <= 0 || pressureDropPsi <= 0) return 0;
  const k = (14700 * flowRateMlPerSec * viscosityCp * coreLengthCm) / (coreAreaCm2 * pressureDropPsi);
  return Math.round(k * 1000) / 1000;
}

export interface SlurryAdditive {
  name: string;
  pctByWeightOfCement: number; // % BWOC
  specificGravity: number;
  waterRequirementGalPerLb: number; // gal water required per lb additive
}

export interface SlurryDesignResult {
  apiClass: string;
  slurryDensityPpg: number;
  slurryYieldFt3Sack: number;
  waterGallonsPerSack: number;
  mixWaterPercent: number; // % BWOC
}

/**
 * 3.3 Slurry Yield & Density from Additives and Absolute Volumes
 * Sourced: Bourgoyne Ch. 3, Example 3.3 - 3.5
 * Standard API cement sack = 94 lbm. Cement absolute volume = 94 / (3.14 * 62.3) = 0.478 ft3/sk.
 */
export function designCementSlurry(
  cementClassKey: 'Class A' | 'Class C' | 'Class G' | 'Class H' = 'Class G',
  additives: SlurryAdditive[] = [],
  customWaterGalPerSack?: number
): SlurryDesignResult {
  const cementRef = API_CEMENT_CLASSES[cementClassKey] || API_CEMENT_CLASSES['Class G'];
  const cementWeightLbm = 94.0;
  const cementSpecificGravity = 3.14;
  const cementVolFt3 = cementWeightLbm / (cementSpecificGravity * 62.37); // 0.478 ft3

  // Base water requirement
  let waterGal = customWaterGalPerSack !== undefined
    ? customWaterGalPerSack
    : (cementWeightLbm * (cementRef.waterReqPct / 100)) / 8.33;

  let totalMassLbm = cementWeightLbm;
  let totalVolumeFt3 = cementVolFt3;

  for (const add of additives) {
    const addMassLbm = (cementWeightLbm * add.pctByWeightOfCement) / 100;
    const addVolFt3 = addMassLbm / (add.specificGravity * 62.37);
    const extraWaterGal = addMassLbm * add.waterRequirementGalPerLb;

    totalMassLbm += addMassLbm;
    totalVolumeFt3 += addVolFt3;
    if (customWaterGalPerSack === undefined) {
      waterGal += extraWaterGal;
    }
  }

  // Add water mass and volume (1 gal water = 8.33 lbm = 0.13368 ft3)
  const waterMassLbm = waterGal * 8.33;
  const waterVolFt3 = waterGal / 7.4805;

  totalMassLbm += waterMassLbm;
  totalVolumeFt3 += waterVolFt3;

  const yieldFt3Sack = totalVolumeFt3;
  const densityPpg = totalMassLbm / (yieldFt3Sack * 7.4805);
  const mixWaterPct = (waterMassLbm / cementWeightLbm) * 100;

  return {
    apiClass: cementClassKey,
    slurryDensityPpg: Math.round(densityPpg * 10) / 10,
    slurryYieldFt3Sack: Math.round(yieldFt3Sack * 100) / 100,
    waterGallonsPerSack: Math.round(waterGal * 10) / 10,
    mixWaterPercent: Math.round(mixWaterPct * 10) / 10,
  };
}

/**
 * 3.4 Weighting & Extending Additive Calculations for Target Slurry Density
 * Sourced: Bourgoyne Ch. 3, Example 3.5
 * Returns the % BWOC of additive needed to reach target density.
 */
export function additiveForTargetDensity(
  cementClassKey: 'Class G' | 'Class H',
  targetDensityPpg: number,
  additiveType: 'bentonite' | 'hematite' | 'barite' | 'sand'
): { pctBWOC: number; expectedYieldFt3Sk: number; waterGalSk: number } {
  // Solve: (M_cem + M_add + M_water) / (7.4805 * (V_cem + V_add + V_water)) = targetRho
  const params = {
    bentonite: { sg: 2.65, waterGalLb: 0.65 },
    hematite: { sg: 5.05, waterGalLb: 0.02 },
    barite: { sg: 4.23, waterGalLb: 0.02 },
    sand: { sg: 2.65, waterGalLb: 0.0 },
  }[additiveType];

  // Numerical search for target pctBWOC
  let bestPct = 0;
  let minDiff = 999;
  for (let pct = 0; pct <= 40; pct += 0.5) {
    const res = designCementSlurry(cementClassKey, [
      { name: additiveType, pctByWeightOfCement: pct, specificGravity: params.sg, waterRequirementGalPerLb: params.waterGalLb }
    ]);
    const diff = Math.abs(res.slurryDensityPpg - targetDensityPpg);
    if (diff < minDiff) {
      minDiff = diff;
      bestPct = pct;
    }
  }

  const finalRes = designCementSlurry(cementClassKey, [
    { name: additiveType, pctByWeightOfCement: bestPct, specificGravity: params.sg, waterRequirementGalPerLb: params.waterGalLb }
  ]);

  return {
    pctBWOC: bestPct,
    expectedYieldFt3Sk: finalRes.slurryYieldFt3Sack,
    waterGalSk: finalRes.waterGallonsPerSack,
  };
}

/**
 * 3.5 Cement Job Volume and Displacement Time Planning
 * Sourced: Bourgoyne Ch. 3, Section 3.6
 */
export interface CementJobPlanResult {
  annularVolumeFt3: number;
  annularVolumeBbl: number;
  shoeTrackVolumeFt3: number;
  totalSlurryVolumeFt3: number;
  totalSlurryVolumeBbl: number;
  sacksRequired: number;
  mixingTimeMinutes: number;
  displacementVolumeBbl: number;
  displacementTimeMinutes: number;
  totalJobTimeMinutes: number;
}

export function planCementJob(
  holeDiameterIn: number,
  casingOdIn: number,
  casingIdIn: number,
  cementIntervalLengthFt: number,
  shoeTrackLengthFt: number,
  excessFactor: number = 1.25, // 25% excess
  slurryYieldFt3Sk: number = 1.15,
  mixingRateSacksPerMin: number = 30,
  displacementPumpRateBpm: number = 6.0,
  totalCasingLengthFt: number = 8000
): CementJobPlanResult {
  // Annular capacity in ft3/ft: (Dh^2 - Dp^2) * pi / (4 * 144) = (Dh^2 - Dp^2) * 0.005454
  const annularCapFt3Ft = ((Math.pow(holeDiameterIn, 2) - Math.pow(casingOdIn, 2)) * Math.PI) / 576;
  const annularVolFt3 = annularCapFt3Ft * cementIntervalLengthFt * excessFactor;

  // Shoe track volume (between float collar and casing guide shoe)
  const casingCapFt3Ft = (Math.pow(casingIdIn, 2) * Math.PI) / 576;
  const shoeTrackVolFt3 = casingCapFt3Ft * shoeTrackLengthFt;

  const totalSlurryFt3 = annularVolFt3 + shoeTrackVolFt3;
  const totalSlurryBbl = totalSlurryFt3 * 0.1781;
  const sacks = Math.ceil(totalSlurryFt3 / Math.max(0.1, slurryYieldFt3Sk));

  // Mixing time
  const mixingMin = Math.ceil(sacks / Math.max(1, mixingRateSacksPerMin));

  // Displacement volume: inside casing above float collar
  const displacementDepthFt = Math.max(0, totalCasingLengthFt - shoeTrackLengthFt);
  const casingCapBblFt = Math.pow(casingIdIn, 2) / CAPACITY_CONSTANT;
  const dispVolBbl = displacementDepthFt * casingCapBblFt;

  // Displacement time
  const dispMin = Math.ceil(dispVolBbl / Math.max(0.1, displacementPumpRateBpm));

  return {
    annularVolumeFt3: Math.round(annularVolFt3),
    annularVolumeBbl: Math.round(annularVolFt3 * 0.1781 * 10) / 10,
    shoeTrackVolumeFt3: Math.round(shoeTrackVolFt3 * 10) / 10,
    totalSlurryVolumeFt3: Math.round(totalSlurryFt3),
    totalSlurryVolumeBbl: Math.round(totalSlurryBbl * 10) / 10,
    sacksRequired: sacks,
    mixingTimeMinutes: mixingMin,
    displacementVolumeBbl: Math.round(dispVolBbl * 10) / 10,
    displacementTimeMinutes: dispMin,
    totalJobTimeMinutes: mixingMin + dispMin,
  };
}

/**
 * 3.6 Cement Additives Recommendation Advisor
 * Based on Bourgoyne Ch. 3, Tables 3.8 - 3.11
 */
export interface AdditiveRecommendation {
  category: 'Accelerator' | 'Retarder' | 'Weighting' | 'Extender' | 'Fluid Loss';
  name: string;
  dosage: string;
  reason: string;
}

export function recommendCementAdditives(
  bottomHoleTempF: number,
  targetDensityPpg: number,
  formationWaterSensitive: boolean
): AdditiveRecommendation[] {
  const recs: AdditiveRecommendation[] = [];

  // Accelerator / Retarder logic
  if (bottomHoleTempF < 120) {
    recs.push({
      category: 'Accelerator',
      name: 'Calcium Chloride (CaCl2)',
      dosage: '1.5% - 2.0% BWOC',
      reason: 'Low bottom-hole temperature (<120°F) requires acceleration to prevent excessively long WOC (Waiting On Cement) time.',
    });
  } else if (bottomHoleTempF > 170) {
    recs.push({
      category: 'Retarder',
      name: 'Lignosulfonate / Calcium Lignosulfonate',
      dosage: '0.2% - 0.6% BWOC',
      reason: 'High bottom-hole temperature (>170°F) accelerates hydration; retarder ensures adequate thickening time for pumpability.',
    });
  }

  // Density control
  if (targetDensityPpg > 16.5) {
    recs.push({
      category: 'Weighting',
      name: 'Hematite (Fe2O3) or Ilmenite',
      dosage: '10% - 30% BWOC',
      reason: `Target density of ${targetDensityPpg} ppg exceeds neat cement capability; dense mineral additive required.`,
    });
  } else if (targetDensityPpg < 14.5) {
    recs.push({
      category: 'Extender',
      name: 'Bentonite or Pozzolan',
      dosage: '2% - 8% BWOC',
      reason: `Lightweight slurry (${targetDensityPpg} ppg) needed to avoid exceeding low fracture gradients in weak formations.`,
    });
  }

  // Fluid loss
  if (formationWaterSensitive || bottomHoleTempF > 150) {
    recs.push({
      category: 'Fluid Loss',
      name: 'Cellulose derivative / Hydroxyethyl cellulose (HEC)',
      dosage: '0.5% - 1.0% BWOC',
      reason: 'Controls filtrate loss into permeable zones, prevents slurry dehydration and gas channeling.',
    });
  }

  return recs;
}
