/**
 * Unit-Aware Engineering Tables and Reference Data
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986).
 */

export interface SteelGrade {
  grade: string;
  minYieldPsi: number;
  maxYieldPsi: number;
  minTensilePsi: number;
  description: string;
}

/**
 * Table 7.1 / Table 7.2 - API Casing and Tubing Steel Grades
 */
export const API_CASING_GRADES: Record<string, SteelGrade> = {
  'H-40': { grade: 'H-40', minYieldPsi: 40000, maxYieldPsi: 80000, minTensilePsi: 60000, description: 'Shallow wells, low pressure' },
  'J-55': { grade: 'J-55', minYieldPsi: 55000, maxYieldPsi: 80000, minTensilePsi: 75000, description: 'Standard service medium depth' },
  'K-55': { grade: 'K-55', minYieldPsi: 55000, maxYieldPsi: 80000, minTensilePsi: 95000, description: 'Higher tensile standard casing' },
  'C-75': { grade: 'C-75', minYieldPsi: 75000, maxYieldPsi: 90000, minTensilePsi: 95000, description: 'Controlled yield for sour gas service' },
  'L-80': { grade: 'L-80', minYieldPsi: 80000, maxYieldPsi: 95000, minTensilePsi: 100000, description: 'H2S sour service standard' },
  'N-80': { grade: 'N-80', minYieldPsi: 80000, maxYieldPsi: 110000, minTensilePsi: 100000, description: 'Deep wells, sweet service' },
  'C-90': { grade: 'C-90', minYieldPsi: 90000, maxYieldPsi: 105000, minTensilePsi: 100000, description: 'Heavy sour service' },
  'T-95': { grade: 'T-95', minYieldPsi: 95000, maxYieldPsi: 110000, minTensilePsi: 105000, description: 'High-strength sour service' },
  'P-110': { grade: 'P-110', minYieldPsi: 110000, maxYieldPsi: 140000, minTensilePsi: 125000, description: 'High pressure deep wells' },
  'Q-125': { grade: 'Q-125', minYieldPsi: 125000, maxYieldPsi: 155000, minTensilePsi: 135000, description: 'Ultra-deep, high collapse & burst' },
};

export interface CementClass {
  class: string;
  depthRangeFt: string;
  tempRangeF: string;
  waterReqPct: number;    // % water by weight of dry cement
  slurryDensityPpg: number; // lbm/gal with normal water
  slurryYieldFt3Sk: number; // ft3/sack
  description: string;
}

/**
 * Table 3.6 - API Spec 10 Cement Classes
 */
export const API_CEMENT_CLASSES: Record<string, CementClass> = {
  'Class A': { class: 'Class A', depthRangeFt: '0 - 6,000', tempRangeF: '80 - 170', waterReqPct: 46, slurryDensityPpg: 15.6, slurryYieldFt3Sk: 1.18, description: 'Ordinary Portland, surface to moderate depths' },
  'Class B': { class: 'Class B', depthRangeFt: '0 - 6,000', tempRangeF: '80 - 170', waterReqPct: 46, slurryDensityPpg: 15.6, slurryYieldFt3Sk: 1.18, description: 'Moderate-to-high sulfate resistance' },
  'Class C': { class: 'Class C', depthRangeFt: '0 - 6,000', tempRangeF: '80 - 170', waterReqPct: 56, slurryDensityPpg: 14.8, slurryYieldFt3Sk: 1.32, description: 'High early strength, rapid set' },
  'Class G': { class: 'Class G', depthRangeFt: '0 - 8,000', tempRangeF: '80 - 200', waterReqPct: 44, slurryDensityPpg: 15.8, slurryYieldFt3Sk: 1.15, description: 'Basic oilwell cement, usable with accelerators/retarders up to 14,000 ft' },
  'Class H': { class: 'Class H', depthRangeFt: '0 - 8,000', tempRangeF: '80 - 200', waterReqPct: 38, slurryDensityPpg: 16.5, slurryYieldFt3Sk: 1.06, description: 'Coarser grind basic cement, high density base' },
};

/**
 * Table 1.1 - Block and Tackle Hoisting Efficiencies by Number of Lines Strung
 * Sourced: Bourgoyne Ch. 1, Table 1.1
 */
export const HOISTING_EFFICIENCY_BY_LINES: Record<number, number> = {
  4: 0.912,
  6: 0.874,
  8: 0.841,
  10: 0.810,
  12: 0.770,
  14: 0.740,
};

/**
 * Fuel Heating Values and Densities (Bourgoyne Ch. 1, Power Systems)
 */
export const FUEL_PROPERTIES = {
  diesel: { name: 'Diesel', heatingValueBtuLbm: 19000, densityLbmGal: 7.2 },
  gasoline: { name: 'Gasoline', heatingValueBtuLbm: 20000, densityLbmGal: 6.1 },
  butane: { name: 'LPG / Butane', heatingValueBtuLbm: 21000, densityLbmGal: 4.8 },
  methane: { name: 'Natural Gas / Methane', heatingValueBtuLbm: 24000, densityLbmGal: 3.5 }, // equivalent
};

/**
 * Pipe Absolute Roughness epsilon in inches and feet
 * Sourced: Bourgoyne Ch. 4 (Hydraulics)
 */
export const PIPE_ROUGHNESS = {
  commercialSteelInches: 0.0018,
  commercialSteelFt: 0.00015,
  drawnTubingFt: 0.000005,
  rustedCasingFt: 0.0004,
};

/**
 * Water activity lookup for oil-based / inhibitive muds (Bourgoyne Ch. 2, Table 2.9)
 */
export const SALT_WATER_ACTIVITY: { salt: string; wtPct: number; activity: number }[] = [
  { salt: 'NaCl', wtPct: 5, activity: 0.97 },
  { salt: 'NaCl', wtPct: 10, activity: 0.93 },
  { salt: 'NaCl', wtPct: 15, activity: 0.89 },
  { salt: 'NaCl', wtPct: 20, activity: 0.84 },
  { salt: 'NaCl', wtPct: 26, activity: 0.75 }, // Saturation
  { salt: 'CaCl2', wtPct: 10, activity: 0.94 },
  { salt: 'CaCl2', wtPct: 20, activity: 0.85 },
  { salt: 'CaCl2', wtPct: 30, activity: 0.68 },
  { salt: 'CaCl2', wtPct: 35, activity: 0.53 },
  { salt: 'CaCl2', wtPct: 40, activity: 0.38 },
];

export interface PipeCapacitySpec {
  odInches: number;
  weightLbFt: number;
  idInches: number;
  capacityBblFt: number;
  displacementBblFt: number;
}

/**
 * Drill Pipe Capacity and Displacement Table (Carter Appendix A, Table A.1)
 */
export const DRILL_PIPE_CAPACITY_DISPLACEMENT: PipeCapacitySpec[] = [
  { odInches: 2.375, weightLbFt: 6.65, idInches: 1.815, capacityBblFt: 0.0032, displacementBblFt: 0.0025 },
  { odInches: 2.875, weightLbFt: 10.4, idInches: 2.151, capacityBblFt: 0.0045, displacementBblFt: 0.0038 },
  { odInches: 3.5, weightLbFt: 13.3, idInches: 2.764, capacityBblFt: 0.0074, displacementBblFt: 0.0045 },
  { odInches: 3.5, weightLbFt: 15.5, idInches: 2.602, capacityBblFt: 0.0066, displacementBblFt: 0.0053 },
  { odInches: 4.0, weightLbFt: 14.0, idInches: 3.34, capacityBblFt: 0.0108, displacementBblFt: 0.0047 },
  { odInches: 4.5, weightLbFt: 16.6, idInches: 3.826, capacityBblFt: 0.0142, displacementBblFt: 0.0053 },
  { odInches: 4.5, weightLbFt: 20.0, idInches: 3.64, capacityBblFt: 0.0129, displacementBblFt: 0.0067 },
  { odInches: 5.0, weightLbFt: 19.5, idInches: 4.276, capacityBblFt: 0.0178, displacementBblFt: 0.0065 },
  { odInches: 5.0, weightLbFt: 25.6, idInches: 4.0, capacityBblFt: 0.0155, displacementBblFt: 0.0087 },
  { odInches: 5.5, weightLbFt: 21.9, idInches: 4.778, capacityBblFt: 0.0222, displacementBblFt: 0.0072 },
  { odInches: 5.5, weightLbFt: 24.7, idInches: 4.67, capacityBblFt: 0.0212, displacementBblFt: 0.0082 },
  { odInches: 6.625, weightLbFt: 25.2, idInches: 5.965, capacityBblFt: 0.0346, displacementBblFt: 0.0081 },
];

/**
 * Heavy Weight Drill Pipe (HWDP) Capacity and Displacement Table (Carter Appendix A, Table A.2)
 */
export const HWDP_CAPACITY_DISPLACEMENT: PipeCapacitySpec[] = [
  { odInches: 3.5, weightLbFt: 25.3, idInches: 2.25, capacityBblFt: 0.0049, displacementBblFt: 0.0070 },
  { odInches: 4.0, weightLbFt: 29.7, idInches: 2.562, capacityBblFt: 0.0064, displacementBblFt: 0.0091 },
  { odInches: 4.5, weightLbFt: 41.0, idInches: 2.75, capacityBblFt: 0.0073, displacementBblFt: 0.0123 },
  { odInches: 5.0, weightLbFt: 49.3, idInches: 3.0, capacityBblFt: 0.0087, displacementBblFt: 0.0155 },
  { odInches: 5.5, weightLbFt: 57.0, idInches: 3.25, capacityBblFt: 0.0103, displacementBblFt: 0.0189 },
  { odInches: 6.625, weightLbFt: 78.5, idInches: 4.5, capacityBblFt: 0.0197, displacementBblFt: 0.0229 },
];

/**
 * Drill Collar Capacity and Displacement Table (Carter Appendix A, Table A.3)
 */
export const DRILL_COLLAR_CAPACITY_DISPLACEMENT: PipeCapacitySpec[] = [
  { odInches: 4.75, weightLbFt: 48.0, idInches: 2.25, capacityBblFt: 0.0049, displacementBblFt: 0.0170 },
  { odInches: 6.25, weightLbFt: 83.0, idInches: 2.25, capacityBblFt: 0.0049, displacementBblFt: 0.0330 },
  { odInches: 6.5, weightLbFt: 91.0, idInches: 2.8125, capacityBblFt: 0.0077, displacementBblFt: 0.0333 },
  { odInches: 7.0, weightLbFt: 110.0, idInches: 2.8125, capacityBblFt: 0.0077, displacementBblFt: 0.0399 },
  { odInches: 8.0, weightLbFt: 150.0, idInches: 2.8125, capacityBblFt: 0.0077, displacementBblFt: 0.0544 },
  { odInches: 9.5, weightLbFt: 217.0, idInches: 3.0, capacityBblFt: 0.0087, displacementBblFt: 0.0789 },
  { odInches: 10.0, weightLbFt: 243.0, idInches: 3.0, capacityBblFt: 0.0087, displacementBblFt: 0.0884 },
];

export interface SurfaceSystemCSS {
  caseNumber: number;
  description: string;
  css: number;
  standpipeFt: { length: number; id: number };
  hoseFt: { length: number; id: number };
  swivelFt: { length: number; id: number };
  kellyFt: { length: number; id: number };
}

/**
 * Surface System Friction Constant (CSS) Cases (Carter Ch. 6, Table 6.1)
 */
export const SURFACE_SYSTEM_CSS: SurfaceSystemCSS[] = [
  {
    caseNumber: 1,
    description: "Case 1: 40 ft x 3.0 in. standpipe, 45 ft x 2.0 in. hose, 4 ft x 2.0 in. swivel, 40 ft x 2.25 in. kelly",
    css: 25,
    standpipeFt: { length: 40, id: 3.0 },
    hoseFt: { length: 45, id: 2.0 },
    swivelFt: { length: 4, id: 2.0 },
    kellyFt: { length: 40, id: 2.25 },
  },
  {
    caseNumber: 2,
    description: "Case 2: 40 ft x 3.5 in. standpipe, 55 ft x 2.5 in. hose, 5 ft x 2.5 in. swivel, 40 ft x 3.25 in. kelly",
    css: 8.6,
    standpipeFt: { length: 40, id: 3.5 },
    hoseFt: { length: 55, id: 2.5 },
    swivelFt: { length: 5, id: 2.5 },
    kellyFt: { length: 40, id: 3.25 },
  },
  {
    caseNumber: 3,
    description: "Case 3: 45 ft x 4.0 in. standpipe, 55 ft x 3.0 in. hose, 5 ft x 2.5 in. swivel, 40 ft x 3.25 in. kelly",
    css: 4.2,
    standpipeFt: { length: 45, id: 4.0 },
    hoseFt: { length: 55, id: 3.0 },
    swivelFt: { length: 5, id: 2.5 },
    kellyFt: { length: 40, id: 3.25 },
  },
  {
    caseNumber: 4,
    description: "Case 4: 45 ft x 4.0 in. standpipe, 55 ft x 3.0 in. hose, 6 ft x 3.0 in. swivel, 40 ft x 4.0 in. top drive / kelly",
    css: 2.0,
    standpipeFt: { length: 45, id: 4.0 },
    hoseFt: { length: 55, id: 3.0 },
    swivelFt: { length: 6, id: 3.0 },
    kellyFt: { length: 40, id: 4.0 },
  },
];

export interface DrillLineCutoffGoal {
  lineDiameterInches: number;
  tonMileGoal: number;
  recommendedCutoffLengthFt: number;
}

/**
 * Recommended Drill Line Ton-Mile Goals (Carter Ch. 7, Table 7.1)
 */
export const DRILL_LINE_TON_MILE_GOAL: DrillLineCutoffGoal[] = [
  { lineDiameterInches: 1.0, tonMileGoal: 800, recommendedCutoffLengthFt: 30 },
  { lineDiameterInches: 1.125, tonMileGoal: 1050, recommendedCutoffLengthFt: 35 },
  { lineDiameterInches: 1.25, tonMileGoal: 1350, recommendedCutoffLengthFt: 40 },
  { lineDiameterInches: 1.375, tonMileGoal: 1650, recommendedCutoffLengthFt: 45 },
  { lineDiameterInches: 1.5, tonMileGoal: 2000, recommendedCutoffLengthFt: 50 },
  { lineDiameterInches: 1.625, tonMileGoal: 2350, recommendedCutoffLengthFt: 55 },
  { lineDiameterInches: 1.75, tonMileGoal: 2700, recommendedCutoffLengthFt: 60 },
  { lineDiameterInches: 2.0, tonMileGoal: 3500, recommendedCutoffLengthFt: 70 },
];
