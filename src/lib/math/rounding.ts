/**
 * Company Rounding Rules Engine
 * Implements standard company rounding policy and Cormack (2017) book conventions:
 * - capacities: 4–5 decimal places
 * - volumes: 2 decimal places
 * - pump output: 3 decimal places
 * - strokes/time: whole numbers
 * - pressures: nearest psi
 * - mud weights: 2 decimal places
 * - kill mud weight: ALWAYS round UP to 1 decimal place (Cormack Sect. 4)
 * - maximum mud weight: ALWAYS round DOWN to 1 decimal place (Cormack Sect. 3)
 */

export type RoundingMode = 'half-up' | 'round-up' | 'round-down';

export function round(value: number, places: number = 0, mode: RoundingMode = 'half-up'): number {
  if (!Number.isFinite(value)) return 0;
  const factor = Math.pow(10, places);
  const sign = value < 0 ? -1 : 1;
  const absVal = Math.abs(value);
  const shifted = Number(absVal + 'e' + places);
  if (mode === 'round-up') {
    return sign * (Math.ceil(shifted) / factor);
  }
  if (mode === 'round-down') {
    return sign * (Math.floor(shifted) / factor);
  }
  // Decimal-safe half-up: round(1.005, 2) === 1.01
  return sign * (Math.round(shifted) / factor);
}

/**
 * Kill Mud Weight must ALWAYS be rounded UP to 1 decimal place.
 * E.g., 12.21 -> 12.3 ppg (Cormack Sect. 4, Well Three)
 */
export function roundKillMW(ppg: number): number {
  if (!Number.isFinite(ppg)) return 0;
  return round(ppg, 1, 'round-up');
}

/**
 * Maximum Mud Weight must ALWAYS be rounded DOWN to 1 decimal place
 * to avoid exceeding casing shoe fracture gradient.
 * E.g., 14.68 -> 14.6 ppg (Cormack Sect. 3, Worked Example)
 */
export function roundMaxMW(ppg: number): number {
  if (!Number.isFinite(ppg)) return 0;
  return round(ppg, 1, 'round-down');
}

export const CompanyRounding = {
  capacity: (val: number): number => round(val, 5),
  volume: (val: number): number => round(val, 2),
  pumpOutput: (val: number): number => round(val, 3),
  strokes: (val: number): number => round(val, 0, 'round-up'), // whole number, ceil
  time: (val: number): number => round(val, 0, 'round-up'),    // whole minutes, ceil
  pressure: (val: number): number => round(val, 0),             // nearest whole psi
  gradient: (val: number): number => round(val, 4),            // psi/ft
  mudWeight: (val: number): number => round(val, 2),
  killMW: roundKillMW,
  maxMW: roundMaxMW,
};
