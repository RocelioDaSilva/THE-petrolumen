/**
 * Air & Gas Drilling Engine (USCS + SI)
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 8.
 */

export interface AirGasCirculationResult {
  bottomHolePressurePsia: number;
  bottomHolePressurePsig: number;
  bottomHolePressureBar: number;
  injectionPressurePsia: number;
  injectionPressurePsig: number;
}

export function staticGasColumnBHP(
  pSurfacePsia: number,
  gasSpecificGravity: number,
  depthFt: number,
  tempAvgR: number = 540,
  zAvg: number = 0.95
): AirGasCirculationResult {
  const pb = pSurfacePsia * (1 + 0.128 * (depthFt / 10000));
  const psig = pb - 14.7;
  const bar = pb / 14.5038;
  return {
    bottomHolePressurePsia: Math.round(pb * 10) / 10,
    bottomHolePressurePsig: Math.round(psig * 10) / 10,
    bottomHolePressureBar: Math.round(bar * 100) / 100,
    injectionPressurePsia: Math.round(pSurfacePsia * 10) / 10,
    injectionPressurePsig: Math.round((pSurfacePsia - 14.7) * 10) / 10,
  };
}

export function directCirculationPressure(
  flowRateScfm: number,
  gasSg: number,
  depthFt: number,
  dpIdInches: number,
  dhInches: number,
  dpOdInches: number
): AirGasCirculationResult {
  const pbh = staticGasColumnBHP(14.7, gasSg, depthFt);
  const pInjPsia = pbh.bottomHolePressurePsia + 0.0001 * flowRateScfm;
  return {
    ...pbh,
    injectionPressurePsia: Math.round(pInjPsia * 10) / 10,
    injectionPressurePsig: Math.round((pInjPsia - 14.7) * 10) / 10,
  };
}

export function reverseCirculationPressure(
  flowRateScfm: number,
  gasSg: number,
  depthFt: number,
  dpIdInches: number,
  dhInches: number,
  dpOdInches: number
): AirGasCirculationResult {
  return directCirculationPressure(flowRateScfm, gasSg, depthFt, dpIdInches, dhInches, dpOdInches);
}
