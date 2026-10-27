/**
 * Drilling Hydraulics Engine
 * Sourced from Cormack (2017), Section 3: "Circulating Pressure and Pump Laws"
 */

import { CAPACITY_CONSTANT } from '../math/constants';
import { CompanyRounding, round } from '../math/rounding';

/**
 * Triplex pump output in bbl/stk
 * Sourced: Cormack Sect. 2, Eq. 2.7
 * Formula: (linerID^2 / 1029.4) * (strokeLengthIn / 12) * 3 * efficiency
 * When stroke is 12", stroke ft = 1.
 */
export function pumpOutputTriplex(
  linerID: number,
  strokeLengthIn: number,
  efficiency: number = 1.0
): number {
  const strokeFt = strokeLengthIn / 12;
  const bblPerStk = (Math.pow(linerID, 2) / CAPACITY_CONSTANT) * strokeFt * 3 * efficiency;
  return CompanyRounding.pumpOutput(bblPerStk);
}

/**
 * Pump flow rate in bbl/min: bbl/stk * SPM
 */
export function pumpOutputBblMin(bblPerStk: number, spm: number): number {
  return CompanyRounding.volume(bblPerStk * spm);
}

/**
 * Number of pump strokes: Volume / Pump Output (rounded UP to whole strokes)
 */
export function strokes(volumeBbl: number, bblPerStk: number): number {
  if (bblPerStk <= 0) return 0;
  return Math.ceil(volumeBbl / bblPerStk);
}

/**
 * Circulating time in minutes: strokes / SPM (rounded UP to whole minutes)
 */
export function circulatingTime(stks: number, spm: number): number {
  if (spm <= 0) return 0;
  return Math.ceil(stks / spm);
}

/**
 * Annular velocity in ft/min: Pump Output (bbl/min) / Annular Capacity (bbl/ft)
 * Sourced: Cormack Sect. 2, Eq. 2.8
 */
export function annularVelocity(bblMin: number, bblPerFt: number): number {
  if (bblPerFt <= 0) return 0;
  return CompanyRounding.volume(bblMin / bblPerFt);
}

/**
 * New circulating pressure at a new pump speed:
 * P2 = P1 * (SPM2 / SPM1)^2
 * Sourced: Cormack Sect. 3, Eq. 3.1
 */
export function newPressureAtNewPumpSpeed(oldP: number, oldSpm: number, newSpm: number): number {
  if (oldSpm <= 0) return oldP;
  const ratio = newSpm / oldSpm;
  return CompanyRounding.pressure(oldP * Math.pow(ratio, 2));
}

/**
 * New circulating pressure with a new mud weight:
 * P2 = P1 * (MW2 / MW1)
 * Sourced: Cormack Sect. 3, Eq. 3.2
 */
export function newPressureAtNewMudWeight(oldP: number, oldMW: number, newMW: number): number {
  if (oldMW <= 0) return oldP;
  const ratio = newMW / oldMW;
  return CompanyRounding.pressure(oldP * ratio);
}

/**
 * Combined pump speed and mud weight pressure change
 * Sourced: Cormack Sect. 3, Q5
 * Golden test result: Old 2,500 psi @ 80 SPM, 10.0 ppg -> New @ 100 SPM, 11.0 ppg = 4,274 psi
 * Verified: Path A (Speed then MW) matches Path B (MW then Speed) identically.
 */
export function combinedPumpChange(
  oldP: number,
  oldSpm: number,
  newSpm: number,
  oldMW: number,
  newMW: number
): { pressure: number; pathAMatchesPathB: boolean } {
  // Path A: speed then mud weight
  // P_int = P1 * (SPM2/SPM1)^2
  // P_final = P_int * (MW2/MW1)
  const speedRatioSq = Math.pow(newSpm / oldSpm, 2);
  const mwRatio = newMW / oldMW;

  const resultA = oldP * speedRatioSq * mwRatio;
  const resultB = oldP * mwRatio * speedRatioSq;

  const pFinal = Math.round(resultA);
  const pathAMatchesPathB = Math.round(resultA) === Math.round(resultB);

  return {
    pressure: pFinal,
    pathAMatchesPathB,
  };
}
