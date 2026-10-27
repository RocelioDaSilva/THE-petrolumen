/**
 * Bourgoyne et al. (SPE Applied Drilling Engineering) Golden Benchmarks
 * Reference: Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering", SPE Textbook Series, Vol. 2, 1986.
 *
 * Verifies 8 core engineering benchmarks from Chapters 1-8.
 */

import { calculateHoistingSystem, duplexPumpFactor, hydraulicHorsepower } from '../bitsAndPower';
import { calculateFannRheology, bariteRequired } from '../fluids';
import { designCementSlurry } from '../cements';
import { calculateBitHydraulics } from '../hydraulicsBourgoyne';
import { calculateCasingProperties } from '../casingDesign';
import { calculateMinimumCurvature, SurveyStation } from '../directional';

export interface BourgoyneTestResult {
  id: string;
  chapter: string;
  name: string;
  reference: string;
  expected: string;
  actual: string;
  passed: boolean;
  notes: string;
}

export interface BourgoyneTestSuiteSummary {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  allPassed: boolean;
  results: BourgoyneTestResult[];
}

export function runBourgoyneGoldenTests(): BourgoyneTestSuiteSummary {
  const results: BourgoyneTestResult[] = [];

  // 1. Ch. 1 — Hoisting Fast-Line & Derrick Load (Example 1.1)
  // W = 500,000 lbf, 10 lines strung, E = 0.810
  // F_f = 500,000 / (0.810 * 10) = 61,728 lbf
  // F_d = ((1 + 0.810 + 8.10) / 8.10) * 500,000 = 611,728 lbf
  const hoistRes = calculateHoistingSystem(500000, 10, 1000, 0.810);
  const hoistPassed = Math.abs(hoistRes.fastLineTensionLbf - 61728) <= 5 &&
                      Math.abs(hoistRes.derrickLoadLbf - 611728) <= 5;
  results.push({
    id: 'bourgoyne-ch1-hoisting',
    chapter: 'Capítulo 1: Equipamentos & Potência',
    name: 'Cargas no Sistema de Elevação (Tensão na Linha Rápida & Carga no Mastro)',
    reference: 'Bourgoyne (1986) Exemplo 1.1, Eq. 1.4 & 1.5',
    expected: 'F_fast = 61,728 lbf | F_derrick = 611,728 lbf (com 10 linhas, E = 0.810)',
    actual: `F_fast = ${hoistRes.fastLineTensionLbf.toLocaleString()} lbf | F_derrick = ${hoistRes.derrickLoadLbf.toLocaleString()} lbf`,
    passed: hoistPassed,
    notes: 'Valida a distribuição de forças estáticas e dinâmicas nos cabos e pernas da torre.',
  });

  // 2. Ch. 1 — Duplex Pump Factor & Hydraulic Horsepower (Example 1.4)
  // 6.5" liner, 2.5" rod, 18" stroke, Ev = 0.90 -> F_p = 0.205 bbl/stk
  // Delta P = 3000 psi, Q = 350 gpm -> HHP = 613 hp
  const fp = duplexPumpFactor(6.5, 2.5, 18, 0.90);
  const hhp = hydraulicHorsepower(3000, 350);
  const pumpPassed = Math.abs(fp - 0.205) <= 0.005 && Math.abs(hhp - 613) <= 2;
  results.push({
    id: 'bourgoyne-ch1-duplex-hhp',
    chapter: 'Capítulo 1: Equipamentos & Bombas',
    name: 'Fator de Deslocamento de Bomba Duplex de Ação Dupla & Potência Hidráulica',
    reference: 'Bourgoyne (1986) Exemplo 1.4, Eq. 1.10 & 1.14',
    expected: 'Fp = 0.205 bbl/stk | HHP = 613 hp (a 3000 psi & 350 gpm)',
    actual: `Fp = ${fp} bbl/stk | HHP = ${hhp} hp`,
    passed: pumpPassed,
    notes: 'Considera a haste do pistão na câmara frontal de bombas de duplo efeito.',
  });

  // 3. Ch. 2 — Fann 35 Rheology Model Fit (Example 2.1)
  // theta600 = 65, theta300 = 40
  // Plastic Viscosity = 25 cP, Yield Point = 15 lbf/100ft2, n = 0.700, K = 260.3 eq cP
  const rheo = calculateFannRheology(65, 40);
  const rheoPassed = rheo.plasticViscosityCp === 25 &&
                     rheo.yieldPointLbf100ft2 === 15 &&
                     Math.abs(rheo.powerLawN - 0.700) <= 0.005;
  results.push({
    id: 'bourgoyne-ch2-rheology',
    chapter: 'Capítulo 2: Fluidos de Perfuração',
    name: 'Reologia Rotacional Fann (Viscosidade Plástica, Limite de Escoamento & Lei de Potência)',
    reference: 'Bourgoyne (1986) Exemplo 2.1, Eq. 2.1 - 2.5',
    expected: 'PV = 25 cP | YP = 15 lbf/100ft² | n = 0.700 | K ≈ 260 cP',
    actual: `PV = ${rheo.plasticViscosityCp} cP | YP = ${rheo.yieldPointLbf100ft2} lbf/100ft² | n = ${rheo.powerLawN} | K = ${rheo.powerLawK} eq cP`,
    passed: rheoPassed,
    notes: 'Ajuste de modelos reológicos Bingham Plastic e Ostwald-de Waele (Power-Law).',
  });

  // 4. Ch. 2 — Weighting Up with Barite (Example 2.16)
  // V1 = 500 bbl, rho1 = 10.0 ppg, target rho2 = 12.0 ppg, barite = 35.0 ppg
  // Required barite = 15,217 lbm = 153 sacks (100 lb)
  const bariteRes = bariteRequired(500, 10.0, 12.0, 35.0);
  const baritePassed = Math.abs(bariteRes.bariteTotalLbm - 15217) <= 10 &&
                       bariteRes.bariteSacksRequired === 153;
  results.push({
    id: 'bourgoyne-ch2-weight-up',
    chapter: 'Capítulo 2: Engenharia de Lama',
    name: 'Adensamento de Fluido com Baritina (Equações de Mistura Ideal)',
    reference: 'Bourgoyne (1986) Exemplo 2.16, Eq. 2.22',
    expected: '15,217 lbm de baritina (153 sacos de 100 lb) | Aumento de volume ~ 10.3 bbl',
    actual: `${bariteRes.bariteTotalLbm.toLocaleString()} lbm (${bariteRes.bariteSacksRequired} sacos) | Vol final: ${bariteRes.finalVolumeBbl} bbl`,
    passed: baritePassed,
    notes: 'Preserva a conservação de massa e volume considerando gravidade específica da baritina = 4.2.',
  });

  // 5. Ch. 3 — API Class G Slurry Design (Example 3.4)
  // Class G neat cement: 44% mix water -> Yield = 1.15 ft3/sk, Density = 15.8 ppg
  const cementRes = designCementSlurry('Class G');
  const cementPassed = Math.abs(cementRes.slurryYieldFt3Sack - 1.15) <= 0.05 &&
                       Math.abs(cementRes.slurryDensityPpg - 15.8) <= 0.2;
  results.push({
    id: 'bourgoyne-ch3-cement-slurry',
    chapter: 'Capítulo 3: Cimentação de Poços',
    name: 'Dimensionamento de Pasta de Cimento API Classe G (Rendimento & Densidade)',
    reference: 'Bourgoyne (1986) Exemplo 3.4, Tabela 3.6',
    expected: 'Rendimento = 1.15 ft³/sk | Densidade = 15.8 ppg | Água = 4.96 gal/sk (44% BWOC)',
    actual: `Rendimento = ${cementRes.slurryYieldFt3Sack} ft³/sk | Densidade = ${cementRes.slurryDensityPpg} ppg | Água = ${cementRes.waterGallonsPerSack} gal/sk`,
    passed: cementPassed,
    notes: 'Baseado na massa de 94 lb/sk e volume absoluto do cimento Portland = 0.478 ft³/sk.',
  });

  // 6. Ch. 4 — Jet Bit Hydraulics & Nozzle Pressure Drop (Example 4.6)
  // Three 12/32" nozzles -> At = 0.331 in2
  // Q = 400 gpm, rho = 10.0 ppg, Cd = 0.95 -> Delta Pb ≈ 1,490 psi
  const bitRes = calculateBitHydraulics(400, 10.0, [12, 12, 12], 8.5, 0.95);
  const bitPassed = Math.abs(bitRes.totalNozzleAreaSqIn - 0.331) <= 0.005 &&
                    Math.abs(bitRes.bitPressureDropPsi - 1490) <= 20;
  results.push({
    id: 'bourgoyne-ch4-bit-hydraulics',
    chapter: 'Capítulo 4: Hidráulica de Perfuração',
    name: 'Queda de Pressão nos Jatos da Broca & Força de Impacto',
    reference: 'Bourgoyne (1986) Exemplo 4.6, Eq. 4.31 & 4.34',
    expected: 'Área Total = 0.331 pol² | ΔPb ≈ 1,490 psi | HHP_broca ≈ 348 hp',
    actual: `Área = ${bitRes.totalNozzleAreaSqIn} pol² | ΔPb = ${bitRes.bitPressureDropPsi} psi | HHP = ${bitRes.hydraulicHorsepowerBit} hp | JIF = ${bitRes.jetImpactForceLbf} lbf`,
    passed: bitPassed,
    notes: 'Calcula velocidade dos jatos (vn = 388 ft/s) e potência hidráulica por polegada quadrada (HSI).',
  });

  // 7. Ch. 7 — Barlow Burst Pressure for API Casing (Example 7.1)
  // 9-5/8" casing, t = 0.435", Grade N-80 (Yp = 80,000 psi)
  // Barlow Burst = 0.875 * (2 * 80,000 * 0.435) / 9.625 = 6,327 psi
  const casingRes = calculateCasingProperties(9.625, 0.435, 'N-80');
  const casingPassed = Math.abs(casingRes.barlowBurstPressurePsi - 6327) <= 10;
  results.push({
    id: 'bourgoyne-ch7-casing-burst',
    chapter: 'Capítulo 7: Projeto de Revestimento',
    name: 'Pressão de Ruptura API (Fórmula de Barlow com Tolerância de Espessura de 12.5%)',
    reference: 'Bourgoyne (1986) Exemplo 7.1, Eq. 7.2',
    expected: 'Pressão de Ruptura = 6,327 psi (Tolerância API de 12.5% na espessura de parede)',
    actual: `Pressão de Ruptura = ${casingRes.barlowBurstPressurePsi} psi | Colapso API: ${casingRes.apiCollapsePressurePsi} psi | Escoamento: ${casingRes.pipeBodyYieldLbf.toLocaleString()} lbf`,
    passed: casingPassed,
    notes: 'Avalia resistência nominal em conformidade com o boletim API 5C3.',
  });

  // 8. Ch. 8 — Directional Survey via Minimum Curvature (Example 8.1)
  // Survey Station 1: 10,000 ft MD, 15.0 deg Inc, 45.0 deg Azi
  // Survey Station 2: 10,100 ft MD, 18.0 deg Inc, 50.0 deg Azi
  // dMD = 100 ft -> DLS ≈ 3.28 deg / 100 ft
  const stations: SurveyStation[] = [
    { measuredDepthFt: 10000, inclinationDeg: 15.0, azimuthDeg: 45.0 },
    { measuredDepthFt: 10100, inclinationDeg: 18.0, azimuthDeg: 50.0 },
  ];
  const surveyRes = calculateMinimumCurvature(stations);
  const dls = surveyRes[1]?.doglegSeverityDeg100ft || 0;
  const surveyPassed = Math.abs(dls - 3.28) <= 0.05;
  results.push({
    id: 'bourgoyne-ch8-min-curvature',
    chapter: 'Capítulo 8: Poços Direcionais',
    name: 'Levantamento Trajetográfico por Curvatura Mínima & Dogleg Severity (DLS)',
    reference: 'Bourgoyne (1986) Exemplo 8.1, Eq. 8.1 - 8.5',
    expected: 'DLS ≈ 3.28°/100 ft | Fator de Razão F ≈ 1.0001',
    actual: `DLS = ${dls}°/100 ft | ΔTVD = ${(surveyRes[1]?.tvd - surveyRes[0]?.tvd).toFixed(1)} ft | Fechamento: ${surveyRes[1]?.closureDistanceFt} ft @ ${surveyRes[1]?.closureAzimuthDeg}°`,
    passed: surveyPassed,
    notes: 'Algoritmo padrão SPE/API para interpolação de trajetórias tridimensionais de poço.',
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
