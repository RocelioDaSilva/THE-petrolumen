/**
 * Stuck Pipe & Fishing Economics Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 2 & Chapter 3.
 */

export function daysToQuitFishing(
  fishValueUSD: number,
  dailyRigRateUSD: number,
  dailyToolRateUSD: number = 0,
  replacementAssemblyCostUSD: number = 0
): { daysToQuit: number; breakEvenCostUSD: number } {
  const totalDaily = dailyRigRateUSD + dailyToolRateUSD;
  if (totalDaily <= 0) return { daysToQuit: 0, breakEvenCostUSD: fishValueUSD };
  const totalValue = fishValueUSD + replacementAssemblyCostUSD;
  const days = totalValue / totalDaily;
  return {
    daysToQuit: Math.round(days * 10) / 10,
    breakEvenCostUSD: Math.round(totalValue),
  };
}

export function freePointMethod1(
  stretchInches: number,
  overpullLb: number,
  dpWeightLbFt: number
): number {
  if (overpullLb <= 0) return 0;
  const depth = (stretchInches * dpWeightLbFt * 735294) / overpullLb;
  return Math.round(depth);
}

export function freePointMethod2(
  stretchInches: number,
  overpullKlbs: number,
  stretchConstant: number
): number {
  if (overpullKlbs <= 0) return 0;
  const depth = (stretchInches * stretchConstant * 1000) / overpullKlbs;
  return Math.round(depth);
}

export function freePointMethod3(
  stretchInches: number,
  overpullLb: number,
  pipeSections: { lengthFt: number; weightLbFt: number }[]
): number {
  if (overpullLb <= 0 || pipeSections.length === 0) return 0;
  let remainingStretch = stretchInches;
  let calculatedDepth = 0;

  for (const sec of pipeSections) {
    const secMaxStretch = (overpullLb * sec.lengthFt) / (sec.weightLbFt * 735294);
    if (remainingStretch <= secMaxStretch) {
      const secDepth = (remainingStretch * sec.weightLbFt * 735294) / overpullLb;
      calculatedDepth += secDepth;
      break;
    } else {
      calculatedDepth += sec.lengthFt;
      remainingStretch -= secMaxStretch;
    }
  }

  return Math.round(calculatedDepth);
}

export function overbalanceGuideline(mudType: 'WBM' | 'SBM' | 'OBM'): { maxOverbalancePsi: number } {
  const maxOverbalancePsi = mudType === 'WBM' ? 1000 : 1500;
  return { maxOverbalancePsi };
}

export function forceToFreePipe(
  stuckLengthFt: number,
  overbalancePsi: number,
  frictionCoefficient: number = 0.2,
  pipeOdInches: number = 5.0
): number {
  const contactAreaSqIn = pipeOdInches * stuckLengthFt * 12;
  const normalForce = contactAreaSqIn * overbalancePsi;
  const forceToFree = normalForce * frictionCoefficient;
  return Math.round(forceToFree);
}

export function washoutDepth(
  strokesToPressureDrop: number,
  opBblStk: number,
  dpCapacityBblFt: number
): number {
  const vToWashoutBbl = strokesToPressureDrop * opBblStk;
  const depth = vToWashoutBbl / dpCapacityBblFt;
  return Math.round(depth);
}
