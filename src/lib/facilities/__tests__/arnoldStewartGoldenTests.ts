/**
 * Arnold & Stewart (Surface Production Operations, Vol. 1, 3rd ed.)
 * Comprehensive Golden Benchmarks Test Suite
 * Covers Chapters 3, 4, 5, 6, 7, 9, 10
 */

import {
  apparentMolecularWeight,
  gasSpecificGravity,
  wichertAzizCorrection,
  gasCompressibilityFactor,
  gasDensity,
  apiToSG,
} from "../pvtProperties";
import { sizeVerticalTwoPhaseSeparator, sizeHorizontalTwoPhaseSeparator } from "../twoPhaseSeparation";
import { sizeVerticalThreePhaseSeparator, sizeHorizontalThreePhaseSeparator } from "../threePhaseSeparation";
import { calculateVesselMechanicalDesign } from "../vesselDesign";
import { gunbarrelWaterLegHeight, sizeHorizontalHeaterTreater } from "../oilTreating";
import { sizeCPIPlatePacks, sizeSkimVessels, minDropletFromPacks } from "../waterTreating";

export interface GoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runArnoldStewartGoldenTests(): GoldenTestResult[] {
  const results: GoldenTestResult[] = [];

  // =========================================================================
  // Test 1: Ex. 3-3 - Natural Gas Molecular Weight & Specific Gravity
  // =========================================================================
  const gasComp = [
    { moleFraction: 0.85, mw: 16.0 },
    { moleFraction: 0.09, mw: 30.0 },
    { moleFraction: 0.04, mw: 44.0 },
    { moleFraction: 0.02, mw: 58.0 },
  ];
  const mwCalc = apparentMolecularWeight(gasComp);
  const sgCalc = gasSpecificGravity(mwCalc, 29);
  const passed1 = Math.abs(mwCalc - 19.23) <= 0.05 && Math.abs(sgCalc - 0.66) <= 0.01;
  results.push({
    id: "AS-Ex-3.3",
    source: "Arnold & Stewart Ex. 3-3 (p. 71)",
    description: "Gas Apparent Molecular Weight & Specific Gravity",
    passed: passed1,
    actual: `MW = ${mwCalc}, SG = ${sgCalc}`,
    expected: "MW = 19.23, SG = 0.66",
    deviationPercent: Math.round(Math.abs((mwCalc - 19.23) / 19.23) * 1000) / 10,
  });

  // =========================================================================
  // Test 2: Ex. 3-6 - Sour Gas Wichert-Aziz Correction & Z-Factor
  // =========================================================================
  // Given: T'pc = 433.9 °R, P'pc = 826.9 psia, H2S = 20%, CO2 = 10%
  const wa = wichertAzizCorrection(433.9, 826.9, 0.2, 0.1);
  const pr = 1000 / wa.ppcAdjustedPsia; // 1000 / 761.7 = 1.313
  const tr = 560 / wa.tpcAdjustedR; // 560 / 404.1 = 1.385
  const zFactor = gasCompressibilityFactor(pr, tr);
  // Book: epsilon = 29.8 °R, T''pc = 404.1 °R, P''pc = 761.7 psia, Z = 0.831
  const passed2 =
    Math.abs(wa.epsilon - 29.8) <= 0.5 &&
    Math.abs(wa.tpcAdjustedR - 404.1) <= 0.5 &&
    Math.abs(wa.ppcAdjustedPsia - 761.7) <= 1.5 &&
    Math.abs(zFactor - 0.831) <= 0.02;
  results.push({
    id: "AS-Ex-3.6",
    source: "Arnold & Stewart Ex. 3-6 (p. 88)",
    description: "Sour Gas Wichert-Aziz Correction & Z-factor",
    passed: passed2,
    actual: `ε = ${wa.epsilon} °R, P''pc = ${wa.ppcAdjustedPsia} psia, Z = ${zFactor}`,
    expected: "ε = 29.8 °R, P''pc = 761.7 psia, Z = 0.831",
    deviationPercent: Math.round(Math.abs((wa.ppcAdjustedPsia - 761.7) / 761.7) * 1000) / 10,
  });

  // =========================================================================
  // Test 3: Ex. 4-1 - Vertical Two-Phase Separator Sizing
  // =========================================================================
  // Given: 10 MMscfd, 2000 BOPD, 40°API, 1000 psia, 60°F, 140 um, tr = 3 min, Z = 0.84
  const vSep = sizeVerticalTwoPhaseSeparator(10, 2000, 1000, 60, 0.84, 0.6, 40, 140, 3, 36);
  // Book: d_gas = 21.9 in, selected 36 in x 10 ft with SR = 3.2
  const passed3 = Math.abs(vSep.dMinGasInches - 21.9) <= 0.5 && vSep.seamToSeamLengthFt === 10;
  results.push({
    id: "AS-Ex-4.1",
    source: "Arnold & Stewart Ex. 4-1 (p. 226)",
    description: "Vertical Two-Phase Separator Sizing",
    passed: passed3,
    actual: `d_gas = ${vSep.dMinGasInches}", Selected: ${vSep.dSelectedInches}" x ${vSep.seamToSeamLengthFt}', SR = ${vSep.slendernessRatio}`,
    expected: 'd_gas = 21.9", Selected: 36" x 10\', SR = 3.2',
    deviationPercent: Math.round(Math.abs((vSep.dMinGasInches - 21.9) / 21.9) * 1000) / 10,
  });

  // =========================================================================
  // Test 4: Ex. 4-3 - Horizontal Two-Phase Separator Sizing
  // =========================================================================
  // Given: Same data as Ex 4-1
  // Note: Book solution p. 232 states 55.04 due to a book typo; the book's own derivation (pp. 206-209) gives 39.85 (39.91 rounded)
  const hSep = sizeHorizontalTwoPhaseSeparator(10, 2000, 1000, 60, 0.84, 0.6, 40, 140, 3);
  const passed4 = Math.abs(hSep.dLeffGasRequirement - 39.91) <= 0.5 && hSep.selectedSize.diameterInches === 36;
  results.push({
    id: "AS-Ex-4.3",
    source: "Arnold & Stewart Ex. 4-3 (p. 232)",
    description: "Horizontal Two-Phase Separator Sizing (Book Typo Corrected per Derivation p. 206)",
    passed: passed4,
    actual: `d*Leff = ${hSep.dLeffGasRequirement}, Selected: ${hSep.selectedSize.diameterInches}" x ${hSep.selectedSize.lengthFt}'`,
    expected: 'd*Leff = 39.91 (Book Typo: 55.04), Selected: 36" x 10\'',
    deviationPercent: Math.round(Math.abs((hSep.dLeffGasRequirement - 39.91) / 39.91) * 1000) / 10,
  });

  // =========================================================================
  // Test 5: Ex. 5-1 - Vertical Three-Phase Separator Sizing
  // =========================================================================
  // Given: 5000 BOPD, 3000 BWPD, 5 MMscfd, 100 psia, 90°F, 30°API, SGw=1.07, Sg=0.6, mu_o=10 cp, mu_w=1 cp, CD=2.01, Z=0.99
  const v3Sep = sizeVerticalThreePhaseSeparator(5, 5000, 3000, 100, 90, 0.99, 0.6, 30, 1.07, 10, 1.0, 10, 10, 90);
  // Book: d_gas = 34.9", d_water_in_oil = 83.0", d_oil_in_water = 50.8" => dmin = 83.0" => 90" x 20' (SR = 2.4)
  const passed5 =
    Math.abs(v3Sep.dMinInches - 83.0) <= 0.5 &&
    v3Sep.dSelectedInches === 90 &&
    v3Sep.seamToSeamLengthFt === 20;
  results.push({
    id: "AS-Ex-5.1",
    source: "Arnold & Stewart Ex. 5-1 (p. 294)",
    description: "Vertical Three-Phase Separator Sizing",
    passed: passed5,
    actual: `d_min = ${v3Sep.dMinInches}", Selected: ${v3Sep.dSelectedInches}" x ${v3Sep.seamToSeamLengthFt}', SR = ${v3Sep.slendernessRatio}`,
    expected: 'd_min = 83.0", Selected: 90" x 20\', SR = 2.4',
    deviationPercent: Math.round(Math.abs((v3Sep.dMinInches - 83.0) / 83.0) * 1000) / 10,
  });

  // =========================================================================
  // Test 6: Ex. 5-3 - Horizontal Three-Phase Separator Sizing
  // =========================================================================
  // Given: Same data as Ex 5-1: (ho)max = 62.1", Aw/A = 0.1875, beta = 0.257, dmax = 241.6", d^2*Leff = 113,600
  const h3Sep = sizeHorizontalThreePhaseSeparator(5, 5000, 3000, 100, 90, 0.99, 0.6, 30, 1.07, 10, 10, 10);
  const passed6 =
    Math.abs(h3Sep.maxOilPadThicknessInches - 62.1) <= 0.5 &&
    Math.abs(h3Sep.maxDiameterInches - 241.6) <= 2.0 &&
    h3Sep.d2LeffLiquidRequirement === 113600;
  results.push({
    id: "AS-Ex-5.3",
    source: "Arnold & Stewart Ex. 5-3 (p. 299)",
    description: "Horizontal Three-Phase Separator Sizing",
    passed: passed6,
    actual: `(ho)max = ${h3Sep.maxOilPadThicknessInches}", d_max = ${h3Sep.maxDiameterInches}", d^2*Leff = ${h3Sep.d2LeffLiquidRequirement}`,
    expected: '(ho)max = 62.1", d_max = 241.6", d^2*Leff = 113,600',
    deviationPercent: Math.round(Math.abs((h3Sep.maxOilPadThicknessInches - 62.1) / 62.1) * 1000) / 10,
  });

  // =========================================================================
  // Test 7: Ex. 6-1 - Mechanical Design of Pressure Vessel (FWKO Weight)
  // =========================================================================
  // Given: 125 psig, 200°F, CA = 0.25", SA-516-70, d = 10 ft (120 in), L = 12 ft, cone apex = 60°
  const mech = calculateVesselMechanicalDesign({
    designPressurePsig: 125,
    insideDiameterInches: 120,
    seamToSeamLengthFt: 12,
    headType: "cone-bottom",
    coneApexAngleDeg: 60,
    materialKey: "SA-516-70",
    jointEfficiency: 0.85,
    corrosionAllowanceInches: 0.25,
    isVertical: true,
    edition: "1998",
  });
  // Book: Shell = 12,870 lb, Head = 4,163 lb, Cone = 5,796 lb, Skirt = 7,260 lb, Subtotal = 30,089 lb, Total = 35,089 lb
  const passed7 =
    mech.weights.shellWeightLb === 12870 &&
    mech.weights.headsWeightLb === 4163 &&
    mech.weights.coneWeightLb === 5796 &&
    mech.weights.skirtWeightLb === 7260 &&
    mech.weights.totalVesselWeightLb === 35089;
  results.push({
    id: "AS-Ex-6.1",
    source: "Arnold & Stewart Ex. 6-1 (p. 342)",
    description: "FWKO Pressure Vessel Weight Estimation (ASME Sec VIII Div 1)",
    passed: passed7,
    actual: `Shell = ${mech.weights.shellWeightLb} lb, Head = ${mech.weights.headsWeightLb} lb, Cone = ${mech.weights.coneWeightLb} lb, Skirt = ${mech.weights.skirtWeightLb} lb, Total = ${mech.weights.totalVesselWeightLb} lb`,
    expected: "Shell = 12,870 lb, Head = 4,163 lb, Cone = 5,796 lb, Skirt = 7,260 lb, Total = 35,089 lb",
    deviationPercent: 0,
  });

  // =========================================================================
  // Test 8: Ex. 7-1 - Gunbarrel External Water Leg Height
  // =========================================================================
  // Given: 36°API (SGo = 0.845), SGw = 1.05, H_oil = 23 ft, H_int = 10 ft, H_water = 1 ft
  const gb = gunbarrelWaterLegHeight(23, 10, 1, 36, 1.05);
  // Book: Ho = 13 ft, Hw = 9 ft, grad_o = 0.366 psi/ft, grad_w = 0.455 psi/ft, H = 19.5 ft
  const passed8 = Math.abs(gb.waterLegHeightHFt - 19.5) <= 0.1 && gb.oilHeightHoFt === 13;
  results.push({
    id: "AS-Ex-7.1",
    source: "Arnold & Stewart Ex. 7-1 (p. 354)",
    description: "Gunbarrel External Water Leg Height (Pressure Balance)",
    passed: passed8,
    actual: `Ho = ${gb.oilHeightHoFt} ft, Hw = ${gb.waterHeightHwFt} ft, Water Leg H = ${gb.waterLegHeightHFt} ft`,
    expected: "Ho = 13 ft, Hw = 9 ft, Water Leg H = 19.5 ft",
    deviationPercent: Math.round(Math.abs((gb.waterLegHeightHFt - 19.5) / 19.5) * 1000) / 10,
  });

  // =========================================================================
  // Test 9: Ex. 7-2 - Horizontal Heater-Treater Heat Required & Sizing
  // =========================================================================
  // Given: 5000 BOPD, 30°API, Tinlet = 80°F, SGw = 1.04, deltaSG = 0.165
  const ht = sizeHorizontalHeaterTreater(5000, 80, 30, 1.04, 20, [80, 100, 120]);
  // Book: q = 43,040 * Delta_T => at 100°F: 0.86 MMBtu/h; at 120°F: 1.72 MMBtu/h; Selected 72" x 20'
  const heat100 = ht.resultsByTemp[1].heatRequiredBtuHr;
  const passed9 = Math.abs(heat100 - 860800) <= 2000 && ht.recommendedSize.diameterInches === 72;
  results.push({
    id: "AS-Ex-7.2",
    source: "Arnold & Stewart Ex. 7-2 (p. 432)",
    description: "Horizontal Heater-Treater Sizing & Heat Input",
    passed: passed9,
    actual: `Heat at 100°F = ${(heat100 / 1e6).toFixed(2)} MMBtu/h, Size: ${ht.recommendedSize.diameterInches}" x ${ht.recommendedSize.coalescingLengthFt}'`,
    expected: 'Heat at 100°F = 0.86 MMBtu/h, Size: 72" x 20\'',
    deviationPercent: Math.round(Math.abs((heat100 - 860800) / 860800) * 1000) / 10,
  });

  // =========================================================================
  // Test 10: Ex. 9-1 - Produced Water CPI Plate Separator Droplet Cutoff
  // =========================================================================
  // Given: 25,000 bpd, 125°F, SGw = 1.06, SGo = 0.75 (deltaSG = 0.31), mu_w = 0.65 cp, Npacks = 1 at 45°
  // Eq. 9-20: dm = sqrt[ 0.077 * (25000 * 0.65) / (0.31 * 1) ] = 63.5 microns
  const dmCutoff = minDropletFromPacks(25000, 0.65, 0.31, 1, 45);
  const passed10 = Math.abs(dmCutoff - 63.5) <= 0.5;
  results.push({
    id: "AS-Ex-9-1",
    source: "Arnold & Stewart Ex. 9-1 (p. 542)",
    description: "CPI Plate Separator Minimum Droplet Cutoff (45° angle, Npacks=1)",
    passed: passed10,
    actual: `dm = ${dmCutoff} μm`,
    expected: "dm = 63.5 μm",
    deviationPercent: Math.round(Math.abs((dmCutoff - 63.5) / 63.5) * 1000) / 10,
  });

  return results;
}
