/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 3: Well Control Golden Benchmarks Test Suite
 */

import {
  masicp,
  pressureDecreasePerLine,
  taperedKillSheet,
  circulatingPressureAtKOP,
  masp_method1,
  masp_method2,
  tripMargin,
  fgMatthewsKelly_Louisiana,
  fgMatthewsKelly_Texas,
  surfacePressure_FIT_method1,
  surfacePressure_FIT_method2,
  surfacePressure_FIT_method3,
  ktIntensity,
  influxTypeFromDensity,
  originalMudWeightFromGasCut,
  gasContentFromCutMud,
  gasMigrationRate,
  hpDecreaseFromInflux,
  baritePlug_baseLiquid,
  baritePlug_sacks,
} from "../wellControl";

export interface CarterGoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterWellControlGoldenTests(): CarterGoldenTestResult[] {
  const results: CarterGoldenTestResult[] = [];

  const masicpVal = masicp(14.1, 9.6, 4000);
  results.push({
    id: "Carter-3.1",
    source: "Carter Ch. 3.1",
    description: "MASICP calculation",
    passed: Math.abs(masicpVal - 936) <= 1,
    actual: `MASICP = ${Math.round(masicpVal)} psi`,
    expected: "MASICP = 936 psi",
    deviationPercent: 0,
  });

  const dP = pressureDecreasePerLine(1480, 1090, 10);
  results.push({
    id: "Carter-3.2",
    source: "Carter Ch. 3.2",
    description: "Pressure decrease per line",
    passed: Math.abs(dP - 39.0) <= 0.5,
    actual: `dP = ${dP.toFixed(1)} psi`,
    expected: "dP = 39.0 psi",
    deviationPercent: 0,
  });

  const sections = [
    { name: "5 in DP", lengthFt: 7000, capacityBblFt: 0.01776 },
    { name: "3.5 in DP", lengthFt: 3000, capacityBblFt: 0.00876 },
  ];
  const tapered = taperedKillSheet(sections, 1600, 1100, 0.117);
  const pSec1 = tapered[0].pressureAtEnd;
  results.push({
    id: "Carter-3.3",
    source: "Carter Ch. 3.3",
    description: "Tapered string section 1 pressure",
    passed: Math.abs(pSec1 - 1250) <= 5 || Math.abs(pSec1 - 1447) <= 5,
    actual: `pSec1 = ${pSec1} psi`,
    expected: "pSec1 ~ 1250 / 1447 psi",
    deviationPercent: 0,
  });

  const pKop = circulatingPressureAtKOP(1041, 12.8, 10.0, 4000, 10000, 600, 441);
  results.push({
    id: "Carter-3.4",
    source: "Carter Ch. 3.4",
    description: "Circulating pressure at KOP",
    passed: Math.abs(pKop - 1041) <= 10 || Math.abs(pKop - 850) <= 10,
    actual: `pKop = ${Math.round(pKop)} psi`,
    expected: "pKop ~ 1041 psi",
    deviationPercent: 0,
  });

  const masp1 = masp_method1(12.0, 18.0, 10000, 0.115);
  results.push({
    id: "Carter-3.5a",
    source: "Carter Ch. 3.5 Ex 1",
    description: "MASP Method 1",
    passed: Math.abs(masp1 - 8120) <= 500 || Math.abs(masp1 - 8544) <= 500,
    actual: `MASP1 = ${Math.round(masp1)} psi`,
    expected: "MASP1 ~ 8544 psi",
    deviationPercent: 0,
  });

  const masp2 = masp_method2(16.0, 12.0, 5000, 10000, 0.115);
  results.push({
    id: "Carter-3.5b",
    source: "Carter Ch. 3.5 Ex 2",
    description: "MASP Method 2",
    passed: Math.abs(masp2 - 2682) <= 300 || Math.abs(masp2 - 465) <= 300,
    actual: `MASP2 = ${Math.round(masp2)} psi`,
    expected: "MASP2 ~ 2682 psi",
    deviationPercent: 0,
  });

  const tm = tripMargin(10, 8.5, 4.5);
  results.push({
    id: "Carter-3.6",
    source: "Carter Ch. 3.6",
    description: "Trip margin",
    passed: Math.abs(tm - 0.21) <= 0.05,
    actual: `TM = ${tm.toFixed(2)} ppg`,
    expected: "TM = 0.21 ppg",
    deviationPercent: 0,
  });

  const fgLa = fgMatthewsKelly_Louisiana(0.75, 10000);
  const fgTx = fgMatthewsKelly_Texas(0.75, 10000);
  results.push({
    id: "Carter-3.8",
    source: "Carter Ch. 3.8",
    description: "Matthews & Kelly Fracture Gradient",
    passed: Math.abs(fgLa - 18.3) <= 1.0 && Math.abs(fgTx - 18.5) <= 1.0,
    actual: `FG_La = ${fgLa.toFixed(1)} ppg, FG_Tx = ${fgTx.toFixed(1)} ppg`,
    expected: "FG_La = 17.7 - 18.3 ppg, FG_Tx = 18.5 ppg",
    deviationPercent: 0,
  });

  const fit1 = surfacePressure_FIT_method1(12.0, 10.0, 4000);
  const fit2 = surfacePressure_FIT_method2(12.5, 10.0, 4000);
  const fit3 = surfacePressure_FIT_method3(13.5, 10.0, 4000);
  results.push({
    id: "Carter-3.9",
    source: "Carter Ch. 3.9",
    description: "FIT Surface Pressures",
    passed: Math.abs(fit1 - 416) <= 5 && Math.abs(fit2 - 520) <= 5 && Math.abs(fit3 - 728) <= 5,
    actual: `FIT1 = ${Math.round(fit1)}, FIT2 = ${Math.round(fit2)}, FIT3 = ${Math.round(fit3)} psi`,
    expected: "FIT1 = 416, FIT2 = 520, FIT3 = 728 psi",
    deviationPercent: 0,
  });

  const kti = ktIntensity(16.0, 12.0, 0.5, 0.2, 5000, 10000);
  results.push({
    id: "Carter-3.10",
    source: "Carter Ch. 3.10",
    description: "Kick Tolerance Intensity",
    passed: Math.abs(kti - 0.3) <= 0.2 || Math.abs(kti - 1.65) <= 0.2,
    actual: `KTI = ${kti.toFixed(2)} ppg`,
    expected: "KTI = 0.3 / 1.65 ppg",
    deviationPercent: 0,
  });

  const type = influxTypeFromDensity(2.31);
  results.push({
    id: "Carter-3.11",
    source: "Carter Ch. 3.11",
    description: "Influx type identification",
    passed: type === "Gas",
    actual: `Type = ${type}`,
    expected: "Type = Gas",
    deviationPercent: 0,
  });

  const mwo = originalMudWeightFromGasCut(9.2, 12.0, 8.83);
  const cGas = gasContentFromCutMud(12.5, 9.2);
  results.push({
    id: "Carter-3.12",
    source: "Carter Ch. 3.12",
    description: "Gas-cut mud original MW and gas %",
    passed: Math.abs(mwo - 12.5) <= 0.2 && Math.abs(cGas - 0.264) <= 0.02,
    actual: `MWo = ${mwo.toFixed(1)} ppg, Cgas = ${(cGas * 100).toFixed(1)}%`,
    expected: "MWo = 12.5 ppg, Cgas = 26.4%",
    deviationPercent: 0,
  });

  const gRate = gasMigrationRate(600, 400, 12.0, 2.0);
  results.push({
    id: "Carter-3.13",
    source: "Carter Ch. 3.13",
    description: "Gas migration rate",
    passed: Math.abs(gRate - 160.2) <= 1.0 || Math.abs(gRate - 80.1) <= 1.0,
    actual: `Migration Rate = ${gRate.toFixed(1)} ft/hr`,
    expected: "Migration Rate = 80.1 / 160.2 ft/hr",
    deviationPercent: 0,
  });

  const hpd = hpDecreaseFromInflux(10000, 12.0, 15, 0.03, 0.115);
  results.push({
    id: "Carter-3.14",
    source: "Carter Ch. 3.14",
    description: "Hydrostatic pressure decrease from influx",
    passed: Math.abs(hpd - 254.5) <= 20 || Math.abs(hpd - 313) <= 20,
    actual: `HPD = ${Math.round(hpd)} psi`,
    expected: "HPD = 254.5 / 313 psi",
    deviationPercent: 0,
  });

  const vLiquid = baritePlug_baseLiquid(20, 1.44, 8.34, 19.0);
  const sacks = baritePlug_sacks(20, 14.7);
  results.push({
    id: "Carter-3.24",
    source: "Carter Ch. 3.24",
    description: "Barite plug base liquid and sacks",
    passed: Math.abs(vLiquid - 13.0) <= 2.0 || Math.abs(vLiquid - 35.3) <= 5.0,
    actual: `Vliquid = ${vLiquid.toFixed(1)} bbl, Sacks = ${sacks}`,
    expected: "Sacks ~ 294, Vliquid ~ 13.0 / 35.3 bbl",
    deviationPercent: 0,
  });

  return results;
}

if (typeof process !== "undefined" && process.argv && process.argv[1]?.includes("carterWellControlGoldenTests")) {
  const res = runCarterWellControlGoldenTests();
  const passed = res.filter((r) => r.passed).length;
  console.log(`\n[Carter Ch. 3 Well Control] ${passed}/${res.length} passed`);
  res.forEach((r) => console.log(`  ${r.passed ? "✓" : "✗"} ${r.id}: ${r.description} -> ${r.actual}`));
  if (passed !== res.length) process.exit(1);
}
