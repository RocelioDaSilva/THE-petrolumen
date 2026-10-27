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
