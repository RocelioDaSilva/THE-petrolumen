/**
 * Completions & Tubing Stretch Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 */

export interface TubingStretchResult {
  weightStretchFt: number;
  pressureStretchFt: number;
  temperatureStretchFt: number;
  ballooningStretchFt: number;
  totalStretchFt: number;
}

export function tubingStretchComponents(
  depthFt: number,
  tubingWeightLbFt: number,
  tubingOdInches: number,
  tubingIdInches: number,
  pInternalPsi: number,
  pExternalPsi: number,
  deltaTempDegF: number
): TubingStretchResult {
  const e = 30e6;
  const alpha = 6.9e-6;
  const aAs = (Math.PI / 4) * (Math.pow(tubingOdInches, 2) - Math.pow(tubingIdInches, 2));

  const sW = (tubingWeightLbFt * Math.pow(depthFt, 2)) / (2 * e * aAs * 12);
  const sT = alpha * deltaTempDegF * depthFt;
  const sP = (pInternalPsi - pExternalPsi) * 0.0001;
  const sB = -0.15 * sP;

  const total = sW + sT + sP + sB;

  return {
    weightStretchFt: Math.round(sW * 100) / 100,
    pressureStretchFt: Math.round(sP * 100) / 100,
    temperatureStretchFt: Math.round(sT * 100) / 100,
    ballooningStretchFt: Math.round(sB * 100) / 100,
    totalStretchFt: Math.round(total * 100) / 100,
  };
}

export function brineTemperatureCorrection(
  surfaceMwPpg: number,
  surfaceTempF: number,
  avgTempF: number
): number {
  const deltaT = avgTempF - surfaceTempF;
  const correctedMw = surfaceMwPpg - deltaT * 0.0035;
  return Math.round(correctedMw * 10) / 10;
}

export function holeWashoutRisk(
  nozzleVelocityFtS: number,
  shearRateSec1: number
): { riskLevel: "Low" | "Moderate" | "High"; maxShearRateSec1: number } {
  let risk: "Low" | "Moderate" | "High" = "Low";
  if (shearRateSec1 > 100000 || nozzleVelocityFtS > 400) {
    risk = "High";
  } else if (shearRateSec1 > 50000 || nozzleVelocityFtS > 250) {
    risk = "Moderate";
  }
  return {
    riskLevel: risk,
    maxShearRateSec1: Math.round(shearRateSec1),
  };
}
