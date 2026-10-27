/**
 * Unit-Aware Formula Evaluation and Step-by-Step Calculation Engine
 * Sourced from Cormack (2017) order of operations:
 * brackets -> squares -> * / / -> + / -
 */

import { DRILLING_CONSTANTS, UnitType } from './constants';
import { round, CompanyRounding } from './rounding';

export interface Quantity {
  value: number;
  unit: UnitType;
  label?: string;
}

export interface CalculationAuditTrail {
  title: string;
  formula: string;
  rearrangedFor?: string;
  inputs: Record<string, Quantity>;
  intermediateSteps: string[];
  result: Quantity;
  roundedResult: Quantity;
}

/**
 * Unit conversion helper matching Cormack (2017) exact book tables
 */
export function convertUnit(value: number, from: UnitType, to: UnitType): number {
  if (from === to) return value;

  // Pressure
  if (from === 'bar' && to === 'psi') return value * DRILLING_CONSTANTS.BARS_TO_PSI; // 14.5
  if (from === 'psi' && to === 'bar') return value * DRILLING_CONSTANTS.PSI_TO_BARS;
  if (from === 'psi' && to === 'kPa') return value * 6.89476;
  if (from === 'kPa' && to === 'psi') return value / 6.89476;

  // Length
  if (from === 'ft' && to === 'm') return value * DRILLING_CONSTANTS.FEET_TO_METERS; // 0.3048
  if (from === 'm' && to === 'ft') return value * DRILLING_CONSTANTS.METERS_TO_FEET; // 3.281

  // Density / Gradient
  if (from === 'ppg' && to === 'SG') return value * DRILLING_CONSTANTS.PPG_TO_SG; // 0.1198
  if (from === 'SG' && to === 'ppg') return value * DRILLING_CONSTANTS.SG_TO_PPG;
  if (from === 'ppg' && to === 'psi/ft') return value * DRILLING_CONSTANTS.HYDROSTATIC_CONSTANT; // 0.052
  if (from === 'psi/ft' && to === 'ppg') return value / DRILLING_CONSTANTS.HYDROSTATIC_CONSTANT;

  // Volume
  if (from === 'bbl' && to === 'm3') return value * DRILLING_CONSTANTS.BBL_TO_M3; // 0.15897
  if (from === 'm3' && to === 'bbl') return value * DRILLING_CONSTANTS.M3_TO_BBL; // 6.2905
  if (from === 'gal' && to === 'bbl') return value * DRILLING_CONSTANTS.GALLONS_TO_BBL; // 0.02381
  if (from === 'bbl' && to === 'gal') return value * DRILLING_CONSTANTS.BBL_TO_GALLONS; // 42
  if (from === 'ft3' && to === 'bbl') return value * DRILLING_CONSTANTS.FT3_TO_BBL; // 0.1781

  return value;
}

/**
 * Formula template and audit generator
 */
export function formatFormulaAudit(
  title: string,
  formulaText: string,
  inputs: Record<string, Quantity>,
  steps: string[],
  rawResult: number,
  roundedResult: number,
  unit: UnitType
): CalculationAuditTrail {
  return {
    title,
    formula: formulaText,
    inputs,
    intermediateSteps: steps,
    result: { value: rawResult, unit },
    roundedResult: { value: roundedResult, unit },
  };
}
