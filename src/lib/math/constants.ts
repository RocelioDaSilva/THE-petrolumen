/**
 * Core Mathematical and Physical Constants
 * Directly sourced from:
 * Colin Cormack, "An Introduction to Well Control Calculations for Drilling Operations",
 * Springer, 2017.
 */

export const HYDROSTATIC_CONSTANT = 0.052; // psi / (ppg * ft)
export const CAPACITY_CONSTANT = 1029.4;    // in^2 * ft / bbl
export const FT3_TO_BBL = 0.1781;          // bbl / ft^3
export const M3_TO_BBL = 6.2905;           // bbl / m^3
export const STEEL_LB_PER_BBL = 2747;      // lb steel / bbl displacement

export const DRILLING_CONSTANTS = {
  HYDROSTATIC_CONSTANT,
  CAPACITY_CONSTANT,
  FT3_TO_BBL,
  M3_TO_BBL,
  STEEL_LB_PER_BBL,
  // Unit conversion factors from Cormack (2017)
  BARS_TO_PSI: 14.5,
  PSI_TO_BARS: 1 / 14.5,
  FEET_TO_METERS: 0.3048,
  METERS_TO_FEET: 3.281,
  PPG_TO_SG: 0.1198,
  SG_TO_PPG: 1 / 0.1198,
  BBL_TO_M3: 0.15897,
  M3_TO_BBL_ALT: 1 / 0.15897,
  GALLONS_TO_BBL: 0.02381, // 1 / 42
  BBL_TO_GALLONS: 42,
} as const;

export type UnitType =
  | 'psi' | 'bar' | 'kPa'
  | 'ft' | 'm'
  | 'ppg' | 'SG' | 'psi/ft'
  | 'bbl' | 'm3' | 'gal' | 'ft3'
  | 'bbl/ft' | 'bbl/stk' | 'bbl/min' | 'gpm'
  | 'ft/min' | 'spm' | 'lb/ft' | 'degF' | 'degC';
