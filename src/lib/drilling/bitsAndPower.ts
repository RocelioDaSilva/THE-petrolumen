/**
 * Rig Equipment, Power & Rotary Drilling Bits Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapters 1 & 5.
 */

import { HOISTING_EFFICIENCY_BY_LINES, FUEL_PROPERTIES } from '../math/tables';

/**
 * 1.1 Power System
 * Sourced: Bourgoyne Ch. 1, Eq. 1.1 - 1.3
 */
export function enginePowerHp(torqueFtLbf: number, rpm: number): number {
  // P = 2 * pi * N * T / 33,000 = N * T / 5252.1
  return Math.round(((rpm * torqueFtLbf) / 5252.1) * 10) / 10;
}

/**
 * Heat energy input from fuel in horsepower (1 hp = 2,544.43 Btu/hr)
 */
export function fuelHeatInputHp(
  fuelRateGalPerHr: number,
  fuelType: 'diesel' | 'gasoline' | 'butane' | 'methane' = 'diesel'
): number {
  const prop = FUEL_PROPERTIES[fuelType];
  const massLbPerHr = fuelRateGalPerHr * prop.densityLbmGal;
  const btuPerHr = massLbPerHr * prop.heatingValueBtuLbm;
  return Math.round((btuPerHr / 2544.43) * 10) / 10;
}

export function engineThermalEfficiency(deliveredPowerHp: number, fuelHeatInputHp: number): number {
  if (fuelHeatInputHp <= 0) return 0;
  return Math.round((deliveredPowerHp / fuelHeatInputHp) * 1000) / 1000;
}

/**
 * 1.2 Hoisting System
 * Sourced: Bourgoyne Ch. 1, Section 1.2, Eq. 1.4 - 1.9
 */
export interface HoistingAnalysisResult {
  fastLineTensionLbf: number;
  deadlineTensionLbf: number;
  derrickLoadLbf: number;
  maxEquivalentDerrickLoadLbf: number;
  derrickEfficiencyFactor: number;
  hookHorsepower: number;
  hoistingSpeedFtMin: number;
}

export function calculateHoistingSystem(
  hookLoadLbf: number,
  numberOfLinesStrung: number = 8,
  inputDrawworksHp: number = 1000,
  customEfficiency?: number
): HoistingAnalysisResult {
  const n = Math.max(4, numberOfLinesStrung);
  const E = customEfficiency !== undefined
    ? customEfficiency
    : (HOISTING_EFFICIENCY_BY_LINES[n] || 0.841);

  // Fast-line tension: F_f = W / (E * n) (Bourgoyne Eq. 1.4)
  const fastLineTension = hookLoadLbf / (E * n);

  // Dead-line tension: F_s = W / n
  const deadlineTension = hookLoadLbf / n;

  // Total derrick load: F_d = W + F_f + F_s = ((1 + E + E*n) / (E*n)) * W (Bourgoyne Eq. 1.5)
  const derrickLoad = ((1 + E + E * n) / (E * n)) * hookLoadLbf;

  // Maximum equivalent derrick load for symmetrical 4-leg design (Eq. 1.7)
  const maxEqDerrickLoad = ((n + 4) / n) * hookLoadLbf;

  // Derrick efficiency factor
  const derrickEff = maxEqDerrickLoad > 0 ? derrickLoad / maxEqDerrickLoad : 1.0;

  // Hook horsepower: P_h = E * P_i (Eq. 1.8)
  const hookHp = E * inputDrawworksHp;

  // Maximum hoisting speed: v_h = P_h * 33,000 / W (ft/min)
  const hoistingSpeed = hookLoadLbf > 0 ? (hookHp * 33000) / hookLoadLbf : 0;

  return {
    fastLineTensionLbf: Math.round(fastLineTension),
    deadlineTensionLbf: Math.round(deadlineTension),
    derrickLoadLbf: Math.round(derrickLoad),
    maxEquivalentDerrickLoadLbf: Math.round(maxEqDerrickLoad),
    derrickEfficiencyFactor: Math.round(derrickEff * 1000) / 1000,
    hookHorsepower: Math.round(hookHp),
    hoistingSpeedFtMin: Math.round(hoistingSpeed * 10) / 10,
  };
}

/**
 * 1.3 Mud Pump Factors (Duplex & Triplex)
 * Sourced: Bourgoyne Ch. 1, Eq. 1.10 - 1.14
 */
export function duplexPumpFactor(
  linerIdInches: number,
  rodDiameterInches: number,
  strokeLengthInches: number,
  volumetricEfficiency: number = 0.90
): number {
  // Duplex double-acting pump displacement per stroke:
  // Fp = 0.000162 * Ls * (2 * dl^2 - dr^2) * Ev in bbl/stk
  const dlSq = Math.pow(linerIdInches, 2);
  const drSq = Math.pow(rodDiameterInches, 2);
  const fp = 0.000162 * strokeLengthInches * (2 * dlSq - drSq) * volumetricEfficiency;
  return Math.round(fp * 1000) / 1000;
}

export function triplexPumpFactor(
  linerIdInches: number,
  strokeLengthInches: number,
  volumetricEfficiency: number = 0.95
): number {
  // Triplex single-acting pump displacement per stroke:
  // Sourced: Bourgoyne Ch. 1, Eq. 1.10 - 1.12 & API formulas
  // Fp = 3 * (Ls / 12) * (dl^2 / 1029.4) * Ev = (Ls * dl^2 / 4117.6) * Ev (bbl/stk)
  const strokeFt = strokeLengthInches / 12;
  const fp = (3 * strokeFt * Math.pow(linerIdInches, 2) / 1029.4) * volumetricEfficiency;
  return Math.round(fp * 1000) / 1000;
}

export function hydraulicHorsepower(differentialPressurePsi: number, flowRateGpm: number): number {
  // P_H = (delta_p * q) / 1714
  return Math.round(((differentialPressurePsi * flowRateGpm) / 1714) * 10) / 10;
}

/**
 * 1.4 Drilling Economics & Cost per Foot Analysis
 * Sourced: Bourgoyne Ch. 1, Section 1.4, Eq. 1.15 - 1.21
 */
export interface DrillingCostResult {
  costPerFoot: number;      // $/ft
  totalBitRunCost: number;  // $
  rotatingCost: number;     // $
  tripCost: number;         // $
  connectionCost: number;   // $
  bitCost: number;          // $
}

export function calculateDrillingCostPerFoot(
  bitCostDollars: number,
  rigOperatingRateDollarsPerHr: number,
  rotatingTimeHours: number,
  connectionTimeHours: number,
  tripTimeHours: number,
  footageDrilledFt: number
): DrillingCostResult {
  const deltaD = Math.max(1, footageDrilledFt);
  const Cr = rigOperatingRateDollarsPerHr;

  const rotatingCost = Cr * rotatingTimeHours;
  const connectionCost = Cr * connectionTimeHours;
  const tripCost = Cr * tripTimeHours;
  const totalCost = bitCostDollars + rotatingCost + connectionCost + tripCost;
  const costPerFoot = totalCost / deltaD;

  return {
    costPerFoot: Math.round(costPerFoot * 100) / 100,
    totalBitRunCost: Math.round(totalCost),
    rotatingCost: Math.round(rotatingCost),
    tripCost: Math.round(tripCost),
    connectionCost: Math.round(connectionCost),
    bitCost: bitCostDollars,
  };
}

/**
 * Trip time estimation based on stand length and depth
 * Sourced: Bourgoyne Ch. 1, Eq. 1.17: t_t = 2 * (t_s / l_s) * D
 */
export function estimateTripTimeHours(
  depthFt: number,
  minutesPerStand: number = 1.0,
  standLengthFt: number = 90
): number {
  // Total round-trip stands = 2 * (D / ls)
  const totalStands = 2 * (depthFt / standLengthFt);
  const totalMinutes = totalStands * minutesPerStand;
  return Math.round((totalMinutes / 60) * 10) / 10;
}

/**
 * 5.1 Rotary Drilling Bits - Penetration Rate & Mechanical Specific Energy (MSE)
 * Sourced: Teale (1962), "The Concept of Specific Energy in Rock Drilling" & Bourgoyne Ch. 5, Eq. 5.15
 */
export function bitSpecificEnergy(
  wobLbf: number,
  rpm: number,
  bitDiameterInches: number,
  ropFtHr: number,
  torqueFtLbf: number
): number {
  const bitAreaSqIn = (Math.PI / 4) * Math.pow(bitDiameterInches, 2);
  if (ropFtHr <= 0 || bitAreaSqIn <= 0) return 0;
  // Teale (1962) MSE equation:
  // E_s = (WOB / A) + (120 * pi * N * T) / (A * ROP)
  const axialTerm = wobLbf / bitAreaSqIn;
  const rotaryTerm = (120 * Math.PI * rpm * torqueFtLbf) / (bitAreaSqIn * ropFtHr);
  return Math.round(axialTerm + rotaryTerm);
}

/**
 * Bourgoyne & Young ROP Model Formulation
 * ROP = f1 * f2 * f3 * f4 * f5 * f6 * f7 * f8
 * Sourced: Bourgoyne Ch. 5, Section 5.4, Eq. 5.16
 */
export function estimateROPBourgoyne(
  baseFormationStrengthK: number, // f1
  depthFt: number,                // f2 (compaction)
  porePressurePpg: number,        // f3 (overbalance)
  mudWeightPpg: number,
  wobLbf: number,                 // f4 (WOB / D)
  bitDiameterInches: number,
  rpm: number,                    // f5 (RPM)
  toothWearFraction: number = 0,  // f6 (dull fraction: 0 to 1)
  hydraulicImpactHp: number = 3.5 // f7 (HSI)
): number {
  // Coefficients calibrated to Gulf Coast shales/sandstones:
  const a2 = 0.0001;
  const a3 = 0.00005;
  const a5 = 0.5; // WOB exponent
  const a6 = 0.7; // RPM exponent
  const a7 = 0.3; // tooth wear slowdown
  const a8 = 0.3; // hydraulics boost

  const wobPerInch = wobLbf / (bitDiameterInches * 1000); // 1000 lbf/in

  const f1 = baseFormationStrengthK;
  const f2 = Math.exp(a2 * (10000 - depthFt));
  const f3 = Math.exp(-a3 * Math.max(0, (mudWeightPpg - porePressurePpg) * 0.052 * depthFt));
  const f4 = Math.pow(Math.max(0.5, wobPerInch), a5);
  const f5 = Math.pow(Math.max(10, rpm) / 100, a6);
  const f6 = Math.exp(-a7 * toothWearFraction);
  const f7 = Math.pow(Math.max(1, hydraulicImpactHp), a8);

  const rop = f1 * f2 * f3 * f4 * f5 * f6 * f7;
  return Math.round(Math.max(1, rop) * 10) / 10;
}

/**
 * 5.2 IADC Dull Grading System Formatter
 * 8-factor IADC standard code: Inner - Outer - Dull Char - Location - Bearing - Gauge - Other - Reason Pulled
 */
export interface IADCDullGrade {
  innerCutters: number;    // 0 to 8
  outerCutters: number;    // 0 to 8
  dullCharacteristics: string; // e.g. BT (broken teeth), WT (worn teeth), JD (junk damage)
  location: string;        // e.g. N (nose), M (middle), G (gauge), A (all)
  bearingSeals: string;    // e.g. E (sealed effective), F (failed), X (fixed cutter)
  gaugeIn16ths: number;    // 0 = in gauge, 1/16" under gauge, etc.
  otherCharacteristics: string;
  reasonPulled: string;    // BHA, DMF, DP, DSF, DST, DTF, FM, HP, HR, LOG, PP, PR, RIG, TD, TQ, TW, WC
}

export function formatIADCDullGrade(grade: IADCDullGrade): string {
  const gStr = grade.gaugeIn16ths === 0 ? 'I' : `${grade.gaugeIn16ths}/16`;
  return `${grade.innerCutters}-${grade.outerCutters}-${grade.dullCharacteristics}-${grade.location}-${grade.bearingSeals}-${gStr}-${grade.otherCharacteristics || 'NO'}-${grade.reasonPulled}`;
}

/**
 * Bit Type Selection Advisor
 */
export function recommendBitType(
  unconfinedCompressiveStrengthPsi: number,
  abrasiveness: 'low' | 'medium' | 'high',
  interbedded: boolean
): { recommendedType: string; iadcSeries: string; reason: string } {
  if (unconfinedCompressiveStrengthPsi < 6000) {
    return {
      recommendedType: 'PDC (Polycrystalline Diamond Compact)',
      iadcSeries: 'M1xx / M2xx (Steel body PDC)',
      reason: 'Soft, ductile formations drill at maximum ROP with shear-cutting PDC bits.',
    };
  } else if (unconfinedCompressiveStrengthPsi < 15000) {
    if (abrasiveness === 'high' || interbedded) {
      return {
        recommendedType: 'Tungsten Carbide Insert (TCI) Roller Cone',
        iadcSeries: 'IADC 517 / 537 (Chisel / Conical Inserts)',
        reason: 'Medium hard, abrasive or interbedded rock requires impact resistance and crushing action.',
      };
    }
    return {
      recommendedType: 'Heavy-Set Matrix PDC',
      iadcSeries: 'M3xx / M4xx',
      reason: 'Matrix body PDC with thermal stable cutters provides long life and good ROP.',
    };
  } else {
    return {
      recommendedType: 'Hard-Rock TCI or Hybrid Roller/Diamond',
      iadcSeries: 'IADC 6xx / 7xx or Impregnated Diamond',
      reason: 'Ultra-hard, brittle formations (>15,000 psi) require crushing/grinding action to avoid cutter shearing delamination.',
    };
  }
}
