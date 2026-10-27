/**
 * Drilling Fluids Engineering Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 2.
 */

import { SALT_WATER_ACTIVITY } from '../math/tables';

export interface FannRheologyResult {
  apparentViscosityCp: number;   // mu_a = 300 * theta_N / N
  plasticViscosityCp: number;    // mu_p = theta_600 - theta_300
  yieldPointLbf100ft2: number;   // tau_y = theta_300 - mu_p
  powerLawN: number;             // n = 3.32 * log10(theta_600 / theta_300)
  powerLawK: number;             // K = 510 * theta_300 / 511^n (eq cP)
  flowBehavior: 'Newtonian' | 'Bingham Plastic' | 'Pseudoplastic (Power-Law)';
}

/**
 * 2.1 Rheology from Fann 35 rotational viscometer readings
 * Sourced: Bourgoyne Ch. 2, Eq. 2.1 - 2.5
 */
export function calculateFannRheology(
  theta600: number,
  theta300: number,
  theta200?: number,
  theta100?: number,
  theta6?: number,
  theta3?: number
): FannRheologyResult {
  const t600 = Math.max(0.1, theta600);
  const t300 = Math.max(0.1, theta300);

  const muP = Math.max(0, t600 - t300);
  const tauY = Math.max(0, t300 - muP);
  const muA = t600 / 2; // Apparent viscosity at 600 rpm: 300 * theta600 / 600

  // Power-law index n and consistency index K
  const n = 3.3219 * Math.log10(t600 / t300);
  // Shear rate for 300 rpm in standard Fann 35 is 511 sec^-1
  const K = (510 * t300) / Math.pow(511, Math.max(0.01, n));

  let flowBehavior: 'Newtonian' | 'Bingham Plastic' | 'Pseudoplastic (Power-Law)' = 'Pseudoplastic (Power-Law)';
  if (tauY <= 1 && Math.abs(n - 1.0) < 0.05) {
    flowBehavior = 'Newtonian';
  } else if (tauY > 0 && n > 0.85) {
    flowBehavior = 'Bingham Plastic';
  }

  return {
    apparentViscosityCp: Math.round(muA * 10) / 10,
    plasticViscosityCp: Math.round(muP * 10) / 10,
    yieldPointLbf100ft2: Math.round(tauY * 10) / 10,
    powerLawN: Math.round(n * 1000) / 1000,
    powerLawK: Math.round(K * 10) / 10,
    flowBehavior,
  };
}

/**
 * Apparent viscosity at any rotational speed N
 * mu_a = 300 * theta_N / N
 */
export function apparentViscosity(thetaN: number, rpm: number): number {
  if (rpm <= 0) return 0;
  return Math.round(((300 * thetaN) / rpm) * 10) / 10;
}

/**
 * 2.2 Chemistry & pH
 * Sourced: Bourgoyne Ch. 2, Eq. 2.6
 */
export function hConcFromPH(pH: number): number {
  return Math.pow(10, -pH);
}

export function ohConcFromPH(pH: number): number {
  return Math.pow(10, pH - 14);
}

export function pHFromH(hConc: number): number {
  if (hConc <= 0) return 14;
  return Math.round(-Math.log10(hConc) * 100) / 100;
}

/**
 * Caustic soda (NaOH) required to raise pH of mud system
 * Sourced: Bourgoyne Ch. 2, Example 2.2
 * Returns grams of NaOH needed
 */
export function causticToRaisePH(volLiters: number, initialPH: number, targetPH: number): number {
  if (targetPH <= initialPH) return 0;
  const ohInitial = ohConcFromPH(initialPH);
  const ohTarget = ohConcFromPH(targetPH);
  const deltaOHMoles = (ohTarget - ohInitial) * volLiters;
  // NaOH molar mass = 40.0 g/mol
  return Math.round(deltaOHMoles * 40.0 * 100) / 100;
}

/**
 * 2.3 Filtration Analysis (API Standard Filter Press)
 * Sourced: Bourgoyne Ch. 2, Eq. 2.7 - 2.11
 * V30 = 2 * (V7.5 - Vsp) + Vsp = 2 * V7.5 - Vsp
 */
export function apiWaterLossFrom75(v75Cm3: number, vSpurtCm3: number): number {
  const v30 = 2 * (v75Cm3 - vSpurtCm3) + vSpurtCm3;
  return Math.round(Math.max(0, v30) * 10) / 10;
}

/**
 * Spurt loss determination by extrapolating cumulative filtrate volume vs sqrt(time in min)
 */
export function spurtLossFromPlot(v1: number, t1Min: number, v2: number, t2Min: number): number {
  const sqrt1 = Math.sqrt(t1Min);
  const sqrt2 = Math.sqrt(t2Min);
  if (Math.abs(sqrt2 - sqrt1) < 1e-4) return 0;
  const slope = (v2 - v1) / (sqrt2 - sqrt1);
  const intercept = v1 - slope * sqrt1;
  return Math.round(Math.max(0, intercept) * 100) / 100;
}

/**
 * HTHP Filter Press conversion to standard API area (HTHP cell is 1/2 area of API cell -> x 2)
 */
export function hthpToApiWaterLoss(v30HthpCm3: number): number {
  return Math.round(v30HthpCm3 * 2 * 10) / 10;
}

/**
 * 2.4 Chemical Analysis of Drilling Fluids
 * Sourced: Bourgoyne Ch. 2, Eq. 2.12 - 2.15
 */
export function chlorideMgL(vTitrationMl: number): number {
  return Math.round(1000 * vTitrationMl);
}

export function naclMgL(vTitrationMl: number): number {
  return Math.round(1650 * vTitrationMl);
}

/**
 * Free lime in lbm/bbl
 * Sourced: Bourgoyne Ch. 2, Eq. 2.14: 0.26 * (Pm - fw * Pf)
 */
export function freeLimeLbmBbl(Pm: number, Pf: number, fw: number): number {
  const lime = 0.26 * (Pm - fw * Pf);
  return Math.round(Math.max(0, lime) * 100) / 100;
}

/**
 * Total and Free Calcium Sulfate (CaSO4) in lbm/bbl
 * Sourced: Bourgoyne Ch. 2, Eq. 2.15
 */
export function caso4TotalLbmBbl(vTm: number): number {
  return Math.round(0.477 * vTm * 100) / 100;
}

export function caso4FreeLbmBbl(vTm: number, vTf: number, fw: number): number {
  const free = 0.477 * (vTm - fw * vTf);
  return Math.round(Math.max(0, free) * 100) / 100;
}

/**
 * Montmorillonite clay content from Methylene Blue Test (MBT / CEC)
 * Sourced: Bourgoyne Ch. 2, Eq. 2.16: Clay (lbm/bbl) = 5 * CEC
 */
export function montmorilloniteLbmBbl(cecMeq100g: number): number {
  return Math.round(5 * cecMeq100g * 10) / 10;
}

/**
 * 2.5 Retort Analysis (Solids, Oil, Water fractions)
 * Sourced: Bourgoyne Ch. 2, Eq. 2.17 - 2.21
 */
export interface RetortResult {
  waterFraction: number;
  oilFraction: number;
  totalSolidsFraction: number;
  lowGravitySolidsFraction: number;
  bariteFraction: number;
  averageSolidsSpecificGravity: number;
}

export function retortAnalysis(
  mudWeightPpg: number,
  waterVolPct: number,
  oilVolPct: number,
  salinityPpm: number = 0,
  rhoBaritePpg: number = 35.0, // 4.2 SG = 35.05 ppg
  rhoLgPpg: number = 21.7       // 2.6 SG = 21.70 ppg
): RetortResult {
  const fw = waterVolPct / 100;
  const fo = oilVolPct / 100;

  // Salt correction factor Cf for brine density
  const Cf = 1.0 + (salinityPpm / 1000000) * 0.7;
  const fs = Math.max(0, 1.0 - fw * Cf - fo);

  const rhoW = 8.33 * Cf;
  const rhoO = 6.67; // typical diesel / mineral oil base

  // Average solids density
  const solidsWeightPpg = mudWeightPpg - fw * rhoW - fo * rhoO;
  const rhoS = fs > 0 ? solidsWeightPpg / fs : rhoLgPpg;

  // Split into Barite and Low Gravity Solids (Bourgoyne Eq. 2.20)
  const denom = Math.max(0.1, rhoBaritePpg - rhoLgPpg);
  const fB = Math.max(0, Math.min(fs, (solidsWeightPpg - fs * rhoLgPpg) / denom));
  const fLg = Math.max(0, fs - fB);

  return {
    waterFraction: Math.round(fw * 1000) / 1000,
    oilFraction: Math.round(fo * 1000) / 1000,
    totalSolidsFraction: Math.round(fs * 1000) / 1000,
    lowGravitySolidsFraction: Math.round(fLg * 1000) / 1000,
    bariteFraction: Math.round(fB * 1000) / 1000,
    averageSolidsSpecificGravity: Math.round((rhoS / 8.33) * 100) / 100,
  };
}

/**
 * 2.6 Mud Weighting Up (Ideal Mixing Equations)
 * Sourced: Bourgoyne Ch. 2, Eq. 2.22 - 2.25
 */
export interface WeightUpResult {
  bariteSacksRequired: number;  // 100-lbm sacks
  bariteTotalLbm: number;
  finalVolumeBbl: number;
  volumeIncreaseBbl: number;
  oldMudToDiscardBbl?: number; // if target final volume was constrained
}

/**
 * Barite required to increase mud weight from rho1 to rho2
 * Sourced: Bourgoyne Ch. 2, Eq. 2.22
 * B = 350 * V1 * (rho2 - rho1) / (rhoB - rho2)
 */
export function bariteRequired(
  v1Bbl: number,
  rho1Ppg: number,
  rho2Ppg: number,
  rhoBaritePpg: number = 35.0
): WeightUpResult {
  if (rho2Ppg <= rho1Ppg) {
    return { bariteSacksRequired: 0, bariteTotalLbm: 0, finalVolumeBbl: v1Bbl, volumeIncreaseBbl: 0 };
  }
  const denom = Math.max(0.1, rhoBaritePpg - rho2Ppg);
  const lbm = (350 * v1Bbl * (rho2Ppg - rho1Ppg)) / denom;
  const volIncBbl = lbm / (350 * (rhoBaritePpg / 8.33 * 8.33)); // Barite volume: lbm / (4.2 * 350) = lbm / 1470
  const finalVol = v1Bbl + (lbm / (rhoBaritePpg * 42));

  return {
    bariteSacksRequired: Math.ceil(lbm / 100),
    bariteTotalLbm: Math.round(lbm),
    finalVolumeBbl: Math.round(finalVol * 10) / 10,
    volumeIncreaseBbl: Math.round((finalVol - v1Bbl) * 10) / 10,
  };
}

/**
 * Weighting up with fixed final volume (must discard some initial mud to make room for barite)
 * Sourced: Bourgoyne Ch. 2, Eq. 2.24 - 2.25
 */
export function weightUpFixedFinalVolume(
  finalTargetVolumeBbl: number,
  rho1Ppg: number,
  rho2Ppg: number,
  rhoBaritePpg: number = 35.0
): { bariteTotalLbm: number; sacks: number; initialMudToKeepBbl: number; oldMudToDiscardBbl: number } {
  const denom = Math.max(0.1, rhoBaritePpg - rho1Ppg);
  const v1Keep = (finalTargetVolumeBbl * (rhoBaritePpg - rho2Ppg)) / denom;
  const discard = Math.max(0, finalTargetVolumeBbl - v1Keep);
  const lbm = (350 * v1Keep * (rho2Ppg - rho1Ppg)) / (rhoBaritePpg - rho2Ppg);

  return {
    bariteTotalLbm: Math.round(lbm),
    sacks: Math.ceil(lbm / 100),
    initialMudToKeepBbl: Math.round(v1Keep * 10) / 10,
    oldMudToDiscardBbl: Math.round(discard * 10) / 10,
  };
}

/**
 * 2.7 Centrifuge Analysis for Solids Control
 * Sourced: Bourgoyne Ch. 2, Eq. 2.26 - 2.32
 */
export function centrifugeUnderflowRate(
  mudFeedGpm: number,
  waterDilutionGpm: number,
  rhoMudFeedPpg: number,
  rhoUnderflowPpg: number,
  rhoOverflowPpg: number,
  rhoWaterPpg: number = 8.33
): number {
  const num = mudFeedGpm * (rhoMudFeedPpg - rhoOverflowPpg) + waterDilutionGpm * (rhoWaterPpg - rhoOverflowPpg);
  const denom = Math.max(0.1, rhoUnderflowPpg - rhoOverflowPpg);
  return Math.round((num / denom) * 10) / 10;
}

/**
 * 2.8 Chemical Treatment for Contaminants
 * Sourced: Bourgoyne Ch. 2, Treatment Tables
 */
export function sodaAshForCalcium(deltaCaMgL: number, systemVolBbl: number): number {
  // 0.000928 lbm soda ash per (mg/L Ca * bbl mud)
  return Math.round(0.000928 * deltaCaMgL * systemVolBbl * 10) / 10;
}

export function sappForCement(deltaCaMgL: number, systemVolBbl: number): number {
  // Sodium Acid Pyrophosphate: 0.000971 lbm per (mg/L * bbl)
  return Math.round(0.000971 * deltaCaMgL * systemVolBbl * 10) / 10;
}

export function sodiumBicarbForCement(deltaCaMgL: number, systemVolBbl: number): number {
  // Sodium Bicarbonate: 0.00147 lbm per (mg/L * bbl)
  return Math.round(0.00147 * deltaCaMgL * systemVolBbl * 10) / 10;
}

export function causticForMagnesium(deltaMgMgL: number, systemVolBbl: number): number {
  // Caustic Soda for Mg removal: 0.00116 lbm per (mg/L * bbl)
  return Math.round(0.00116 * deltaMgMgL * systemVolBbl * 10) / 10;
}

/**
 * 2.9 Inhibitive Shale & Water Activity
 * Sourced: Bourgoyne Ch. 2, Eq. 2.42
 * Shale adsorptive pressure: P_s = -(R * T / V_w) * ln(a_w_mud / a_w_shale)
 */
export function shaleAdsorptivePressure(
  mudActivity: number,
  shaleActivity: number,
  tempRankine: number = 540 // ~80 °F
): number {
  if (mudActivity <= 0 || shaleActivity <= 0) return 0;
  // R = 10.73 psi * ft3 / (lbm-mol * °R), Vw = 0.288 ft3 / lbm-mol
  // R / Vw = 37.26 psi / °R
  const factor = 37.26 * tempRankine;
  const ratio = Math.max(0.01, mudActivity / shaleActivity);
  const p = -factor * Math.log(ratio);
  return Math.round(p);
}

/**
 * Barite specific gravity field test
 * Sourced: Carter Ch. 4, Eq. 4.1
 */
export function bariteSpecificGravityField(dWeightGram: number, vWaterAddedMl: number): number {
  return dWeightGram / (100 - vWaterAddedMl);
}

/**
 * Increase mud weight short formula
 * Sourced: Carter Ch. 4, Eqs. 4.2–4.3
 */
export function increaseMudWeight_field(pOldPpg: number, pNewPpg: number): { sacksPer100Bbl: number; volumeIncreaseBblPer100Bbl: number } {
  const sacks = (1470 * (pNewPpg - pOldPpg)) / (35.0 - pNewPpg);
  const volInc = sacks / 14.7;
  return {
    sacksPer100Bbl: Math.round(sacks),
    volumeIncreaseBblPer100Bbl: Math.round(volInc * 10) / 10,
  };
}

/**
 * Increase mud weight long formula with custom SG
 * Sourced: Carter Ch. 4, Eqs. 4.4–4.5
 */
export function increaseMudWeight_long(pOldPpg: number, pNewPpg: number, sgWeightMat: number = 4.2): { sacksPer100Bbl: number; volumeIncreaseBblPer100Bbl: number } {
  const rhoWm = sgWeightMat * 8.34;
  const sacks = (350 * 100 * (pNewPpg - pOldPpg)) / (rhoWm - pNewPpg);
  const volInc = (sacks * 100) / (sgWeightMat * 350);
  return {
    sacksPer100Bbl: Math.round(sacks),
    volumeIncreaseBblPer100Bbl: Math.round(volInc * 10) / 10,
  };
}

/**
 * Increase mud weight for limited system volume
 * Sourced: Carter Ch. 4, Eqs. 4.6–4.7
 */
export function increaseMudWeight_limitedVolume(pOldPpg: number, pNewPpg: number, vFinalBbl: number, sgWeightMat: number = 4.2): { startVolumeBbl: number; sacks: number } {
  const rhoWm = sgWeightMat * 8.34;
  const vStart = vFinalBbl * ((rhoWm - pNewPpg) / (rhoWm - pOldPpg));
  const sacks = (350 * vStart * (pNewPpg - pOldPpg)) / (rhoWm - pNewPpg);
  return {
    startVolumeBbl: Math.round(vStart * 10) / 10,
    sacks: Math.round(sacks),
  };
}

/**
 * Increase mud weight with liquid addition for wetting
 * Sourced: Carter Ch. 4, Eqs. 4.8–4.11
 */
export function increaseMudWeight_withLiquid(pOldPpg: number, pNewPpg: number, vStartBbl: number, sgWeightMat: number = 4.2, liquidBblPer100Sacks: number = 2.0): { sacks: number; wettingLiquidBbl: number; finalVolumeBbl: number } {
  const rhoWm = sgWeightMat * 8.34;
  const sacks = (350 * vStartBbl * (pNewPpg - pOldPpg)) / (rhoWm - pNewPpg);
  const vWetting = (sacks / 100) * liquidBblPer100Sacks;
  const vFinal = vStartBbl + (sacks * 100) / (sgWeightMat * 350) + vWetting;
  return {
    sacks: Math.round(sacks),
    wettingLiquidBbl: Math.round(vWetting * 10) / 10,
    finalVolumeBbl: Math.round(vFinal * 10) / 10,
  };
}

/**
 * Increase mud weight for limited final volume with liquid
 * Sourced: Carter Ch. 4, Eqs. 4.9, 4.12–4.15
 */
export function increaseMudWeight_limitedFinalV(pOldPpg: number, pNewPpg: number, vFinalBbl: number, sgWeightMat: number = 4.2, liquidBblPer100Sacks: number = 2.0): { startVolumeBbl: number; sacks: number; wettingLiquidBbl: number } {
  const rhoWm = sgWeightMat * 8.34;
  const vStart = vFinalBbl * ((rhoWm - pNewPpg) / (rhoWm - pOldPpg));
  const res = increaseMudWeight_withLiquid(pOldPpg, pNewPpg, vStart, sgWeightMat, liquidBblPer100Sacks);
  return {
    startVolumeBbl: Math.round(vStart * 10) / 10,
    sacks: res.sacks,
    wettingLiquidBbl: res.wettingLiquidBbl,
  };
}

/**
 * Increase mud weight with limited inventory
 * Sourced: Carter Ch. 4, Eqs. 4.16–4.18
 */
export function increaseMudWeight_limitedInventory(weightMaterialInventorySacks: number, pOldPpg: number, pNewPpg: number, vPitCapacityBbl: number, sgWeightMat: number = 4.2, liquidBblPer100Sacks: number = 2.0): { startVolumeBbl: number; discardVolumeBbl: number; finalVolumeBbl: number } {
  const rhoWm = sgWeightMat * 8.34;
  const vStart = (weightMaterialInventorySacks * (rhoWm - pNewPpg - (liquidBblPer100Sacks / 100) * 350 * (pNewPpg - 8.34))) / (350 * (pNewPpg - pOldPpg));
  const wetting = (weightMaterialInventorySacks / 100) * liquidBblPer100Sacks;
  const vFinal = vStart + (weightMaterialInventorySacks * 100) / (sgWeightMat * 350) + wetting;
  const vDiscard = Math.max(0, vStart - vPitCapacityBbl);
  return {
    startVolumeBbl: Math.round(vStart * 10) / 10,
    discardVolumeBbl: Math.round(vDiscard * 10) / 10,
    finalVolumeBbl: Math.round(vFinal * 10) / 10,
  };
}

/**
 * Maximum mud weight achievable with inventory
 * Sourced: Carter Ch. 4, Eq. 4.19
 */
export function maxMudWeightWithInventory(wmiSacks: number, maxVolBbl: number, liquidBblPer100Sacks: number, startVolBbl: number, pOldPpg: number): number {
  const pMax = pOldPpg + (wmiSacks * (35.0 - pOldPpg)) / (1470 * startVolBbl + wmiSacks);
  return Math.round(pMax * 10) / 10;
}

/**
 * Mud weight reduction with base liquid
 * Sourced: Carter Ch. 4, Eq. 4.20
 */
export function mudWeightReduction_baseLiquid(vMudBbl: number, pOldPpg: number, pNewPpg: number, pBaseLiquidPpg: number = 8.34): number {
  return (vMudBbl * (pOldPpg - pNewPpg)) / (pNewPpg - pBaseLiquidPpg);
}

/**
 * Mud weight reduction using oil/brine mixture
 * Sourced: Carter Ch. 4, Eq. 4.21
 */
export function mudWeightReduction_oilBrine(vMudBbl: number, pOldPpg: number, pNewPpg: number, fOil: number, pOilPpg: number, fWater: number, pBrinePpg: number): number {
  const pMix = fOil * pOilPpg + fWater * pBrinePpg;
  return mudWeightReduction_baseLiquid(vMudBbl, pOldPpg, pNewPpg, pMix);
}

/**
 * Mix two fluids without volume limit
 * Sourced: Carter Ch. 4, Eq. 4.22
 */
export function mixTwoFluids_noVolumeLimit(v1Bbl: number, rho1Ppg: number, v2Bbl: number, rho2Ppg: number): number {
  return (v1Bbl * rho1Ppg + v2Bbl * rho2Ppg) / (v1Bbl + v2Bbl);
}

/**
 * Mix two fluids with limited total volume
 * Sourced: Carter Ch. 4, Eqs. 4.23–4.24
 */
export function mixTwoFluids_limitedVolume(vTotalBbl: number, rhoTargetPpg: number, rho1Ppg: number, rho2Ppg: number): { v1Bbl: number; v2Bbl: number } {
  const v1 = vTotalBbl * ((rhoTargetPpg - rho2Ppg) / (rho1Ppg - rho2Ppg));
  const v2 = vTotalBbl - v1;
  return {
    v1Bbl: Math.round(v1 * 10) / 10,
    v2Bbl: Math.round(v2 * 10) / 10,
  };
}

/**
 * OBM starting volume
 * Sourced: Carter Ch. 4, Eq. 4.25
 */
export function obmStartVolume(mwFinalPpg: number, mwOwmPpg: number, vFinalBbl: number, sgWeightMat: number = 4.2): number {
  const rhoWm = sgWeightMat * 8.34;
  return vFinalBbl * ((rhoWm - mwFinalPpg) / (rhoWm - mwOwmPpg));
}

/**
 * OBM oil content
 * Sourced: Carter Ch. 4, Eq. 4.26
 */
export function obmOilContent(vStartBbl: number, oilRatioPct: number): number {
  return (vStartBbl * oilRatioPct) / 100;
}

/**
 * OBM water content
 * Sourced: Carter Ch. 4, Eq. 4.27
 */
export function obmWaterContent(vStartBbl: number, waterRatioPct: number): number {
  return (vStartBbl * waterRatioPct) / 100;
}

/**
 * OBM weighting material volume
 * Sourced: Carter Ch. 4, Eq. 4.28
 */
export function obmWeightMaterialVolume(vFinalBbl: number, vStartBbl: number): number {
  return vFinalBbl - vStartBbl;
}

/**
 * OBM weighting material sacks
 * Sourced: Carter Ch. 4, Eq. 4.29
 */
export function obmWeightMaterialSacks(vWmBbl: number, sgWeightMat: number = 4.2): number {
  return Math.round((vWmBbl * sgWeightMat * 350) / 100);
}

/**
 * OBM recalculation of mud weight
 * Sourced: Carter Ch. 4, Eq. 4.30
 */
export function obmRecalcMudWeight(vOilBbl: number, pOilPpg: number, vWaterBbl: number, pWaterPpg: number, vWmBbl: number, sgWm: number = 4.2): number {
  const totalVol = vOilBbl + vWaterBbl + vWmBbl;
  return (vOilBbl * pOilPpg + vWaterBbl * pWaterPpg + vWmBbl * sgWm * 8.34) / totalVol;
}

/**
 * Oil-Water Ratio from retort %
 * Sourced: Carter Ch. 4, Eq. 4.31
 */
export function owrFromRetort(oilPct: number, waterPct: number): { oilRatio: number; waterRatio: number } {
  const totalLiquid = oilPct + waterPct;
  if (totalLiquid <= 0) return { oilRatio: 0, waterRatio: 0 };
  const o = (oilPct / totalLiquid) * 100;
  const w = (waterPct / totalLiquid) * 100;
  return {
    oilRatio: Math.round(o),
    waterRatio: Math.round(w),
  };
}

/**
 * Change OWR by adding oil
 * Sourced: Carter Ch. 4, Eq. 4.32
 */
export function changeOWR_addOil(vOilBbl: number, wOldPct: number, wNewPct: number): number {
  return vOilBbl * (wOldPct / wNewPct - 1);
}

/**
 * Change OWR by adding water
 * Sourced: Carter Ch. 4, Eq. 4.33
 */
export function changeOWR_addWater(vOilBbl: number, oOldPct: number, oNewPct: number): number {
  return vOilBbl * (oOldPct / oNewPct - 1);
}

/**
 * Saltwater volume from Cl- ppm
 * Sourced: Carter Ch. 4, Eq. 4.34
 */
export function saltwaterVolume(clPpm: number, wPct: number): number {
  return wPct * (1 + clPpm / 1000000);
}

/**
 * Suspended solids %
 * Sourced: Carter Ch. 4, Eq. 4.35
 */
export function suspendedSolids(wSolidsPct: number, oPct: number): number {
  return 100 - wSolidsPct - oPct;
}

/**
 * Saltwater SG from Cl- ppm
 * Sourced: Carter Ch. 4, Eq. 4.36
 */
export function saltwaterSG(clPpm: number): number {
  return 1.0 + clPpm * 0.0000007;
}

/**
 * Suspended solids SG
 * Sourced: Carter Ch. 4, Eq. 4.37
 */
export function suspendedSolidsSG(mwPpg: number, oPct: number, pOilPpg: number, wPct: number, sgSw: number, ssPct: number): number {
  if (ssPct <= 0) return 2.65;
  const pSolids = (100 * mwPpg - oPct * pOilPpg - wPct * sgSw * 8.34) / ssPct;
  return pSolids / 8.34;
}

/**
 * Suspended solids SG (no salt)
 * Sourced: Carter Ch. 4, Eq. 4.38
 */
export function suspendedSolidsSG_noSalt(mwPpg: number, oPct: number, pOilPpg: number, wPct: number, ssPct: number): number {
  return suspendedSolidsSG(mwPpg, oPct, pOilPpg, wPct, 1.0, ssPct);
}

/**
 * LGS Volume %
 * Sourced: Carter Ch. 4, Eq. 4.39
 */
export function lgsVolume(ssPct: number, sgBarite: number, sgSolids: number, sgLgs: number = 2.6) {
  const lgs = (ssPct * (sgBarite - sgSolids)) / (sgBarite - sgLgs);
  return Math.max(0, lgs);
}

/**
 * LGS concentration in ppb
 * Sourced: Carter Ch. 4, Eq. 4.40
 */
export function lgsPpb(lgsPct: number, sgLgs: number = 2.6): number {
  return lgsPct * 3.5 * sgLgs;
}

/**
 * HGS Volume %
 * Sourced: Carter Ch. 4, Eq. 4.41
 */
export function hgsVolume(ssPct: number, lgsPct: number): number {
  return Math.max(0, ssPct - lgsPct);
}

/**
 * HGS concentration in ppb
 * Sourced: Carter Ch. 4, Eq. 4.42
 */
export function hgsPpb(hgsPct: number, sgBarite: number = 4.2): number {
  return hgsPct * 3.5 * sgBarite;
}

/**
 * Bentonite concentration in ppb
 * Sourced: Carter Ch. 4, Eq. 4.43
 */
export function bentonitePpb(fCec: number, mbtValue: number, lgsPct: number): number {
  return mbtValue * 5;
}

/**
 * Bentonite %
 * Sourced: Carter Ch. 4, Eq. 4.44
 */
export function bentonitePct(bPpb: number): number {
  return bPpb / 9.1;
}

/**
 * Bentonite estimated %
 * Sourced: Carter Ch. 4, Eq. 4.45
 */
export function bentoniteEstimatedPct(mbtValue: number, lgsPct: number): number {
  return (mbtValue * 5) / 9.1;
}

/**
 * Drill solids %
 * Sourced: Carter Ch. 4, Eq. 4.46
 */
export function drillSolidsPct(lgsPct: number, bentonitePctVal: number): number {
  return Math.max(0, lgsPct - bentonitePctVal);
}

/**
 * Drill solids ppb
 * Sourced: Carter Ch. 4, Eq. 4.47
 */
export function drillSolidsPpb(dsPct: number, sgLgs: number = 2.6): number {
  return dsPct * 3.5 * sgLgs;
}

/**
 * Drill solids to bentonite ratio
 * Sourced: Carter Ch. 4, Eq. 4.48
 */
export function drillSolidsToBentoniteRatio(dsPpb: number, bPpb: number): number {
  if (bPpb <= 0) return 0;
  return dsPpb / bPpb;
}

/**
 * Recommended maximum solids %
 * Sourced: Carter Ch. 4, Eq. 4.49
 */
export function recommendedSolidsMax(mwPpg: number): number {
  return (mwPpg - 8.34) * 2 + 5;
}

/**
 * Recommended maximum LGS %
 * Sourced: Carter Ch. 4, Eq. 4.50
 */
export function recommendedLgsMax(mwPpg: number, srmPct: number): number {
  return srmPct * 0.4;
}

/**
 * Dilution volume without volume limit
 * Sourced: Carter Ch. 4, Eq. 4.51
 */
export function dilutionVolumeNoVolumeLimit(vStartBbl: number, lgsOldPct: number, lgsDesiredPct: number, lgsAddedPct: number = 0): number {
  return vStartBbl * ((lgsOldPct - lgsDesiredPct) / (lgsDesiredPct - lgsAddedPct));
}

/**
 * Dilution volume with displacement
 * Sourced: Carter Ch. 4, Eq. 4.52
 */
export function dilutionDisplacementVolume(vStartBbl: number, lgsOldPct: number, lgsDesiredPct: number, lgsAddedPct: number = 0): number {
  return dilutionVolumeNoVolumeLimit(vStartBbl, lgsOldPct, lgsDesiredPct, lgsAddedPct);
}

/**
 * Hydrocyclone solids fraction
 * Sourced: Carter Ch. 4, Eq. 4.53
 */
export function hydrocycloneSolidsFraction(mwDischargePpg: number, sgSolids: number = 2.6): number {
  return (mwDischargePpg - 8.34) / (sgSolids * 8.34 - 8.34);
}

/**
 * Hydrocyclone solids mass rate (lb/hr)
 * Sourced: Carter Ch. 4, Eq. 4.54
 */
export function hydrocycloneSolidsMassRate(hSolidsFrac: number, vFlowGpm: number, timeHours: number = 1.0): number {
  return hSolidsFrac * vFlowGpm * 8.34 * 2.6 * 60 * timeHours;
}

/**
 * Hydrocyclone liquid volume (gal/hr)
 * Sourced: Carter Ch. 4, Eq. 4.55
 */
export function hydrocycloneLiquidVolume(hSolidsFrac: number, vFlowGpm: number, timeHours: number = 1.0): number {
  return (1 - hSolidsFrac) * vFlowGpm * 60 * timeHours;
}

/**
 * Hydrocyclone cut point (microns)
 * Sourced: Carter Ch. 4, Eq. 4.56
 */
export function hydrocycloneCutPoint(pvCp: number, mwPpg: number): number {
  return 15 * Math.sqrt(pvCp / Math.max(1, mwPpg - 8.34));
}

/**
 * Centrifuge G-force
 * Sourced: Carter Ch. 4, Eq. 4.57
 */
export function centrifugeForce(rpm: number, bowlDiameterInches: number): number {
  return 0.0000142 * Math.pow(rpm, 2) * bowlDiameterInches;
}

/**
 * Centrifuge underflow volume
 * Sourced: Carter Ch. 4, Eq. 4.58
 */
export function centrifugeUnderflowVolume(vFeedGpm: number, mwFeedPpg: number, mwOverflowPpg: number, vDilutionGpm: number, mwDilutionPpg: number, mwUnderflowPpg: number): number {
  const num = vFeedGpm * (mwFeedPpg - mwOverflowPpg) + vDilutionGpm * (mwDilutionPpg - mwOverflowPpg);
  return num / (mwUnderflowPpg - mwOverflowPpg);
}

/**
 * Old mud fraction in underflow
 * Sourced: Carter Ch. 4, Eq. 4.59
 */
export function oldMudFractionUnderflow(sgWm: number, mwDilutionPpg: number, mwUnderflowPpg: number, mwFeedPpg: number, vDilutionGpm: number, vFeedGpm: number): number {
  return (vFeedGpm * (mwFeedPpg - mwDilutionPpg)) / ((vFeedGpm + vDilutionGpm) * (mwUnderflowPpg - mwDilutionPpg));
}

/**
 * Clay mass rate in underflow (lb/min)
 * Sourced: Carter Ch. 4, Eq. 4.60
 */
export function clayMassRate(lgsPpbVal: number, vFeedGpm: number, vUnderflowGpm: number, vOldMudFraction: number): number {
  return (lgsPpbVal * vUnderflowGpm * vOldMudFraction) / 42;
}

/**
 * Additive mass rate in underflow (lb/min)
 * Sourced: Carter Ch. 4, Eq. 4.61
 */
export function additiveMassRate(additivePpb: number, vFeedGpm: number, vUnderflowGpm: number, vOldMudFraction: number): number {
  return (additivePpb * vUnderflowGpm * vOldMudFraction) / 42;
}

/**
 * Base liquid flow rate in underflow (gal/min)
 * Sourced: Carter Ch. 4, Eq. 4.62
 */
export function baseLiquidFlowRate(vFeedGpm: number, sgWm: number, mwDilutionPpg: number, mwFeedPpg: number, vUnderflowGpm: number, mwUnderflowPpg: number): number {
  return vUnderflowGpm * (1 - (mwUnderflowPpg - 8.34) / (sgWm * 8.34 - 8.34));
}

/**
 * Water wetting barite in underflow (gal/min)
 * Sourced: Carter Ch. 4, Eq. 4.63
 */
export function waterWettingBarite(mwUnderflowPpg: number): number {
  return 0.05 * mwUnderflowPpg;
}

/**
 * Percent barite in underflow
 * Sourced: Carter Ch. 4, Eq. 4.64
 */
export function percentBariteInUnderflow(vWaterWettingGpm: number): number {
  return 100 - vWaterWettingGpm;
}

/**
 * Barite-liquid mixture in underflow
 * Sourced: Carter Ch. 4, Eq. 4.65
 */
export function bariteLiquidMixture(vFeedGpm: number, vFeedMw: number, vUnderflowGpm: number, vUnderflowMw: number, wUnderflowClay: number, wUnderflowAdditives: number): number {
  return vUnderflowGpm * vUnderflowMw - wUnderflowClay - wUnderflowAdditives;
}

/**
 * Barite weight in underflow (lb/min)
 * Sourced: Carter Ch. 4, Eq. 4.66
 */
export function bariteWeightInUnderflow(baritePct: number, mwUnderflowPpg: number, vBariteMixtureGpm: number): number {
  return (baritePct / 100) * mwUnderflowPpg * vBariteMixtureGpm;
}

/**
 * Hole volume per 1000 ft
 * Sourced: Carter Ch. 4, Eq. 4.67
 */
export function holeVolume1000ft(dhInches: number, washOutPct: number = 0): number {
  const dEff = dhInches * (1 + washOutPct / 100);
  return (Math.pow(dEff, 2) / 1029.4) * 1000;
}

/**
 * Mud separated with cuttings per 1000 ft
 * Sourced: Carter Ch. 4, Eq. 4.68
 */
export function mudSeparatedWithCuttings(mudToCuttingsRatio: number, vHole1000ftBbl: number): number {
  return vHole1000ftBbl * mudToCuttingsRatio;
}

/**
 * Total mud volume required per 1000 ft
 * Sourced: Carter Ch. 4, Eq. 4.69
 */
export function totalMudVolume1000ft(vHole1000ftBbl: number, vMudSeparatedBbl: number): number {
  return vHole1000ftBbl + vMudSeparatedBbl;
}

/**
 * Salt volume in brine %
 * Sourced: Carter Ch. 4, Eq. 4.70
 */
export function saltVolumeInBrine(cacl2Pct: number): number {
  return cacl2Pct * 0.8;
}

/**
 * Brine volume from salt and water
 * Sourced: Carter Ch. 4, Eq. 4.71
 */
export function brineVolume(vSaltBbl: number, vWaterBbl: number): number {
  return vSaltBbl + vWaterBbl;
}

/**
 * Corrected solids % from retort
 * Sourced: Carter Ch. 4, Eq. 4.72
 */
export function correctedSolids(vOilRetort: number, vBrineCorrected: number): number {
  return 100 - vOilRetort - vBrineCorrected;
}

/**
 * Base oil/brine downhole density
 * Sourced: Carter Ch. 4, Eq. 4.73
 */
export function baseOilBrineDownholeDensity(pSurfacePpg: number, tempF: number, pressPsi: number): number {
  return pSurfacePpg * (1 - (tempF - 60) * 0.0004 + pressPsi * 0.000003);
}

/**
 * Equivalent static density (ESD) at depth
 * Sourced: Carter Ch. 4, Eq. 4.74
 */
export function esdAtDepth(pSurfacePpg: number, tvdFt: number, tempGradDegFFt: number): number {
  const avgTemp = 60 + (tempGradDegFFt * tvdFt) / 2;
  const avgPress = pSurfacePpg * 0.052 * (tvdFt / 2);
  return baseOilBrineDownholeDensity(pSurfacePpg, avgTemp, avgPress);
}
