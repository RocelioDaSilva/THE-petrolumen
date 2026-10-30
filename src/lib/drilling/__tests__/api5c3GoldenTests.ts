/**
 * API 5C3 / ISO 10400 Casing Structural Integrity & Rig Power Golden Benchmarks
 * Reference: American Petroleum Institute Bulletin 5C3 (6th Ed.) / ISO 10400:2007
 * and Teale (1962) "The Concept of Specific Energy in Rock Drilling".
 *
 * Verifies critical safety remedies for:
 * - ENG-01: Correct 0.10679e-5 plastic collapse coefficient (replaces 0.10679e-4 10x error)
 * - ENG-02: Grade-dependent D/t regime boundaries (dtYield, dtPlastic, dtTransition)
 * - ENG-03: Transition collapse parameters F & G strictly derived from API equations
 * - ENG-04: API 5C3 published casing collapse ratings for commercial OCTG sizes
 * - ENG-14: Teale MSE 120*pi rotary term unit conversion
 * - ENG-15: Canonical triplex single-acting pump displacement factor
 */

import { calculateCasingProperties, calculateAPI5C3Coefficients } from '../casingDesign';
import { triplexPumpFactor, bitSpecificEnergy } from '../bitsAndPower';

export interface API5C3BenchmarkResult {
  id: string;
  name: string;
  reference: string;
  expected: string;
  actual: string;
  passed: boolean;
  notes: string;
}

export interface API5C3TestSuiteSummary {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  allPassed: boolean;
  results: API5C3BenchmarkResult[];
}

export function runAPI5C3GoldenTests(): API5C3TestSuiteSummary {
  const results: API5C3BenchmarkResult[] = [];

  // 1. 7-inch 29 lb/ft Grade N-80 Casing Collapse (ENG-01, ENG-04)
  // OD = 7.000 in, t = 0.408 in, D/t = 17.16
  // Plastic collapse regime (dtYield 13.38 < 17.16 <= dtPlastic 22.47)
  // API 5C3 Published Collapse Rating: ~7,020 psi.
  // Pre-fix buggy code gave 10,756 psi (+53% unsafe error).
  const c7_29 = calculateCasingProperties(7.000, 0.408, 'N-80');
  const pass1 = Math.abs(c7_29.apiCollapsePressurePsi - 7029) <= 30 && c7_29.collapseRegime === 'plastic';
  results.push({
    id: 'api5c3-n80-7in-29lb',
    name: 'Revestimento 7" 29 lb/ft N-80 - Colapso Plástico API 5C3',
    reference: 'API Bul. 5C3 Tabela 1 & ISO 10400 Seção 3',
    expected: 'Colapso API ≈ 7,020 - 7,030 psi | Regime: Plástico (D/t = 17.16)',
    actual: `Colapso: ${c7_29.apiCollapsePressurePsi} psi | Regime: ${c7_29.collapseRegime} | Barlow Burst: ${c7_29.barlowBurstPressurePsi} psi`,
    passed: pass1,
    notes: 'Elimina superdimensionamento perigoso de 53% que sobrestimava a integridade do poço.',
  });

  // 2. 9-5/8 inch 47 lb/ft Grade N-80 Casing Collapse (ENG-01, ENG-04)
  // OD = 9.625 in, t = 0.472 in, D/t = 20.39
  // Plastic collapse regime (dtYield 13.38 < 20.39 <= dtPlastic 22.47)
  // API 5C3 Published Collapse Rating: ~4,750 psi.
  // Pre-fix buggy code gave 7,896 psi (+66% unsafe error).
  const c9_47 = calculateCasingProperties(9.625, 0.472, 'N-80');
  const pass2 = Math.abs(c9_47.apiCollapsePressurePsi - 4757) <= 25 && c9_47.collapseRegime === 'plastic';
  results.push({
    id: 'api5c3-n80-958in-47lb',
    name: 'Revestimento 9⅝" 47 lb/ft N-80 - Colapso Plástico API 5C3',
    reference: 'API Bul. 5C3 Tabela 1 & ISO 10400 Seção 3',
    expected: 'Colapso API ≈ 4,750 - 4,760 psi | Regime: Plástico (D/t = 20.39)',
    actual: `Colapso: ${c9_47.apiCollapsePressurePsi} psi | Regime: ${c9_47.collapseRegime} | Barlow Burst: ${c9_47.barlowBurstPressurePsi} psi`,
    passed: pass2,
    notes: 'Elimina erro de 66% na pressão crítica de colapso para tubulares intermediários.',
  });

  // 3. 9-5/8 inch 40 lb/ft Grade J-55 Casing Collapse (ENG-02, ENG-04)
  // OD = 9.625 in, t = 0.395 in, D/t = 24.37
  // J-55 plastic regime: dtYield 14.81 < 24.37 <= dtPlastic 25.01
  // API 5C3 Published Rating: ~2,570 psi
  const c9_40_j55 = calculateCasingProperties(9.625, 0.395, 'J-55');
  const pass3 = Math.abs(c9_40_j55.apiCollapsePressurePsi - 2573) <= 25;
  results.push({
    id: 'api5c3-j55-958in-40lb',
    name: 'Revestimento 9⅝" 40 lb/ft J-55 - Limites de D/t de Grau Padrão',
    reference: 'API Bul. 5C3 Tabela 1 (Yp = 55,000 psi)',
    expected: 'Colapso API ≈ 2,570 psi | D/t = 24.37 (Limite Plástico J-55: 25.01)',
    actual: `Colapso: ${c9_40_j55.apiCollapsePressurePsi} psi | Regime: ${c9_40_j55.collapseRegime}`,
    passed: pass3,
    notes: 'Comprova fronteiras dinâmicas e contínuas de escoamento para aço doce grau J-55.',
  });

  // 4. Thick-Walled Yield Strength Collapse Regime (ENG-02)
  // 5-inch heavy-wall casing (t = 0.490 in, D/t = 10.20 <= dtYield 13.38)
  // Formula: Pc = 2 * Yp * (D/t - 1) / (D/t)^2 = 2 * 80000 * 9.20 / 104.04 = 14,148 psi
  const c5_heavy = calculateCasingProperties(5.000, 0.490, 'N-80');
  const pass4 = Math.abs(c5_heavy.apiCollapsePressurePsi - 14148) <= 20 && c5_heavy.collapseRegime === 'yield';
  results.push({
    id: 'api5c3-yield-collapse-regime',
    name: 'Regime de Colapso por Tensão de Escoamento (Paredes Espessas Lamé)',
    reference: 'API Bul. 5C3 Eq. 3.1 & Bourgoyne Eq. 7.3 (D/t <= 13.38)',
    expected: 'Colapso por Escoamento = 14,148 psi | Regime: "yield"',
    actual: `Colapso: ${c5_heavy.apiCollapsePressurePsi} psi | Regime: ${c5_heavy.collapseRegime}`,
    passed: pass4,
    notes: 'Validação da equação elasto-plástica de Lamé para tubulares de altíssima espessura.',
  });

  // 5. Thin-Walled Elastic Instability Collapse Regime (Euler Buckling)
  // 13-3/8 inch 48 lb/ft (t = 0.330 in, D/t = 40.53 > dtTransition 31.02)
  // Formula: Pc = 46.95e6 / (D/t * (D/t - 1)^2) = 46.95e6 / (40.53 * 39.53^2) = 742 psi
  const c13_thin = calculateCasingProperties(13.375, 0.330, 'N-80');
  const pass5 = Math.abs(c13_thin.apiCollapsePressurePsi - 742) <= 15 && c13_thin.collapseRegime === 'elastic';
  results.push({
    id: 'api5c3-elastic-collapse-regime',
    name: 'Regime de Instabilidade Elástica de Euler (Tubulares de Grande Diâmetro)',
    reference: 'API Bul. 5C3 Eq. 3.4 & Clinedinst Theory (D/t > 31.02)',
    expected: 'Colapso Elástico = 742 psi (Independente de Yp) | Regime: "elastic"',
    actual: `Colapso: ${c13_thin.apiCollapsePressurePsi} psi | Regime: ${c13_thin.collapseRegime}`,
    passed: pass5,
    notes: 'Comprova instabilidade geométrica estrutural sem dependência da resistência ao escoamento.',
  });

  // 6. Teale (1962) Mechanical Specific Energy (ENG-14)
  // Bit 8.5", WOB = 30,000 lbf, 100 RPM, 50 ft/hr, Torque = 1,500 ft-lbf
  // Bit Area = pi/4 * 8.5^2 = 56.745 sq in
  // Axial = 30000 / 56.745 = 528.7 psi
  // Rotary = (120 * pi * 100 * 1500) / (56.745 * 50) = 19,931 psi
  // MSE = 528.7 + 19,931 = 20,460 psi
  const mse = bitSpecificEnergy(30000, 100, 8.5, 50, 1500);
  const pass6 = Math.abs(mse - 20460) <= 25;
  results.push({
    id: 'drilling-teale-mse-benchmark',
    name: 'Energia Específica Mecânica de Perfuração Teale (MSE)',
    reference: 'Teale (1962) Eq. 1 & Bourgoyne Ch. 5, Eq. 5.15',
    expected: 'MSE = 20,460 psi (Termo Rotacional Teale 120·π·N·T / A·ROP)',
    actual: `MSE = ${mse.toLocaleString()} psi (Axial ≈ 529 psi, Rotacional ≈ 19,931 psi)`,
    passed: pass6,
    notes: 'Corrige omissão de 12× na conversão de polegadas-para-pés no trabalho rotacional de corte.',
  });

  // 7. Canonical Triplex Pump Output (ENG-15)
  // Liner 6.0", Stroke 12.0", Ev = 0.95
  // Fp = 3 * (12/12) * 6^2 / 1029.4 * 0.95 = 108 / 1029.4 * 0.95 = 0.09966 bbl/stk -> 0.100 bbl/stk
  const triplexOutput = triplexPumpFactor(6.0, 12.0, 0.95);
  const pass7 = Math.abs(triplexOutput - 0.100) <= 0.002;
  results.push({
    id: 'drilling-triplex-pump-factor',
    name: 'Deslocamento Volumétrico de Bomba Triplex de Ação Simples',
    reference: 'Bourgoyne Ch. 1, Eq. 1.10 - 1.12 & API Formulas',
    expected: 'Fp = 0.100 bbl/stk (com camisa de 6", curso de 12" e Ev = 95%)',
    actual: `Fp = ${triplexOutput.toFixed(3)} bbl/stk`,
    passed: pass7,
    notes: 'Elimina aplicação duplicada de π/4 que gerava subestimação de 21.5% na taxa de bombeio.',
  });

  const passedTests = results.filter((r) => r.passed).length;

  return {
    totalTests: results.length,
    passedTests,
    failedTests: results.length - passedTests,
    allPassed: passedTests === results.length,
    results,
  };
}

export const runApi5c3GoldenTests = runAPI5C3GoldenTests;

