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
