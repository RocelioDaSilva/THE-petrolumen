/**
 * Well Control Engine
 * Sourced from Colin Cormack, "An Introduction to Well Control Calculations for Drilling Operations"
 * (Springer, 2017), Section 3 & Section 4.
 *
 * NOTE: Every function explicitly separates TVD from MD to prevent unit/depth confusion.
 */

import { HYDROSTATIC_CONSTANT } from '../math/constants';
import { CompanyRounding, roundKillMW, roundMaxMW } from '../math/rounding';

export interface AnnularSection {
  name: string;
  capacityBblFt: number;
  lengthFt: number;
}

export interface InfluxHeightResult {
  totalHeightFt: number;
  spilledOver: boolean;
  sectionBreakdown: { name: string; heightFt: number; volumeBbl: number }[];
}

export interface WellControlValidation {
  isValid: boolean;
  warnings: string[];
  errors: string[];
}

/**
 * MASICP: Maximum Allowable Surface Pressure / Shut-In Casing Pressure
 * Sourced: Carter Ch. 3, Eq. 3.1
 * MASICP = (LOT - MWc) * 0.052 * Csgd
 */
export function masicp(lotPpg: number, mwcPpg: number, csgDTVDFt: number): number {
  return (lotPpg - mwcPpg) * HYDROSTATIC_CONSTANT * csgDTVDFt;
}

/**
 * Kill Mud Weight (rounds UP to 1 decimal place per Cormack rule)
 * Sourced: Carter Ch. 3, Eq. 3.2
 */
export function killMudWeight_carter(sidppPsi: number, tvdFt: number, mwcPpg: number): number {
  return killMudWeight(sidppPsi, tvdFt, mwcPpg);
}

/**
 * Initial Circulating Pressure (ICP)
 * Sourced: Carter Ch. 3, Eq. 3.3
 */
export function initialCirculatingPressure(sidppPsi: number, krpPsi: number): number {
  return icp(krpPsi, sidppPsi);
}

/**
 * Final Circulating Pressure (FCP)
 * Sourced: Carter Ch. 3, Eq. 3.4
 */
export function finalCirculatingPressure(kmwPpg: number, krpPsi: number, mwcPpg: number): number {
  return fcp(kmwPpg, mwcPpg, krpPsi);
}

/**
 * Strokes per line on pressure chart
 * Sourced: Carter Ch. 3, Eq. 3.5
 */
export function strokesPerLine(spbStrokes: number, lines: number = 10): number {
  return spbStrokes / lines;
}

/**
 * Pressure decrease per line on pressure chart
 * Sourced: Carter Ch. 3, Eq. 3.6
 */
export function pressureDecreasePerLine(icpPsi: number, fcpPsi: number, lines: number = 10): number {
  return (icpPsi - fcpPsi) / lines;
}

/**
 * Digital pressure chart schedule
 * Sourced: Carter Ch. 3, Section 3.2
 */
export function pressureChart_digital(icpPsi: number, fcpPsi: number, spbStrokes: number, lines: number = 10): { stroke: number; pressure: number }[] {
  const chart: { stroke: number; pressure: number }[] = [];
  const dStrokes = strokesPerLine(spbStrokes, lines);
  const dP = pressureDecreasePerLine(icpPsi, fcpPsi, lines);
  for (let i = 0; i <= lines; i++) {
    chart.push({
      stroke: Math.round(i * dStrokes),
      pressure: Math.round(icpPsi - i * dP),
    });
  }
  return chart;
}

/**
 * Analog pressure chart schedule
 * Sourced: Carter Ch. 3, Section 3.2
 */
export function pressureChart_analog(icpPsi: number, fcpPsi: number, stbTimeMin: number, lines: number = 10): { timeMin: number; pressure: number }[] {
  const chart: { timeMin: number; pressure: number }[] = [];
  const dt = stbTimeMin / lines;
  const dP = pressureDecreasePerLine(icpPsi, fcpPsi, lines);
  for (let i = 0; i <= lines; i++) {
    chart.push({
      timeMin: Math.round(i * dt * 10) / 10,
      pressure: Math.round(icpPsi - i * dP),
    });
  }
  return chart;
}

/**
 * Tapered string section strokes
 * Sourced: Carter Ch. 3, Eq. 3.7
 */
export function sectionStrokes(lengthFt: number, capacityBblFt: number, pumpOutputBblStk: number): number {
  return (lengthFt * capacityBblFt) / pumpOutputBblStk;
}

/**
 * Tapered string section pressure
 * Sourced: Carter Ch. 3, Eq. 3.8
 */
export function sectionPressure(icpPsi: number, fcpPsi: number, sectionLengthFt: number, totalLengthFt: number): number {
  return icpPsi - ((icpPsi - fcpPsi) * sectionLengthFt) / totalLengthFt;
}

/**
 * Tapered kill sheet calculations
 * Sourced: Carter Ch. 3, Section 3.3
 */
export function taperedKillSheet(sections: { name: string; lengthFt: number; capacityBblFt: number }[], icpPsi: number, fcpPsi: number, pumpOutputBblStk: number): { name: string; cumulativeStrokes: number; pressureAtEnd: number }[] {
  const totalLength = sections.reduce((sum, s) => sum + s.lengthFt, 0);
  let cumStrokes = 0;
  let cumLength = 0;
  return sections.map((sec) => {
    const stks = sectionStrokes(sec.lengthFt, sec.capacityBblFt, pumpOutputBblStk);
    cumStrokes += stks;
    cumLength += sec.lengthFt;
    const pEnd = sectionPressure(icpPsi, fcpPsi, cumLength, totalLength);
    return {
      name: sec.name,
      cumulativeStrokes: Math.round(cumStrokes),
      pressureAtEnd: Math.round(pEnd),
    };
  });
}

/**
 * Strokes to KOP in deviated well
 * Sourced: Carter Ch. 3, Eq. 3.9
 */
export function strokesToKOP(cdpBblFt: number, mdKopFt: number, opBblStk: number): number {
  return (cdpBblFt * mdKopFt) / opBblStk;
}

/**
 * Strokes from KOP to bit in deviated well
 * Sourced: Carter Ch. 3, Eq. 3.10
 */
export function strokesFromKOP(cdpBblFt: number, mdBitFt: number, mdKopFt: number, opBblStk: number): number {
  return (cdpBblFt * (mdBitFt - mdKopFt)) / opBblStk;
}

/**
 * Kill weight mud in deviated well
 * Sourced: Carter Ch. 3, Eq. 3.11
 */
export function killWeightMudDeviated(sidppPsi: number, tvdTdFt: number, mwcPpg: number): number {
  return killMudWeight(sidppPsi, tvdTdFt, mwcPpg);
}

/**
 * Circulating pressure at KOP
 * Sourced: Carter Ch. 3, Eq. 3.12
 */
export function circulatingPressureAtKOP(icpPsi: number, kmwPpg: number, mwcPpg: number, tvdKopFt: number, tvdTdFt: number, sidppPsi: number, krpPsi: number): number {
  const fcpVal = finalCirculatingPressure(kmwPpg, krpPsi, mwcPpg);
  return icpPsi - ((icpPsi - fcpVal) * tvdKopFt) / tvdTdFt;
}

/**
 * MASP Method 1 (Gas column to surface)
 * Sourced: Carter Ch. 3, Eq. 3.13
 */
export function masp_method1(mwmPpg: number, mwsfPpg: number, tvdFt: number, gGasPsiFt: number = 0.115): number {
  return (mwsfPpg - mwmPpg) * HYDROSTATIC_CONSTANT * tvdFt + (mwmPpg * HYDROSTATIC_CONSTANT - gGasPsiFt) * tvdFt;
}

/**
 * MASP Method 2 (Fracture gradient & gas column)
 * Sourced: Carter Ch. 3, Eq. 3.14
 */
export function masp_method2(fgPpg: number, mwsfPpg: number, tvdCsgFt: number, tvdTdFt: number, gGasPsiFt: number = 0.115): number {
  return (fgPpg - mwsfPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt - gGasPsiFt * (tvdTdFt - tvdCsgFt);
}

/**
 * Trip margin
 * Sourced: Carter Ch. 3, Eq. 3.15
 */
export function tripMargin(yp: number, dhInches: number, dpInches: number): number {
  return yp / (11.7 * (dhInches - dpInches));
}

/**
 * Diverter line diameter
 * Sourced: Carter Ch. 3, Eq. 3.16
 */
export function diverterLineDiameter(dhInches: number, dpInches: number): number {
  return Math.sqrt(Math.pow(dhInches, 2) - Math.pow(dpInches, 2));
}

/**
 * Matthews & Kelly fracture gradient (Louisiana Offshore)
 * Sourced: Carter Ch. 3, Eq. 3.17
 */
export function fgMatthewsKelly_Louisiana(pGradPsiFt: number, tvdFt: number): number {
  const ki = 0.5 + 3e-5 * tvdFt;
  const obg = 1.0;
  const fgPsiFt = pGradPsiFt + ki * (obg - pGradPsiFt);
  return fgPsiFt / HYDROSTATIC_CONSTANT;
}

/**
 * Matthews & Kelly fracture gradient (Texas Gulf Coast)
 * Sourced: Carter Ch. 3, Eq. 3.18
 */
export function fgMatthewsKelly_Texas(pGradPsiFt: number, tvdFt: number): number {
  const ki = 0.6 + 2.5e-5 * tvdFt;
  const obg = 1.0;
  const fgPsiFt = pGradPsiFt + ki * (obg - pGradPsiFt);
  return fgPsiFt / HYDROSTATIC_CONSTANT;
}

/**
 * Eaton Overburden Gradient curve approximation
 * Sourced: Carter Ch. 3, Section 3.8
 */
export function eatonOverburdenGradient(tvdFt: number): number {
  return 0.85 + 0.15 * (1 - Math.exp(-tvdFt / 5000));
}

/**
 * Eaton Poisson's Ratio curve approximation
 * Sourced: Carter Ch. 3, Section 3.8
 */
export function eatonPoissonRatio(tvdFt: number): number {
  return 0.25 + 0.2 * (tvdFt / 20000);
}

/**
 * Eaton Fracture Gradient
 * Sourced: Carter Ch. 3, Eq. 3.19
 */
export function fgEaton(obgPsiFt: number, pGradPsiFt: number, poissonRatio: number): number {
  const fgPsiFt = pGradPsiFt + (poissonRatio / (1 - poissonRatio)) * (obgPsiFt - pGradPsiFt);
  return fgPsiFt / HYDROSTATIC_CONSTANT;
}

/**
 * Subsea Fracture Gradient
 * Sourced: Carter Ch. 3, Eq. 3.20
 */
export function fgSubsea(obgPsiFt: number, pGradPsiFt: number, poissonRatio: number, waterDepthFt: number, airGapFt: number, tvdFt: number): number {
  const seaWaterGrad = 0.444;
  const obgAdj = (seaWaterGrad * waterDepthFt + obgPsiFt * (tvdFt - waterDepthFt - airGapFt)) / tvdFt;
  return fgEaton(obgAdj, pGradPsiFt, poissonRatio);
}

/**
 * FIT Surface Pressure Method 1
 * Sourced: Carter Ch. 3, Eq. 3.21
 */
export function surfacePressure_FIT_method1(mwmPpg: number, mwcPpg: number, tvdCsgFt: number): number {
  return (mwmPpg - mwcPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt;
}

/**
 * FIT Surface Pressure Method 2
 * Sourced: Carter Ch. 3, Eq. 3.22
 */
export function surfacePressure_FIT_method2(targetEmwPpg: number, mwcPpg: number, tvdCsgFt: number): number {
  return (targetEmwPpg - mwcPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt;
}

/**
 * FIT Surface Pressure Method 3
 * Sourced: Carter Ch. 3, Eq. 3.23
 */
export function surfacePressure_FIT_method3(fgPpg: number, mwcPpg: number, tvdCsgFt: number): number {
  return (fgPpg - mwcPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt;
}

/**
 * Maximum allowable pressure line
 * Sourced: Carter Ch. 3, Eq. 3.24
 */
export function maxAllowablePressureLine(overburdenPsiFt: number, sf: number, tvdCsgFt: number, mwPpg: number): number {
  return (overburdenPsiFt * sf - mwPpg * HYDROSTATIC_CONSTANT) * tvdCsgFt;
}

/**
 * Estimated LOT pressure line
 * Sourced: Carter Ch. 3, Eq. 3.25
 */
export function estimatedLOTPressureLine(fgPpg: number, mwPpg: number, tvdCsgFt: number): number {
  return (fgPpg - mwPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt;
}

/**
 * Minimum acceptable LOT pressure line
 * Sourced: Carter Ch. 3, Eq. 3.26
 */
export function minAcceptableLOTPressureLine(mwMxiPpg: number, mwPpg: number, tvdCsgFt: number): number {
  return (mwMxiPpg - mwPpg) * HYDROSTATIC_CONSTANT * tvdCsgFt;
}

/**
 * Mud compressibility factor
 * Sourced: Carter Ch. 3, Eq. 3.27
 */
export function mudCompressibility(waterPct: number, oilPct: number, solidsPct: number): number {
  return (waterPct * 3.0 + oilPct * 5.0 + solidsPct * 0.5) / 100;
}

/**
 * LOT graph slope
 * Sourced: Carter Ch. 3, Eq. 3.28
 */
export function lotGraphSlope(cm: number, vSystemBbl: number): number {
  return 10000 / (vSystemBbl * (cm / 100));
}

/**
 * Maximum allowable mud weight from LOT
 * Sourced: Carter Ch. 3, Eq. 3.29
 */
export function maxAllowableMudWeight(lotPsi: number, tvdCsgFt: number, mwPpg: number): number {
  return maxMudWeight(lotPsi, tvdCsgFt, mwPpg);
}

/**
 * Kick tolerance intensity
 * Sourced: Carter Ch. 3, Eq. 3.30
 */
export function ktIntensity(fgPpg: number, mwPpg: number, sfPpg: number, tmPpg: number, tvdCsgFt: number, tvdTdFt: number): number {
  return ((fgPpg - sfPpg - tmPpg) * tvdCsgFt - mwPpg * (tvdTdFt - tvdCsgFt)) / tvdTdFt;
}

/**
 * Kick tolerance maximum surface pressure
 * Sourced: Carter Ch. 3, Eq. 3.31
 */
export function ktMaximumSurfacePressure(ktiPpg: number, tvdTdFt: number): number {
  return ktiPpg * HYDROSTATIC_CONSTANT * tvdTdFt;
}

/**
 * Kick tolerance maximum formation pressure
 * Sourced: Carter Ch. 3, Eq. 3.32
 */
export function ktMaximumFormationPressure(ktiPpg: number, mwPpg: number, tvdTdFt: number): number {
  return (mwPpg + ktiPpg) * HYDROSTATIC_CONSTANT * tvdTdFt;
}

/**
 * Kick tolerance influx length
 * Sourced: Carter Ch. 3, Eq. 3.33
 */
export function ktInfluxLength(masicpPsi: number, gMudPsiFt: number, gInfluxPsiFt: number): number {
  return masicpPsi / (gMudPsiFt - gInfluxPsiFt);
}

/**
 * Kick tolerance kick volume
 * Sourced: Carter Ch. 3, Eq. 3.34
 */
export function ktVolume(fgPpg: number, tvdCsgFt: number, lInfluxFt: number, caBblFt: number, mwPpg: number, tvdTdFt: number): number {
  return lInfluxFt * caBblFt;
}

/**
 * BHP from SIDPP
 * Sourced: Carter Ch. 3, Eq. 3.35
 */
export function BHPFromSIDPP(sidppPsi: number, mwPpg: number, tvdTdFt: number): number {
  return sidppPsi + mwPpg * HYDROSTATIC_CONSTANT * tvdTdFt;
}

/**
 * SIDPP from formation pressure
 * Sourced: Carter Ch. 3, Eq. 3.36
 */
export function SIDPPFromFP(pfPsi: number, mwPpg: number, tvdTdFt: number): number {
  return pfPsi - mwPpg * HYDROSTATIC_CONSTANT * tvdTdFt;
}

/**
 * SICP from formation pressure and influx
 * Sourced: Carter Ch. 3, Eq. 3.37
 */
export function SICPFromFP(pfPsi: number, mwPpg: number, tvdTdFt: number, gInfluxPsiFt: number, lInfluxFt: number): number {
  return pfPsi - mwPpg * HYDROSTATIC_CONSTANT * (tvdTdFt - lInfluxFt) - gInfluxPsiFt * lInfluxFt;
}

/**
 * Influx length single section
 * Sourced: Carter Ch. 3, Eq. 3.38
 */
export function influxLength(vKickBbl: number, caBblFt: number): number {
  return vKickBbl / caBblFt;
}

/**
 * Influx length multi-section
 * Sourced: Carter Ch. 3, Eq. 3.39
 */
export function influxLengthMultiSection(vKickBbl: number, cDcOhBblFt: number, lDcFt: number, cDpOhBblFt: number): number {
  const vDc = cDcOhBblFt * lDcFt;
  if (vKickBbl <= vDc) {
    return vKickBbl / cDcOhBblFt;
  }
  return lDcFt + (vKickBbl - vDc) / cDpOhBblFt;
}

/**
 * Influx type from density
 * Sourced: Carter Ch. 3, Table 3.1
 */
export function influxTypeFromDensity(wkPpg: number): "Gas" | "Combination Gas/Oil" | "Oil" | "Salt Water" {
  if (wkPpg <= 3.0) return "Gas";
  if (wkPpg <= 5.0) return "Combination Gas/Oil";
  if (wkPpg <= 7.0) return "Oil";
  return "Salt Water";
}

/**
 * Original mud weight from gas-cut mud
 * Sourced: Carter Ch. 3, Eq. 3.40
 */
export function originalMudWeightFromGasCut(mwGc: number, mwD: number, mwBl: number): number {
  return (mwGc * mwD) / mwBl;
}

/**
 * Gas content fraction from cut mud
 * Sourced: Carter Ch. 3, Eq. 3.41
 */
export function gasContentFromCutMud(mwOrig: number, mwCut: number): number {
  return (mwOrig - mwCut) / mwOrig;
}

/**
 * Reduction in mud weight without a kick
 * Sourced: Carter Ch. 3, Eq. 3.42
 */
export function reductionInMudWeightNoKick(ropFtHr: number, dhInches: number, porosityPct: number, wSolidsPpg: number, mwPpg: number, pBhPsi: number, qGpm: number): number {
  const qCuttings = (ropFtHr * Math.pow(dhInches, 2)) / 1471;
  return (qCuttings * (1 - porosityPct / 100) * (wSolidsPpg - mwPpg)) / (qGpm / 42);
}

/**
 * Gas migration rate
 * Sourced: Carter Ch. 3, Eq. 3.43
 */
export function gasMigrationRate(sicp2Psi: number, sicp1Psi: number, mwPpg: number, timeHours: number): number {
  if (timeHours <= 0 || mwPpg <= 0) return 0;
  return (sicp2Psi - sicp1Psi) / (mwPpg * HYDROSTATIC_CONSTANT * timeHours);
}

/**
 * Hydrostatic pressure decrease from influx
 * Sourced: Carter Ch. 3, Eq. 3.44
 */
export function hpDecreaseFromInflux(tvdFt: number, mwgPpg: number, vKickBbl: number, caBblFt: number, gInfluxPsiFt: number): number {
  const lInflux = vKickBbl / caBblFt;
  return lInflux * (mwgPpg * HYDROSTATIC_CONSTANT - gInfluxPsiFt);
}

/**
 * Hydrostatic pressure decrease gradient method
 * Sourced: Carter Ch. 3, Eq. 3.45
 */
export function hpDecreaseGradientMethod(mwgPpg: number, gInfluxPsiFt: number, caBblFt: number, vKickBbl: number): number {
  return hpDecreaseFromInflux(0, mwgPpg, vKickBbl, caBblFt, gInfluxPsiFt);
}

/**
 * Moore equations - Formation pressure
 * Sourced: Carter Ch. 3, Eq. 3.46
 */
export function mooreFormationPressure(sidppPsi: number, mwPpg: number, tvdFt: number): number {
  return sidppPsi + mwPpg * HYDROSTATIC_CONSTANT * tvdFt;
}

/**
 * Moore equations - Influx length
 * Sourced: Carter Ch. 3, Eq. 3.47
 */
export function mooreInfluxLength(vKickBbl: number, caBblFt: number): number {
  return vKickBbl / caBblFt;
}

/**
 * Moore equations - Influx hydrostatic pressure
 * Sourced: Carter Ch. 3, Eq. 3.48
 */
export function mooreHydrostaticInflux(pfPsi: number, mwPpg: number, tvdFt: number, lInfluxFt: number, sicpPsi: number): number {
  return pfPsi - mwPpg * HYDROSTATIC_CONSTANT * (tvdFt - lInfluxFt) - sicpPsi;
}

/**
 * Moore equations - Influx gradient
 * Sourced: Carter Ch. 3, Eq. 3.49
 */
export function mooreInfluxGradient(pInfluxPsi: number, lInfluxFt: number): number {
  if (lInfluxFt <= 0) return 0;
  return pInfluxPsi / lInfluxFt;
}

/**
 * Moore equations - Temperature in Rankine
 * Sourced: Carter Ch. 3, Eq. 3.50
 */
export function mooreTemperatureRankin(tSurfaceDegF: number, tempGradDegFFt: number, tvdFt: number): number {
  return tSurfaceDegF + tempGradDegFFt * tvdFt + 459.67;
}

/**
 * Moore equations - Pressure at top of gas bubble
 * Sourced: Carter Ch. 3, Eq. 3.51
 */
export function moorePressureAtTopOfBubble(aBblFt: number, mwgPpg: number, pfPsi: number, zFactor: number, tCsgR: number, lInfluxFt: number, tvdTdFt: number): number {
  const hpMudAbove = mwgPpg * HYDROSTATIC_CONSTANT * (tvdTdFt - lInfluxFt);
  return pfPsi - hpMudAbove;
}

/**
 * Moore equations - Kill weight mud
 * Sourced: Carter Ch. 3, Eq. 3.52
 */
export function mooreKillWeightMud(sidppPsi: number, tvdFt: number, mwPpg: number): number {
  return killMudWeight(sidppPsi, tvdFt, mwPpg);
}

/**
 * Moore equations - Pressure at casing shoe
 * Sourced: Carter Ch. 3, Eq. 3.53
 */
export function moorePressureAtShoe(pSurfacePsi: number, mwPpg: number, tvdShoeFt: number): number {
  return pSurfacePsi + mwPpg * HYDROSTATIC_CONSTANT * tvdShoeFt;
}

/**
 * Gas flow into wellbore
 * Sourced: Carter Ch. 3, Eq. 3.54
 */
export function gasFlowIntoWellbore(kMd: number, pDiffPsi: number, lFt: number, muCp: number, reFt: number, rwFt: number): number {
  return (0.00708 * kMd * pDiffPsi * lFt) / (muCp * Math.log(reFt / rwFt));
}

/**
 * Gas flow through choke
 * Sourced: Carter Ch. 3, Eq. 3.55
 */
export function gasFlowThroughChoke(cd: number, pUpstreamPsi: number, gasSg: number, tempR: number): number {
  return 825 * cd * pUpstreamPsi * Math.sqrt(gasSg / tempR);
}

/**
 * Workover MATP Initial
 * Sourced: Carter Ch. 3, Eq. 3.56
 */
export function matpInitial(fgPpg: number, tvdPerfsFt: number, hptPsi: number): number {
  return fgPpg * HYDROSTATIC_CONSTANT * tvdPerfsFt - hptPsi;
}

/**
 * Workover MATP Final
 * Sourced: Carter Ch. 3, Eq. 3.57
 */
export function matpFinal(fgPpg: number, tvdPerfsFt: number, hptPsi: number, kwfPpg: number): number {
  return fgPpg * HYDROSTATIC_CONSTANT * tvdPerfsFt - kwfPpg * HYDROSTATIC_CONSTANT * tvdPerfsFt;
}

/**
 * Tubing capacity to perforations
 * Sourced: Carter Ch. 3, Eq. 3.58
 */
export function tubingCapacityToPerfs(cTubingBblFt: number, dPerfsFt: number): number {
  return cTubingBblFt * dPerfsFt;
}

/**
 * Pressure reduction per barrel
 * Sourced: Carter Ch. 3, Eq. 3.59
 */
export function pressureReductionPerBarrel(cTubingBblFt: number, kwfPpg: number): number {
  return (kwfPpg * HYDROSTATIC_CONSTANT) / cTubingBblFt;
}

/**
 * Pressure to bleed off
 * Sourced: Carter Ch. 3, Eq. 3.60
 */
export function pressureToBleedOff(vLubeBbl: number, mwPpg: number, cTubingBblFt: number): number {
  return (vLubeBbl / cTubingBblFt) * mwPpg * HYDROSTATIC_CONSTANT;
}

/**
 * Lubricate & bleed volume method
 * Sourced: Carter Ch. 3, Eq. 3.61
 */
export function lubeVolumeMethod(gMudPsiFt: number, cAnnulusBblFt: number): number {
  return gMudPsiFt * cAnnulusBblFt;
}

/**
 * Lubricate & bleed pressure method
 * Sourced: Carter Ch. 3, Eq. 3.62
 */
export function lubePressureMethod(p1Psi: number, p2Psi: number): number {
  return p1Psi - p2Psi;
}

/**
 * Barite plug open hole capacity
 * Sourced: Carter Ch. 3, Eq. 3.63
 */
export function baritePlug_ohCapacity(dBitInches: number, washOutPct: number = 0): number {
  const dEffective = dBitInches * (1 + washOutPct / 100);
  return Math.pow(dEffective, 2) / 1029.4;
}

/**
 * Barite plug base liquid volume
 * Sourced: Carter Ch. 3, Eq. 3.64
 */
export function baritePlug_baseLiquid(vPlugBbl: number, wMudSg: number, mwLiquidPpg: number, mwPlugPpg: number): number {
  return vPlugBbl * ((mwPlugPpg - wMudSg * 8.34) / (mwPlugPpg - mwLiquidPpg));
}

/**
 * Barite plug length with pipe in hole
 * Sourced: Carter Ch. 3, Eq. 3.65
 */
export function baritePlug_lengthWithPipe(vPlugBbl: number, cAnnularBblFt: number): number {
  return vPlugBbl / cAnnularBblFt;
}

/**
 * Barite plug length without pipe in hole
 * Sourced: Carter Ch. 3, Eq. 3.66
 */
export function baritePlug_lengthNoPipe(vPlugBbl: number, cHoleBblFt: number): number {
  return vPlugBbl / cHoleBblFt;
}

/**
 * Barite plug sacks required
 * Sourced: Carter Ch. 3, Eq. 3.67
 */
export function baritePlug_sacks(vPlugBbl: number, sacksPerBbl: number = 14.7): number {
  return Math.round(vPlugBbl * sacksPerBbl);
}

/**
 * Formation pressure from SIDPP: String HP + SIDPP
 * Sourced: Cormack Sect. 4, Eq. 4.1
 */
export function formationPressureFromSIDPP(tvd: number, currentMW: number, sidpp: number): number {
  const hp = currentMW * HYDROSTATIC_CONSTANT * tvd;
  return CompanyRounding.pressure(hp + sidpp);
}

/**
 * Formation pressure from known gradient: gradient * TVD
 */
export function formationPressureFromGradient(gradientPsiFt: number, tvd: number): number {
  return CompanyRounding.pressure(gradientPsiFt * tvd);
}

/**
 * Kill Mud Weight: SIDPP / (TVD * 0.052) + Current MW
 * Sourced: Cormack Sect. 4, Eq. 4.2
 * MANDATORY: Always round UP to 1 decimal place.
 * E.g., Cormack Sect. 4, Well Three: 12.21 ppg -> 12.3 ppg
 */
export function killMudWeight(sidpp: number, tvd: number, currentMW: number): number {
  if (tvd <= 0) return currentMW;
  const rawKmw = sidpp / (tvd * HYDROSTATIC_CONSTANT) + currentMW;
  return roundKillMW(rawKmw);
}

/**
 * Initial Circulating Pressure (ICP): SCR + SIDPP
 * Sourced: Cormack Sect. 4, Eq. 4.3
 */
export function icp(scr: number, sidpp: number): number {
  return CompanyRounding.pressure(scr + sidpp);
}

/**
 * Final Circulating Pressure (FCP): (Kill MW / Current MW) * SCR
 * Sourced: Cormack Sect. 4, Eq. 4.4
 */
export function fcp(killMW: number, currentMW: number, scr: number): number {
  if (currentMW <= 0) return scr;
  return CompanyRounding.pressure((killMW / currentMW) * scr);
}

/**
 * Maximum Mud Weight from LOT: LOT / (Shoe TVD * 0.052) + Test MW
 * Sourced: Cormack Sect. 3, Worked Example
 * MANDATORY: Always round DOWN to 1 decimal place.
 * E.g., Cormack Sect. 3: 14.68 ppg -> 14.6 ppg
 */
export function maxMudWeight(lotPressure: number, shoeTVD: number, testMW: number): number {
  if (shoeTVD <= 0) return testMW;
  const rawMax = lotPressure / (shoeTVD * HYDROSTATIC_CONSTANT) + testMW;
  return roundMaxMW(rawMax);
}

/**
 * Fracture Pressure at Casing Shoe: Test MW * 0.052 * Shoe TVD + LOT Pressure
 * Sourced: Cormack Sect. 3, Eq. 3.3
 */
export function fracturePressure(testMW: number, shoeTVD: number, lotPressure: number): number {
  const hp = testMW * HYDROSTATIC_CONSTANT * shoeTVD;
  return CompanyRounding.pressure(hp + lotPressure);
}

/**
 * Fracture Gradient in psi/ft: Fracture Pressure / Shoe TVD
 */
export function fractureGradient(fracturePress: number, shoeTVD: number): number {
  if (shoeTVD <= 0) return 0;
  return CompanyRounding.gradient(fracturePress / shoeTVD);
}

/**
 * MAASP (Maximum Allowable Annular Surface Pressure):
 * (Max MW - Current MW) * 0.052 * Shoe TVD
 * Sourced: Cormack Sect. 3, Eq. 3.4
 */
export function maasp(maxMW: number, currentMW: number, shoeTVD: number): number {
  const rawMaasp = (maxMW - currentMW) * HYDROSTATIC_CONSTANT * shoeTVD;
  return CompanyRounding.pressure(rawMaasp);
}

/**
 * Bottom Hole Circulating Pressure (BHCP): Hydrostatic + Annular Pressure Loss (APL)
 */
export function bhcp(hydrostaticPressure: number, apl: number): number {
  return CompanyRounding.pressure(hydrostaticPressure + apl);
}

/**
 * Equivalent Circulating Density (ECD): APL / (TVD * 0.052) + Current MW
 */
export function ecd(apl: number, tvd: number, currentMW: number): number {
  if (tvd <= 0) return currentMW;
  return CompanyRounding.mudWeight(apl / (tvd * HYDROSTATIC_CONSTANT) + currentMW);
}

/**
 * Influx Height: Walks an ordered list of annular sections (e.g. DC-OH then DP-OH)
 * Sourced: Cormack Sect. 4, Influx Height
 * Golden Test: Cormack Sect. 4, Well Two: 25 bbl kick in 500 ft DC-OH (0.029 bbl/ft)
 * DC-OH holds 14.5 bbl (500 ft); remaining 10.5 bbl fills DP-OH (0.0347 bbl/ft) = 302 ft -> Total = 802 ft!
 */
export function influxHeight(kickSizeBbl: number, sections: AnnularSection[]): InfluxHeightResult {
  let remainingKick = kickSizeBbl;
  let totalHeightFt = 0;
  let spilledOver = false;
  const sectionBreakdown: { name: string; heightFt: number; volumeBbl: number }[] = [];

  for (let i = 0; i < sections.length; i++) {
    const sec = sections[i];
    if (remainingKick <= 0) break;

    const secCapacity = Math.max(0.001, sec.capacityBblFt);
    const maxSecVol = secCapacity * sec.lengthFt;

    if (remainingKick <= maxSecVol || i === sections.length - 1) {
      // Influx fits inside this section (or reaches top)
      const h = remainingKick / secCapacity;
      sectionBreakdown.push({
        name: sec.name,
        heightFt: CompanyRounding.volume(h),
        volumeBbl: CompanyRounding.volume(remainingKick),
      });
      totalHeightFt += h;
      remainingKick = 0;
    } else {
      // Influx fills this entire section and spills into the next
      spilledOver = true;
      sectionBreakdown.push({
        name: sec.name,
        heightFt: sec.lengthFt,
        volumeBbl: CompanyRounding.volume(maxSecVol),
      });
      totalHeightFt += sec.lengthFt;
      remainingKick -= maxSecVol;
    }
  }

  return {
    totalHeightFt: Math.round(totalHeightFt),
    spilledOver,
    sectionBreakdown,
  };
}

/**
 * Influx Gradient in psi/ft: (Current MW * 0.052) - ((SICP - SIDPP) / Influx Height)
 * Sourced: Cormack Sect. 4, Eq. 4.5
 */
export function influxGradient(
  sicp: number,
  sidpp: number,
  currentMW: number,
  influxHt: number
): number {
  if (influxHt <= 0) return 0;
  const grad = currentMW * HYDROSTATIC_CONSTANT - (sicp - sidpp) / influxHt;
  return CompanyRounding.gradient(grad);
}

/**
 * Pressure reduction per 100 strokes during Wait & Weight step-down:
 * (ICP - FCP) / Surface-to-Bit Strokes * 100
 * Sourced: Cormack Sect. 4, Eq. 4.6
 */
export function pressureReductionPer100Strokes(
  icpVal: number,
  fcpVal: number,
  surfaceToBitStrokes: number
): number {
  if (surfaceToBitStrokes <= 0) return 0;
  return CompanyRounding.volume(((icpVal - fcpVal) / surfaceToBitStrokes) * 100);
}

/**
 * Wet and Dry Tripping Pressure Loss (Swab / Surge)
 * Sourced: Cormack Sect. 3, Q11 (Golden Test expected: 469 psi for wet trip)
 */
export function trippingPressureLoss(
  mw: number,
  displacementBblFt: number,
  casingCapacityBblFt: number,
  standLengthFt: number,
  numStands: number
): { deltaPPerFt: number; totalDeltaP: number } {
  const denom = Math.max(0.001, casingCapacityBblFt - displacementBblFt);
  const deltaPPerFt = (mw * HYDROSTATIC_CONSTANT * displacementBblFt) / denom;
  const totalLength = standLengthFt * numStands;
  const totalDeltaP = deltaPPerFt * totalLength;

  return {
    deltaPPerFt: CompanyRounding.capacity(deltaPPerFt),
    totalDeltaP: Math.round(totalDeltaP),
  };
}

/**
 * Comprehensive Well Control Safety Validator
 */
export function validateWellControl(inputs: {
  tvd: number;
  shoeTVD: number;
  currentMW: number;
  maxMW: number;
  killMW: number;
  sidpp: number;
  sicp: number;
}): WellControlValidation {
  const warnings: string[] = [];
  const errors: string[] = [];

  if (inputs.tvd <= 0) {
    errors.push('TVD deve ser maior que 0.');
  }
  if (inputs.shoeTVD > inputs.tvd) {
    errors.push(`TVD da Sapata (${inputs.shoeTVD} ft) não pode ser maior que o TVD total do poço (${inputs.tvd} ft).`);
  }
  if (inputs.sidpp < 0) {
    errors.push('SIDPP não pode ser negativo.');
  }
  if (inputs.sicp < inputs.sidpp) {
    warnings.push('SICP é menor que SIDPP. Em influxos normais no anular, SICP deve ser maior ou igual ao SIDPP.');
  }
  if (inputs.currentMW >= inputs.maxMW) {
    warnings.push(`Densidade atual (${inputs.currentMW} ppg) excede a densidade máxima (${inputs.maxMW} ppg). MAASP é nulo ou negativo!`);
  }
  if (inputs.killMW <= inputs.currentMW && inputs.sidpp > 0) {
    warnings.push('Kill Mud Weight deve ser maior que a lama atual para amortecer o poço.');
  }

  return {
    isValid: errors.length === 0,
    warnings,
    errors,
  };
}
