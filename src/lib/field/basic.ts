/**
 * Basic Field Formulas (Field Units Only)
 * Sourced from Carter, Lyons & Lapeyrouse,
 * "Formulas and Calculations for Drilling, Production, and Workover" (5th Ed., Elsevier, 2023), Chapter 1.
 */

import {
  FW_DENSITY_LB_FT3,
  FW_DENSITY_PPG,
  CONVERSION_FACTOR_0_052,
  CAPACITY_CONSTANT,
  FT3_TO_BBL,
  STEEL_LB_PER_BBL,
} from "./constants";

export function mudWeightLbFt3_fw(sg: number): number {
  return sg * FW_DENSITY_LB_FT3;
}

export function mudWeightPpg_fw(sg: number): number {
  return sg * FW_DENSITY_PPG;
}

export function sg_fw(mwLbFt3: number): number {
  return mwLbFt3 / FW_DENSITY_LB_FT3;
}

export function sgFromMudWeight(mwPpg: number): number {
  return mwPpg / FW_DENSITY_PPG;
}

export function hydrostaticPressure_psf(mwLbFt3: number, hFt: number): number {
  return mwLbFt3 * hFt;
}

export function hydrostaticPressure_psi_ft3(mwLbFt3: number, hFt: number): number {
  return (mwLbFt3 * hFt) / 144;
}

export function hydrostaticPressure_psi_ppg(mwPpg: number, hFt: number): number {
  return CONVERSION_FACTOR_0_052 * mwPpg * hFt;
}

export function pressureGradient_psi_ft(mwPpg: number): number {
  return CONVERSION_FACTOR_0_052 * mwPpg;
}

export function pressureGradient_ppg(pressureGradientPsiFt: number): number {
  return pressureGradientPsiFt / CONVERSION_FACTOR_0_052;
}

export function triplex_galPerStroke(DlInches: number, SInches: number, evFraction: number = 1.0): number {
  return 0.000243 * Math.pow(DlInches, 2) * SInches * evFraction * 42;
}

export function triplex_bblPerStroke(DlInches: number, SInches: number, evFraction: number = 1.0): number {
  return 0.000243 * Math.pow(DlInches, 2) * SInches * evFraction;
}

export function triplex_gpm(DlInches: number, SInches: number, spm: number, evFraction: number = 1.0): number {
  return triplex_galPerStroke(DlInches, SInches, evFraction) * spm;
}

export function triplex_bpm(DlInches: number, SInches: number, spm: number, evFraction: number = 1.0): number {
  return triplex_bblPerStroke(DlInches, SInches, evFraction) * spm;
}

export function duplex_galPerStroke(DlInches: number, DrInches: number, SInches: number, evFraction: number = 1.0): number {
  return 0.000162 * (2 * Math.pow(DlInches, 2) - Math.pow(DrInches, 2)) * SInches * evFraction * 42;
}

export function duplex_bblPerStroke(DlInches: number, DrInches: number, SInches: number, evFraction: number = 1.0): number {
  return 0.000162 * (2 * Math.pow(DlInches, 2) - Math.pow(DrInches, 2)) * SInches * evFraction;
}

export function duplex_gpm(DlInches: number, DrInches: number, SInches: number, spm: number, evFraction: number = 1.0): number {
  return duplex_galPerStroke(DlInches, DrInches, SInches, evFraction) * spm;
}

export function hydraulicHP_circulating(pressurePsi: number, qGpm: number): number {
  return (pressurePsi * qGpm) / 1714;
}

export function hydraulicHP_input(pressurePsi: number, qGpm: number, evFraction: number = 0.95, emFraction: number = 0.85): number {
  return hydraulicHP_circulating(pressurePsi, qGpm) / (evFraction * emFraction);
}

export function capacity_bblFt(idInches: number): number {
  return Math.pow(idInches, 2) / CAPACITY_CONSTANT;
}

export function capacity_ftBbl(idInches: number): number {
  return CAPACITY_CONSTANT / Math.pow(idInches, 2);
}

export function capacity_galFt(idInches: number): number {
  return capacity_bblFt(idInches) * 42;
}

export function capacity_ftGal(idInches: number): number {
  return 1 / capacity_galFt(idInches);
}

export function capacity_ft3Ft(idInches: number): number {
  return capacity_bblFt(idInches) / FT3_TO_BBL;
}

export function capacity_ftFt3(idInches: number): number {
  return 1 / capacity_ft3Ft(idInches);
}

export function displacement_bblFt(odInches: number, idInches: number): number {
  return (Math.pow(odInches, 2) - Math.pow(idInches, 2)) / CAPACITY_CONSTANT;
}

export function displacement_ftBbl(odInches: number, idInches: number): number {
  return CAPACITY_CONSTANT / (Math.pow(odInches, 2) - Math.pow(idInches, 2));
}

export function displacement_galFt(odInches: number, idInches: number): number {
  return displacement_bblFt(odInches, idInches) * 42;
}

export function displacement_ftGal(odInches: number, idInches: number): number {
  return 1 / displacement_galFt(odInches, idInches);
}

export function displacement_ft3Ft(odInches: number, idInches: number): number {
  return displacement_bblFt(odInches, idInches) / FT3_TO_BBL;
}

export function displacement_ftFt3(odInches: number, idInches: number): number {
  return 1 / displacement_ft3Ft(odInches, idInches);
}

export function annularCapacity_bblFt(dhInches: number, dpInches: number): number {
  return (Math.pow(dhInches, 2) - Math.pow(dpInches, 2)) / CAPACITY_CONSTANT;
}

export function annularCapacity_ftBbl(dhInches: number, dpInches: number): number {
  return CAPACITY_CONSTANT / (Math.pow(dhInches, 2) - Math.pow(dpInches, 2));
}

export function annularCapacity_galFt(dhInches: number, dpInches: number): number {
  return annularCapacity_bblFt(dhInches, dpInches) * 42;
}

export function annularCapacity_ftGal(dhInches: number, dpInches: number): number {
  return 1 / annularCapacity_galFt(dhInches, dpInches);
}

export function annularCapacity_ft3Ft(dhInches: number, dpInches: number): number {
  return annularCapacity_bblFt(dhInches, dpInches) / FT3_TO_BBL;
}

export function annularCapacity_ftFt3(dhInches: number, dpInches: number): number {
  return 1 / annularCapacity_ft3Ft(dhInches, dpInches);
}

export function annularCapacityMultipleTubing_bblFt(diInches: number, tubingOdsInches: number[]): number {
  const sumOdSq = tubingOdsInches.reduce((sum, od) => sum + Math.pow(od, 2), 0);
  return (Math.pow(diInches, 2) - sumOdSq) / CAPACITY_CONSTANT;
}

export function annularCapacityMultipleTubing_ftBbl(diInches: number, tubingOdsInches: number[]): number {
  return 1 / annularCapacityMultipleTubing_bblFt(diInches, tubingOdsInches);
}

export function annularCapacityMultipleTubing_galFt(diInches: number, tubingOdsInches: number[]): number {
  return annularCapacityMultipleTubing_bblFt(diInches, tubingOdsInches) * 42;
}

export function annularCapacityMultipleTubing_ftGal(diInches: number, tubingOdsInches: number[]): number {
  return 1 / annularCapacityMultipleTubing_galFt(diInches, tubingOdsInches);
}

export function annularCapacityMultipleTubing_ft3Ft(diInches: number, tubingOdsInches: number[]): number {
  return annularCapacityMultipleTubing_bblFt(diInches, tubingOdsInches) / FT3_TO_BBL;
}

export function annularCapacityMultipleTubing_ftFt3(diInches: number, tubingOdsInches: number[]): number {
  return 1 / annularCapacityMultipleTubing_ft3Ft(diInches, tubingOdsInches);
}

export function cuttingsVolume_bblFt(dhInches: number, porosityFraction: number = 0): number {
  return (Math.pow(dhInches, 2) / CAPACITY_CONSTANT) * (1 - porosityFraction);
}

export function cuttingsVolume_ft3Ft(dhInches: number, porosityFraction: number = 0): number {
  return cuttingsVolume_bblFt(dhInches, porosityFraction) / FT3_TO_BBL;
}

export function cuttingsWeight_lb(caBblFt: number, ldFt: number, porosityFraction: number, sgRock: number = 2.65): number {
  return caBblFt * ldFt * (1 - porosityFraction) * sgRock * STEEL_LB_PER_BBL;
}

export function annularVelocity_ftMin_bblMin(qpBblMin: number, caBblFt: number): number {
  return qpBblMin / caBblFt;
}

export function annularVelocity_ftMin_gpm(qGpm: number, dhInches: number, dpInches: number): number {
  return (24.5 * qGpm) / (Math.pow(dhInches, 2) - Math.pow(dpInches, 2));
}

export function annularVelocity_ftMin_bblMin_alt(qpBblMin: number, dhInches: number, dpInches: number): number {
  return (1029.4 * qpBblMin) / (Math.pow(dhInches, 2) - Math.pow(dpInches, 2));
}

export function annularVelocity_ftSec(qpBblMin: number, dhInches: number, dpInches: number): number {
  return annularVelocity_ftMin_bblMin_alt(qpBblMin, dhInches, dpInches) / 60;
}

export function pumpOutputForAV(avFtMin: number, dhInches: number, dpInches: number): number {
  return (avFtMin * (Math.pow(dhInches, 2) - Math.pow(dpInches, 2))) / 24.5;
}

export function strokesPerMinForAV(avFtMin: number, caBblFt: number, opBblStk: number): number {
  return (avFtMin * caBblFt) / opBblStk;
}

export function bottomsUpTime(dhInches: number, dpInches: number, lFt: number, qGpm: number): number {
  const caBblFt = annularCapacity_bblFt(dhInches, dpInches);
  const qBblMin = qGpm / 42;
  return (caBblFt * lFt) / qBblMin;
}

export function roughneckNewPressure(pOldPsi: number, spmNew: number, spmOld: number): number {
  return pOldPsi * Math.pow(spmNew / spmOld, 2);
}

export function roughneckExactFactor(pNew: number, pOld: number, qNew: number, qOld: number): number {
  return Math.log(pNew / pOld) / Math.log(qNew / qOld);
}

export function buoyancyFactor_ppg(mwPpg: number): number {
  return (65.5 - mwPpg) / 65.5;
}

export function buoyancyFactor_lbFt3(mwLbFt3: number): number {
  return (489.5 - mwLbFt3) / 489.5;
}

export function formationTemp(tsDegF: number, tempGradientDegFFt: number, tvdFt: number): number {
  return tsDegF + tempGradientDegFFt * tvdFt;
}

export function fahrenheitToCelsius(f: number): number {
  return ((f - 32) * 5) / 9;
}

export function celsiusToFahrenheit(c: number): number {
  return (c * 9) / 5 + 32;
}

export function celsiusToKelvin(c: number): number {
  return c + 273.15;
}

export function fahrenheitToRankine(f: number): number {
  return f + 459.67;
}

export function fahrenheitToCelsius_rule(f: number): number {
  return (f - 30) / 2;
}

export function celsiusToFahrenheit_rule(c: number): number {
  return c * 2 + 30;
}
