/**
 * Rate of Penetration (ROP) Engine (Carter v3)
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 */

export function ropMudEffects(rop1FtHr: number, mw1Ppg: number, mw2Ppg: number): number {
  if (mw2Ppg <= 0) return rop1FtHr;
  return Math.round(rop1FtHr * Math.pow(mw1Ppg / mw2Ppg, 2) * 10) / 10;
}

export function cuttingsConcentration(ropFtHr: number, bitDiameterInches: number, flowRateGpm: number): number {
  const qCuttingsBblMin = (ropFtHr * Math.pow(bitDiameterInches, 2)) / 1471 / 60;
  const qMudBblMin = flowRateGpm / 42;
  const ca = (qCuttingsBblMin / (qCuttingsBblMin + qMudBblMin)) * 100;
  return Math.round(ca * 10) / 10;
}

export function dExponent(
  ropFtHr: number,
  rpm: number,
  wobKlbs: number,
  bitDiameterInches: number,
  mwActualPpg: number = 9.0,
  mwNormalPpg: number = 9.0
): { dExp: number; dExponentCorrected: number } {
  const logRopRpm = Math.log10(ropFtHr / (60 * rpm));
  const logWobDia = Math.log10((12 * wobKlbs) / (1000 * bitDiameterInches));
  const d = logRopRpm / logWobDia;
  const dc = d * (mwNormalPpg / mwActualPpg);
  return {
    dExp: Math.round(d * 100) / 100,
    dExponentCorrected: Math.round(dc * 100) / 100,
  };
}

export function drillingCostPerFoot(
  bitCostUSD: number,
  rigRateUSDHr: number,
  drillingTimeHours: number,
  tripTimeHours: number,
  footageDrilledFt: number
): number {
  if (footageDrilledFt <= 0) return 0;
  const totalCost = bitCostUSD + rigRateUSDHr * (drillingTimeHours + tripTimeHours);
  return Math.round((totalCost / footageDrilledFt) * 100) / 100;
}
