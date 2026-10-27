/**
 * Rig Operations Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 2.
 */

import { HYDROSTATIC_CONSTANT } from '../math/constants';

export function accumulatorUsableVolume(
  pPrechargePsi: number,
  pMaxPsi: number,
  pMinPsi: number,
  bottleCapacityGal: number
): { usableVolumeGal: number; usableFraction: number } {
  const v2 = bottleCapacityGal * (pPrechargePsi / pMaxPsi);
  const v3 = bottleCapacityGal * (pPrechargePsi / pMinPsi);
  const usable = v3 - v2;
  return {
    usableVolumeGal: Math.round(usable * 10) / 10,
    usableFraction: Math.round((usable / bottleCapacityGal) * 100) / 100,
  };
}

export function deepwaterAccumulatorUsableVolume(
  pPrechargePsi: number,
  pMaxPsi: number,
  pMinPsi: number,
  waterDepthFt: number,
  bottleCapacityGal: number
): { usableVolumeGal: number } {
  const hydrostaticHead = waterDepthFt * 0.444;
  const pMaxEff = pMaxPsi - hydrostaticHead;
  const pMinEff = pMinPsi - hydrostaticHead;
  const res = accumulatorUsableVolume(pPrechargePsi, Math.max(100, pMaxEff), Math.max(50, pMinEff), bottleCapacityGal);
  return { usableVolumeGal: res.usableVolumeGal };
}

export function prechargePressureRequired(pMinPsi: number, pMaxPsi: number, requiredUsableGal: number, totalBottleCapGal: number): number {
  return (requiredUsableGal * pMinPsi * pMaxPsi) / (totalBottleCapGal * (pMaxPsi - pMinPsi));
}

export function slugVolumeRequired(
  lengthDryPipeFt: number,
  dpCapacityBblFt: number,
  mwPpg: number,
  slugMwPpg: number
): number {
  const deltaMw = slugMwPpg - mwPpg;
  if (deltaMw <= 0) return 0;
  const hSlug = (lengthDryPipeFt * mwPpg) / deltaMw;
  return hSlug * dpCapacityBblFt;
}

export function slugMudWeightRequired(
  lengthDryPipeFt: number,
  vSlugBbl: number,
  dpCapacityBblFt: number,
  mwPpg: number
): number {
  const hSlug = vSlugBbl / dpCapacityBblFt;
  if (hSlug <= 0) return mwPpg;
  return mwPpg + (lengthDryPipeFt * mwPpg) / hSlug;
}

export function slugPitGainAndHydrostatic(
  vSlugBbl: number,
  slugMwPpg: number,
  mwPpg: number,
  dpCapacityBblFt: number
): { pitGainBbl: number; heightInPipeFt: number; hydrostaticPressureChangePsi: number } {
  const hSlug = vSlugBbl / dpCapacityBblFt;
  const hDry = (vSlugBbl * (slugMwPpg - mwPpg)) / (mwPpg * dpCapacityBblFt);
  const hpChange = (slugMwPpg - mwPpg) * HYDROSTATIC_CONSTANT * hSlug;
  return {
    pitGainBbl: Math.round(vSlugBbl * 10) / 10,
    heightInPipeFt: Math.round(hDry * 10) / 10,
    hydrostaticPressureChangePsi: Math.round(hpChange * 10) / 10,
  };
}

export function bulkDensityFromMudBalance(mudWeightPpg: number): { sg: number; densityLbFt3: number } {
  const sg = mudWeightPpg / 8.34;
  const lbFt3 = mudWeightPpg * 7.4805;
  return {
    sg: Math.round(sg * 100) / 100,
    densityLbFt3: Math.round(lbFt3 * 10) / 10,
  };
}

export function spottingPillCalculations(
  lAnnularCoverageFt: number,
  cAnnularBblFt: number,
  cDpBblFt: number,
  lPipeAboveFt: number,
  opBblStk: number
): { vPillAnnulusBbl: number; vPillPipeBbl: number; vPillTotalBbl: number; strokesToSpot: number } {
  const vAnn = lAnnularCoverageFt * cAnnularBblFt;
  const vPipe = lAnnularCoverageFt * cDpBblFt;
  const vTotal = vAnn + vPipe;
  const vDisplace = lPipeAboveFt * cDpBblFt;
  const strokes = Math.round(vDisplace / opBblStk);
  return {
    vPillAnnulusBbl: Math.round(vAnn * 10) / 10,
    vPillPipeBbl: Math.round(vPipe * 10) / 10,
    vPillTotalBbl: Math.round(vTotal * 10) / 10,
    strokesToSpot: strokes,
  };
}

export function breakoverPoint(
  pFormationPsi: number,
  mwPpg: number,
  tvdFt: number
): { pressureGradientPsiFt: number; maxDepthFt: number } {
  const grad = mwPpg * HYDROSTATIC_CONSTANT;
  const depth = pFormationPsi / grad;
  return {
    pressureGradientPsiFt: Math.round(grad * 1000) / 1000,
    maxDepthFt: Math.round(depth),
  };
}

export function lowPressureLineVelocity(qGpm: number, lineIdInches: number): number {
  const vFtS = qGpm / (2.448 * Math.pow(lineIdInches, 2));
  return Math.round(vFtS * 10) / 10;
}
