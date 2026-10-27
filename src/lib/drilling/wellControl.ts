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
