/**
 * Unified Droplet Settling Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapters 4, 5, 7, 9, 10 and Bourgoyne et al. (1986) Chapter 4.
 */

export interface SettlingIterationResult {
  terminalVelocity: number; // ft/s
  dragCoefficient: number; // dimensionless
  reynoldsNumber: number; // dimensionless
  iterations: number;
}

/**
 * Calculates drag coefficient using the Schiller-Naumann / Arnold & Stewart complete formula:
 * CD = 24/Re + 3/sqrt(Re) + 0.34 (Eq. 4-6)
 */
export function dragCoefficient(re: number): number {
  if (re <= 0) return 0.34;
  return 24 / re + 3 / Math.sqrt(re) + 0.34;
}

/**
 * Iteratively calculates the terminal settling velocity of a liquid droplet in gas
 * using Arnold & Stewart's procedure (Eqs. 4-6 and 4-7a):
 * Field Units:
 *   Vt = 0.0119 * [((rhoL - rhoG) / rhoG) * (dm / CD)]^0.5
 *   Re = 0.0049 * (rhoG * dm * Vt) / mu
 * Sourced: Arnold & Stewart Ex. 4-1 / 4-3
 */
export function iterativeDropletVelocityField(
  rhoL: number, // lb/ft3
  rhoG: number, // lb/ft3
  dmMicrons: number, // microns
  muCp: number // cp
): SettlingIterationResult {
  if (rhoL <= rhoG || dmMicrons <= 0 || muCp <= 0) {
    return { terminalVelocity: 0, dragCoefficient: 0.34, reynoldsNumber: 0, iterations: 0 };
  }

  const deltaRhoOverRhoG = (rhoL - rhoG) / rhoG;

  // Step 1: Initial estimate with CD = 0.34
  let cd = 0.34;
  let vt = 0.0204 * Math.sqrt(deltaRhoOverRhoG * dmMicrons);
  let re = 0.0049 * ((rhoG * dmMicrons * vt) / muCp);
  let iters = 0;

  for (let i = 0; i < 50; i++) {
    iters++;
    const newCd = dragCoefficient(re);
    const newVt = 0.0119 * Math.sqrt((deltaRhoOverRhoG * dmMicrons) / newCd);
    const newRe = 0.0049 * ((rhoG * dmMicrons * newVt) / muCp);

    if (Math.abs(newCd - cd) < 0.001) {
      cd = newCd;
      vt = newVt;
      re = newRe;
      break;
    }
    cd = newCd;
    vt = newVt;
    re = newRe;
  }

  return {
    terminalVelocity: Math.round(vt * 1000) / 1000,
    dragCoefficient: Math.round(cd * 1000) / 1000,
    reynoldsNumber: Math.round(re * 10) / 10,
    iterations: iters,
  };
}

/**
 * Stokes' Law Terminal Velocity for Liquid-Liquid settling (Oil in Water or Water in Oil)
 * Field Units:
 *   Vt = 1.78e-6 * (deltaSG * dm^2) / mu  (Eq. 5-2a, 7-7a, 9-1a, 10-3a)
 * where Vt is in ft/s, deltaSG is |SGo - SGw|, dm is microns, mu is cp of continuous phase.
 */
export function stokesLiquidVelocityField(
  deltaSG: number, // dimensionless
  dmMicrons: number, // microns
  muContinuousCp: number // cp
): number {
  if (muContinuousCp <= 0 || dmMicrons <= 0 || deltaSG <= 0) return 0;
  return (1.78e-6 * deltaSG * Math.pow(dmMicrons, 2)) / muContinuousCp;
}

/**
 * Stokes' Law in SI Units:
 *   Vt = 5.56e-7 * (deltaSG * dm^2) / mu  (Eq. 5-2b, 7-7b, 9-1b)
 * where Vt is in m/s.
 */
export function stokesLiquidVelocitySI(
  deltaSG: number,
  dmMicrons: number,
  muContinuousCp: number
): number {
  if (muContinuousCp <= 0 || dmMicrons <= 0 || deltaSG <= 0) return 0;
  return (5.56e-7 * deltaSG * Math.pow(dmMicrons, 2)) / muContinuousCp;
}
