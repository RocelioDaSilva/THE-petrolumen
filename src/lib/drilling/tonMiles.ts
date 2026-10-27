/**
 * Ton-Mile Calculations Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 */

export function roundTripTonMiles(
  depthFt: number,
  standLengthFt: number,
  drillPipeWeightLbFt: number,
  drillCollarWeightLbFt: number,
  drillCollarLengthFt: number,
  blockWeightLb: number
): number {
  const wDp = drillPipeWeightLbFt;
  const wDc = drillCollarWeightLbFt;
  const lDc = drillCollarLengthFt;
  const M = blockWeightLb;

  const wSubmergedDp = wDp * (depthFt - lDc);
  const wSubmergedDc = wDc * lDc;
  const totalStringWeight = wSubmergedDp + wSubmergedDc;

  const tm = (depthFt * (totalStringWeight + 2 * M) + depthFt * wSubmergedDp) / 10560000;
  return Math.round(tm * 10) / 10;
}

export function drillingTonMiles(rttmStart: number, rttmEnd: number): number {
  return Math.max(0, 3 * (rttmEnd - rttmStart));
}

export function coringTonMiles(rttmStart: number, rttmEnd: number): number {
  return Math.max(0, 2 * (rttmEnd - rttmStart));
}

export function casingTonMiles(casingDepthFt: number, casingWeightLbFt: number, blockWeightLb: number): number {
  const tm = (casingDepthFt * (casingDepthFt * casingWeightLbFt + 2 * blockWeightLb)) / 10560000;
  return Math.round(tm * 10) / 10;
}

export function shortTripTonMiles(rttmDeep: number, rttmShallow: number): number {
  return Math.max(0, rttmDeep - rttmShallow);
}

export function drillLineCutoffLength(derrickHeightFt: number, drumDiameterInches: number, numLaps: number = 2.5): number {
  const cutoff = (derrickHeightFt + Math.PI * (drumDiameterInches / 12) * numLaps);
  return Math.round(cutoff * 10) / 10;
}
