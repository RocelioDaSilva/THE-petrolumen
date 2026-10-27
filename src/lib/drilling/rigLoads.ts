/**
 * Rig Loads Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 * Reuses Bourgoyne's block-and-tackle efficiency table.
 */

import { HOISTING_EFFICIENCY_BY_LINES } from '../math/tables';

export interface RigLoadsResult {
  deadLineLoadLb: number;
  fastLineLoadStaticLb: number;
  fastLineLoadDynamicHoistingLb: number;
  fastLineLoadDynamicLoweringLb: number;
  derrickLoadLb: number;
  substructureLoadLb: number;
  deadLineSafetyFactor: number;
  fastLineSafetyFactor1: number;
  fastLineSafetyFactor2: number;
}

export function calculateRigLoads(
  hookLoadLb: number,
  numLines: number = 10,
  lineBreakingStrengthLb: number = 396000,
  derrickRatingLb: number = 1000000,
  substructureRatingLb: number = 1500000,
  blockWeightLb: number = 25000
): RigLoadsResult {
  const n = numLines;
  const eff = HOISTING_EFFICIENCY_BY_LINES[n] || 0.81;

  const W = hookLoadLb + blockWeightLb;
  const tDead = W / n;
  const tFastStatic = W / n;
  const tFastDynamicHoisting = W / (n * eff);
  const tFastDynamicLowering = (W * eff) / n;

  const derrickLoad = W + tDead + tFastDynamicHoisting;
  const substructureLoad = W + blockWeightLb;

  const sfDead = lineBreakingStrengthLb / Math.max(1, tDead);
  const sfFast1 = lineBreakingStrengthLb / Math.max(1, tFastDynamicHoisting);
  const sfFast2 = lineBreakingStrengthLb / Math.max(1, tFastDynamicLowering);

  return {
    deadLineLoadLb: Math.round(tDead),
    fastLineLoadStaticLb: Math.round(tFastStatic),
    fastLineLoadDynamicHoistingLb: Math.round(tFastDynamicHoisting),
    fastLineLoadDynamicLoweringLb: Math.round(tFastDynamicLowering),
    derrickLoadLb: Math.round(derrickLoad),
    substructureLoadLb: Math.round(substructureLoad),
    deadLineSafetyFactor: Math.round(sfDead * 100) / 100,
    fastLineSafetyFactor1: Math.round(sfFast1 * 100) / 100,
    fastLineSafetyFactor2: Math.round(sfFast2 * 100) / 100,
  };
}
