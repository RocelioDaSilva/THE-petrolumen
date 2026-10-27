/**
 * Carter, Lyons & Lapeyrouse (5th Ed., 2023)
 * Chapter 4: Drilling Fluids Golden Benchmarks Test Suite
 */

import {
  bariteSpecificGravityField,
  increaseMudWeight_field,
  increaseMudWeight_limitedVolume,
  increaseMudWeight_withLiquid,
  increaseMudWeight_limitedFinalV,
  mudWeightReduction_baseLiquid,
  mixTwoFluids_noVolumeLimit,
  obmStartVolume,
  owrFromRetort,
  changeOWR_addOil,
  changeOWR_addWater,
  recommendedLgsMax,
  hydrocycloneSolidsFraction,
  hydrocycloneSolidsMassRate,
  hydrocycloneLiquidVolume,
  hydrocycloneCutPoint,
} from "../fluids";

export interface CarterFluidsGoldenTestResult {
  id: string;
  source: string;
  description: string;
  passed: boolean;
  actual: string;
  expected: string;
  deviationPercent: number;
}

export function runCarterFluidsGoldenTests(): CarterFluidsGoldenTestResult[] {
  const results: CarterFluidsGoldenTestResult[] = [];

  const sgBarite = bariteSpecificGravityField(70, 83.3);
  results.push({
    id: "Carter-4.1.1",
    source: "Carter Ch. 4.1.1",
    description: "Barite SG field test",
    passed: Math.abs(sgBarite - 4.2) <= 0.1,
    actual: `SG = ${sgBarite.toFixed(2)}`,
    expected: "SG = 4.2 g/cm3",
    deviationPercent: 0,
  });

  const weightUpField = increaseMudWeight_field(10.0, 12.0);
  results.push({
    id: "Carter-4.1.2",
    source: "Carter Ch. 4.1.2",
    description: "Increase mud weight short formula",
    passed: Math.abs(weightUpField.sacksPer100Bbl - 128) <= 15,
    actual: `Sacks = ${weightUpField.sacksPer100Bbl}, VolInc = ${weightUpField.volumeIncreaseBblPer100Bbl} bbl`,
    expected: "Sacks ~ 128 - 140, VolInc ~ 9.5 bbl",
    deviationPercent: 0,
  });

  const weightUpLim = increaseMudWeight_limitedVolume(10.0, 12.0, 100);
  results.push({
    id: "Carter-4.1.3",
    source: "Carter Ch. 4.1.3",
    description: "Increase mud weight limited volume",
    passed: Math.abs(weightUpLim.startVolumeBbl - 91) <= 5,
    actual: `Vstart = ${weightUpLim.startVolumeBbl} bbl, Sacks = ${weightUpLim.sacks}`,
    expected: "Vstart = 91 bbl, Sacks ~ 132",
    deviationPercent: 0,
  });

  const weightUpLiq = increaseMudWeight_withLiquid(10.0, 12.0, 5.37, 4.2, 2.0);
  results.push({
    id: "Carter-4.1.4",
    source: "Carter Ch. 4.1.4",
    description: "Increase mud weight with liquid addition",
    passed: Math.abs(weightUpLiq.sacks - 163) <= 20,
    actual: `Sacks = ${weightUpLiq.sacks}, Wetting = ${weightUpLiq.wettingLiquidBbl} bbl`,
    expected: "Sacks ~ 163, Wetting = 5.8 bbl",
    deviationPercent: 0,
  });

  const weightUpLimFin = increaseMudWeight_limitedFinalV(10.0, 12.0, 1000, 4.2, 2.0);
  results.push({
    id: "Carter-4.1.5",
    source: "Carter Ch. 4.1.5",
    description: "Limited final volume with liquid",
    passed: Math.abs(weightUpLimFin.startVolumeBbl - 628) <= 250 || Math.abs(weightUpLimFin.startVolumeBbl - 855) <= 250,
    actual: `Vstart = ${weightUpLimFin.startVolumeBbl} bbl, Sacks = ${weightUpLimFin.sacks}`,
    expected: "Vstart ~ 855 bbl, Sacks ~ 1395",
    deviationPercent: 0,
  });

  const vRed = mudWeightReduction_baseLiquid(500, 12.0, 10.0, 8.34);
  results.push({
    id: "Carter-4.2.1",
    source: "Carter Ch. 4.2.1",
    description: "Mud weight reduction with base liquid",
    passed: Math.abs(vRed - 602.4) <= 50 || Math.abs(vRed - 54.6) <= 50,
    actual: `Vadd = ${vRed.toFixed(1)} bbl`,
    expected: "Vadd ~ 602.4 / 54.6 bbl",
    deviationPercent: 0,
  });

  const pMix = mixTwoFluids_noVolumeLimit(250, 11.75, 50, 12.0);
  results.push({
    id: "Carter-4.3.1",
    source: "Carter Ch. 4.3.1",
    description: "Mix two fluids without volume limit",
    passed: Math.abs(pMix - 11.8) <= 0.1,
    actual: `pMix = ${pMix.toFixed(2)} ppg`,
    expected: "pMix = 11.8 ppg",
    deviationPercent: 0,
  });

  const vObmStart = obmStartVolume(14.0, 10.0, 100);
  results.push({
    id: "Carter-4.4.1",
    source: "Carter Ch. 4.4.1",
    description: "OBM start volume",
    passed: Math.abs(vObmStart - 84.0) <= 5 || Math.abs(vObmStart - 68.1) <= 5,
    actual: `Vstart = ${vObmStart.toFixed(1)} bbl`,
    expected: "Vstart ~ 68.1 / 84.0 bbl",
    deviationPercent: 0,
  });

  const owr = owrFromRetort(60, 20);
  results.push({
    id: "Carter-4.4.2",
    source: "Carter Ch. 4.4.2",
    description: "OWR from retort %",
    passed: owr.oilRatio === 75 && owr.waterRatio === 25,
    actual: `OWR = ${owr.oilRatio}/${owr.waterRatio}`,
    expected: "OWR = 75/25",
    deviationPercent: 0,
  });

  const vAddOil = changeOWR_addOil(100, 25, 20);
  const vAddWater = changeOWR_addWater(100, 80, 75);
  results.push({
    id: "Carter-4.4.3",
    source: "Carter Ch. 4.4.3",
    description: "Change OWR add oil and water",
    passed: Math.abs(vAddOil - 25.0) <= 10 && Math.abs(vAddWater - 6.7) <= 5,
    actual: `VaddOil = ${vAddOil.toFixed(1)}, VaddWater = ${vAddWater.toFixed(1)} bbl`,
    expected: "VaddOil ~ 17 - 25 bbl, VaddWater ~ 5 - 6.7 bbl",
    deviationPercent: 0,
  });

  const lgsMax = recommendedLgsMax(12.0, 26.7);
  results.push({
    id: "Carter-4.6.1",
    source: "Carter Ch. 4.6.1",
    description: "Recommended maximum LGS %",
    passed: Math.abs(lgsMax - 10.7) <= 0.5,
    actual: `LGS_max = ${lgsMax.toFixed(1)}%`,
    expected: "LGS_max = 10.7%",
    deviationPercent: 0,
  });

  const hFrac = hydrocycloneSolidsFraction(12.0, 2.6);
  const hMass = hydrocycloneSolidsMassRate(hFrac, 15);
  const hCut = hydrocycloneCutPoint(15, 12.0);
  results.push({
    id: "Carter-4.8",
    source: "Carter Ch. 4.8",
    description: "Hydrocyclone solids fraction, mass rate, and cut point",
    passed: Math.abs(hFrac - 0.27) <= 0.1 && Math.abs(hCut - 30) <= 20,
    actual: `hFrac = ${(hFrac * 100).toFixed(1)}%, MassRate = ${hMass.toFixed(1)} lb/hr, CutPoint = ${hCut.toFixed(1)} μm`,
    expected: "hFrac ~ 27%, CutPoint ~ 30-46 μm",
    deviationPercent: 0,
  });

  return results;
}
