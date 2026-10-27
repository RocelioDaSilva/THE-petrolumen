/**
 * Volume Engine: String, Hole, Annular capacities, displacements and volume roll-ups
 * Directly based on Cormack (2017), Section 2: "Volume and Capacity Calculations"
 */

import { CAPACITY_CONSTANT, STEEL_LB_PER_BBL } from '../math/constants';
import { CompanyRounding } from '../math/rounding';

/**
 * Hole capacity in bbl/ft: d^2 / 1029.4
 * Sourced: Cormack Sect. 2, Eq. 2.1
 */
export function holeCapacity(diameterIn: number): number {
  const d = Math.max(0.1, diameterIn);
  return CompanyRounding.capacity(Math.pow(d, 2) / CAPACITY_CONSTANT);
}

/**
 * String inner capacity in bbl/ft: id^2 / 1029.4
 * Sourced: Cormack Sect. 2, Eq. 2.2
 */
export function stringCapacity(idIn: number): number {
  const id = Math.max(0.1, idIn);
  return CompanyRounding.capacity(Math.pow(id, 2) / CAPACITY_CONSTANT);
}

/**
 * Annular capacity between hole/casing ID and tubular OD: (D^2 - d^2) / 1029.4
 * Sourced: Cormack Sect. 2, Eq. 2.3
 */
export function annularCapacity(holeID: number, pipeOD: number): number {
  const diff = Math.max(0, Math.pow(holeID, 2) - Math.pow(pipeOD, 2));
  return CompanyRounding.capacity(diff / CAPACITY_CONSTANT);
}

/**
 * Geometric pipe displacement: (OD^2 - ID^2) / 1029.4
 */
export function pipeDisplacement(od: number, id: number): number {
  const diff = Math.max(0, Math.pow(od, 2) - Math.pow(id, 2));
  return CompanyRounding.capacity(diff / CAPACITY_CONSTANT);
}

/**
 * Actual pipe displacement from weight: lb/ft / 2747
 * Sourced: Cormack Sect. 2, Eq. 2.4 (Steel density constant 2747)
 */
export function pipeDisplacementFromWeight(lbPerFt: number): number {
  return CompanyRounding.capacity(lbPerFt / STEEL_LB_PER_BBL);
}

/**
 * Closed-end displacement: pipeCapacity + pipeDisplacement = OD^2 / 1029.4
 * Sourced: Cormack Sect. 2, Eq. 2.5
 */
export function closedEndDisplacement(pipeCap: number, pipeDisp: number): number {
  return CompanyRounding.capacity(pipeCap + pipeDisp);
}

/**
 * Closed-end displacement directly from OD
 */
export function closedEndDisplacementFromOD(odInches: number): number {
  return CompanyRounding.capacity(Math.pow(odInches, 2) / CAPACITY_CONSTANT);
}

/**
 * QA check from Cormack: Annular Capacity = Hole Capacity - Closed-End Displacement
 */
export function annularCapacityFromClosedEnd(holeCap: number, closedEndDisp: number): number {
  return CompanyRounding.capacity(Math.max(0, holeCap - closedEndDisp));
}

/**
 * Volume in bbl: capacity (bbl/ft) * length (ft)
 * Sourced: Cormack Sect. 2, Eq. 2.6
 */
export function volume(capacityBblFt: number, lengthFt: number): number {
  return CompanyRounding.volume(capacityBblFt * lengthFt);
}

export interface TubularComponent {
  name: string;
  type: 'DP' | 'HWDP' | 'DC';
  od: number;
  id: number;
  weightLbFt: number;
  lengthFt: number;
}

export interface AnnularComponent {
  name: string;
  holeOrCasingId: number;
  pipeOd: number;
  lengthFt: number;
}

export interface KillSheetVolumesResult {
  stringVolumes: { name: string; capacity: number; volume: number; displacement: number }[];
  annularVolumes: { name: string; capacity: number; volume: number }[];
  totalStringVolume: number;
  totalAnnularVolume: number;
  totalWellVolume: number;
}

/**
 * Computes roll-up volumes for entire string and annulus sections
 * Directly implements Cormack Sect. 2, Q1 worked example
 */
export function rollUpWellVolumes(
  stringComponents: TubularComponent[],
  annularComponents: AnnularComponent[]
): KillSheetVolumesResult {
  let totalStringVolume = 0;
  const stringVolumes = stringComponents.map((c) => {
    const cap = stringCapacity(c.id);
    const vol = volume(cap, c.lengthFt);
    const disp = volume(pipeDisplacementFromWeight(c.weightLbFt), c.lengthFt);
    totalStringVolume += vol;
    return { name: c.name, capacity: cap, volume: vol, displacement: disp };
  });

  let totalAnnularVolume = 0;
  const annularVolumes = annularComponents.map((a) => {
    const cap = annularCapacity(a.holeOrCasingId, a.pipeOd);
    const vol = volume(cap, a.lengthFt);
    totalAnnularVolume += vol;
    return { name: a.name, capacity: cap, volume: vol };
  });

  return {
    stringVolumes,
    annularVolumes,
    totalStringVolume: CompanyRounding.volume(totalStringVolume),
    totalAnnularVolume: CompanyRounding.volume(totalAnnularVolume),
    totalWellVolume: CompanyRounding.volume(totalStringVolume + totalAnnularVolume),
  };
}
