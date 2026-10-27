/**
 * Core Analysis Engine (Dean Stark Method)
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 */

export interface DeanStarkResult {
  poreVolumeCm3: number;
  porosityPct: number;
  waterSaturationPct: number;
  oilSaturationPct: number;
  gasSaturationPct: number;
}

export function deanStarkCoreAnalysis(
  totalCoreVolumeCm3: number,
  waterExtractedCm3: number,
  oilExtractedGrams: number,
  oilDensityGcm3: number = 0.85,
  grainDensityGcm3: number = 2.65,
  dryGrainWeightGrams?: number
): DeanStarkResult {
  const vWater = waterExtractedCm3;
  const vOil = oilExtractedGrams / oilDensityGcm3;

  let vPore = vWater + vOil;
  if (dryGrainWeightGrams !== undefined && dryGrainWeightGrams > 0) {
    const vGrain = dryGrainWeightGrams / grainDensityGcm3;
    vPore = Math.max(vPore, totalCoreVolumeCm3 - vGrain);
  }

  const phi = (vPore / totalCoreVolumeCm3) * 100;
  const sw = (vWater / vPore) * 100;
  const so = (vOil / vPore) * 100;
  const sg = Math.max(0, 100 - sw - so);

  return {
    poreVolumeCm3: Math.round(vPore * 100) / 100,
    porosityPct: Math.round(phi * 10) / 10,
    waterSaturationPct: Math.round(sw * 10) / 10,
    oilSaturationPct: Math.round(so * 10) / 10,
    gasSaturationPct: Math.round(sg * 10) / 10,
  };
}
