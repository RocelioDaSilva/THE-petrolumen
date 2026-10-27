/**
 * Surface Facilities & Tank Volume Engine
 * Sourced from Cormack (2017), Section 2: "Volume and Capacity Calculations"
 */

import { FT3_TO_BBL, M3_TO_BBL } from '../math/constants';
import { CompanyRounding } from '../math/rounding';
import { rollUpWellVolumes, TubularComponent, AnnularComponent, KillSheetVolumesResult } from './volumes';

/**
 * Rectangular Mud Pit / Tank Volume in bbl
 * Sourced: Cormack Sect. 2, Eq. 2.9
 * - If unit is 'ft': L * W * D * 0.1781
 * - If unit is 'm': m^3 * 6.2905
 */
export function rectTankVolume(l: number, w: number, d: number, unit: 'ft' | 'm' = 'ft'): number {
  if (unit === 'm') {
    const volM3 = l * w * d;
    return CompanyRounding.volume(volM3 * M3_TO_BBL);
  }
  const volCuFt = l * w * d;
  return CompanyRounding.volume(volCuFt * FT3_TO_BBL);
}

/**
 * Trip tank displacement per stand in bbl
 */
export function tripTankDisplacementPerStand(dispBblFt: number, standLengthFt: number): number {
  return CompanyRounding.volume(dispBblFt * standLengthFt);
}

export interface TripSheetRowInput {
  standNumber: number;
  standLengthFt: number;
  actualTripTankLevelBbl: number;
  transferInBbl?: number;
  transferOutBbl?: number;
}

export interface TripSheetEntry {
  standNumber: number;
  calculatedDisplacementBbl: number;
  actualTripTankLevelBbl: number;
  tankRunningVolumeBbl: number;
  transferBbl: number;
  cumulativeCalculatedBbl: number;
  cumulativeActualBbl: number;
  differenceBbl: number;
  status: 'OK' | 'WARNING_GAIN' | 'WARNING_LOSS' | 'TRANSFER_TRIGGERED';
}

/**
 * Digital Trip Sheet Processor with automatic transfer threshold tracking
 * Sourced from Cormack Sect. 2 worked example (20 bbl tank, 15 bbl transfer threshold)
 */
export function processTripSheet(
  rows: TripSheetRowInput[],
  dispBblFt: number,
  tankCapacityBbl: number = 20,
  transferThresholdBbl: number = 15
): TripSheetEntry[] {
  let cumCalc = 0;
  let cumActual = 0;
  let currentTankVolume = tankCapacityBbl; // starts full or at initial level
  const entries: TripSheetEntry[] = [];

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const calcStand = CompanyRounding.volume(dispBblFt * row.standLengthFt);
    cumCalc = CompanyRounding.volume(cumCalc + calcStand);

    const transferIn = row.transferInBbl || 0;
    const transferOut = row.transferOutBbl || 0;
    const netTransfer = transferIn - transferOut;

    // Tank volume changes as mud is drawn into hole or mud fills tank
    const actualChange = row.actualTripTankLevelBbl;
    cumActual = CompanyRounding.volume(cumActual + actualChange);
    currentTankVolume = CompanyRounding.volume(currentTankVolume - actualChange + netTransfer);

    const diff = CompanyRounding.volume(cumActual - cumCalc);

    let status: 'OK' | 'WARNING_GAIN' | 'WARNING_LOSS' | 'TRANSFER_TRIGGERED' = 'OK';
    if (currentTankVolume <= tankCapacityBbl - transferThresholdBbl || currentTankVolume <= 5) {
      status = 'TRANSFER_TRIGGERED';
    } else if (diff > 1.5) {
      status = 'WARNING_GAIN'; // hole took less mud than expected -> swab / kick
    } else if (diff < -1.5) {
      status = 'WARNING_LOSS'; // hole took more mud than expected -> fluid loss
    }

    entries.push({
      standNumber: row.standNumber,
      calculatedDisplacementBbl: calcStand,
      actualTripTankLevelBbl: row.actualTripTankLevelBbl,
      tankRunningVolumeBbl: currentTankVolume,
      transferBbl: netTransfer,
      cumulativeCalculatedBbl: cumCalc,
      cumulativeActualBbl: cumActual,
      differenceBbl: diff,
      status,
    });
  }

  return entries;
}

export interface WellModel {
  stringComponents: TubularComponent[];
  annularComponents: AnnularComponent[];
}

/**
 * Sourced: Cormack Sect. 2, Q1
 * Golden Test expected:
 * String = 164.32 bbl
 * Annulus = 1,147.04 bbl
 * Total Well = 1,311.36 bbl
 */
export function killSheetVolume(well: WellModel): KillSheetVolumesResult {
  return rollUpWellVolumes(well.stringComponents, well.annularComponents);
}
