/**
 * PetroLúmen Master Golden Benchmarks Test Runner
 * Executes all 11 verified engineering benchmark suites documented across:
 * - Cormack (2017) [Well Control & Swab Pressures]
 * - Bourgoyne et al. (1986) [Rig Hoisting, Mud Rheology, Hydraulics, Casing Burst, Directional]
 * - API Bulletin 5C3 & Teale (1962) [Casing Collapse Regimes & Mechanical Specific Energy]
 * - Arnold & Stewart (2008) [2-Phase & 3-Phase Separators, Vessels, Treating, CPI]
 * - Carter, Lyons & Lapeyrouse (5th Ed., 2023) [8 Suites: Well Control, Fluids, Cements, Hydraulics, Rig Ops, Stuck Pipe, Phase 7, Phase 8]
 */

import { runCormackGoldenTests } from './lib/drilling/__tests__/cormackGoldenTests';
import { runBourgoyneGoldenTests } from './lib/drilling/__tests__/bourgoyneGoldenTests';
import { runApi5c3GoldenTests } from './lib/drilling/__tests__/api5c3GoldenTests';
import { runArnoldStewartGoldenTests } from './lib/facilities/__tests__/arnoldStewartGoldenTests';
import { runCarterWellControlGoldenTests } from './lib/drilling/__tests__/carterWellControlGoldenTests';
import { runCarterFluidsGoldenTests } from './lib/drilling/__tests__/carterFluidsGoldenTests';
import { runCarterCementsGoldenTests } from './lib/drilling/__tests__/carterCementsGoldenTests';
import { runCarterHydraulicsGoldenTests } from './lib/drilling/__tests__/carterHydraulicsGoldenTests';
import { runCarterRigOpsGoldenTests } from './lib/drilling/__tests__/carterRigOpsGoldenTests';
import { runCarterStuckPipeGoldenTests } from './lib/drilling/__tests__/carterStuckPipeGoldenTests';
import { runCarterPhase7GoldenTests } from './lib/drilling/__tests__/carterPhase7GoldenTests';
import { runCarterPhase8GoldenTests } from './lib/drilling/__tests__/carterPhase8GoldenTests';

console.log('======================================================================');
console.log('PetroLúmen Verified Petroleum Engineering Benchmark Suite');
console.log('11 Golden Benchmark Suites • Carter, Bourgoyne, API 5C3, Cormack, A&S');
console.log('======================================================================\n');

let hasFailure = false;
let grandTotalTests = 0;
let grandTotalPassed = 0;

function reportSuite(title: string, tests: Array<{ id: string; description?: string; name?: string; passed: boolean; actual?: string }>) {
  const passed = tests.filter((t) => t.passed).length;
  grandTotalTests += tests.length;
  grandTotalPassed += passed;
  console.log(`\n[${title}] ${passed}/${tests.length} passed`);
  for (const t of tests) {
    const symbol = t.passed ? '✓' : '✗';
    const label = t.name || t.description || t.id;
    console.log(`  ${symbol} ${t.id}: ${label}`);
    if (!t.passed) {
      hasFailure = true;
      if (t.actual) console.log(`      Actual: ${t.actual}`);
    }
  }
}

// 1. Cormack Suite (7 tests)
const cormack = runCormackGoldenTests();
reportSuite('Cormack 2017 (Well Control & Tripping)', cormack.results);

// 2. Bourgoyne Suite (8 tests)
const bourgoyne = runBourgoyneGoldenTests();
reportSuite('Bourgoyne et al. 1986 (Drilling Engineering)', bourgoyne.results);

// 3. API 5C3 & Rig Power Suite (7 tests)
const api5c3 = runApi5c3GoldenTests();
reportSuite('API Bulletin 5C3 & Teale 1962 (Casing Integrity & MSE)', api5c3.results);

// 4. Arnold & Stewart Suite (10 tests)
const arnoldStewart = runArnoldStewartGoldenTests();
reportSuite('Arnold & Stewart 2008 (Surface Facilities)', arnoldStewart);

// 5. Carter Ch. 3 Well Control (15 tests)
const carterWellControl = runCarterWellControlGoldenTests();
reportSuite('Carter Ch. 3 (Well Control & Kick Sheets)', carterWellControl);

// 6. Carter Ch. 4 Drilling Fluids & Retort (12 tests)
const carterFluids = runCarterFluidsGoldenTests();
reportSuite('Carter Ch. 4 (Drilling Fluids & Retort Analysis)', carterFluids);

// 7. Carter Ch. 5 Cementing (3 tests)
const carterCements = runCarterCementsGoldenTests();
reportSuite('Carter Ch. 5 (Cement Slurries & Plug Bumping)', carterCements);

// 8. Carter Ch. 6 Drilling Hydraulics (7 tests)
const carterHydraulics = runCarterHydraulicsGoldenTests();
reportSuite('Carter Ch. 6 (Drilling Hydraulics & ECD)', carterHydraulics);

// 9. Carter Ch. 2 Rig Operations (7 tests)
const carterRigOps = runCarterRigOpsGoldenTests();
reportSuite('Carter Ch. 2 (Rig Capacity, Trip Time & Bit Wear)', carterRigOps);

// 10. Carter Ch. 2.6 Stuck Pipe & Fishing (6 tests)
const carterStuckPipe = runCarterStuckPipeGoldenTests();
reportSuite('Carter Ch. 2.6 (Stuck Pipe & Fishing Economics)', carterStuckPipe);

// 11. Carter Phase 7 & 8 Formation Pressure & Directional (10 tests)
const carterPhase7 = runCarterPhase7GoldenTests();
reportSuite('Carter Phase 7 (Formation Pressure & LOT)', carterPhase7);

const carterPhase8 = runCarterPhase8GoldenTests();
reportSuite('Carter Phase 8 (Directional Surveying & DLS)', carterPhase8);

console.log('\n======================================================================');
console.log(`TOTAL BENCHMARK SCORE: ${grandTotalPassed} / ${grandTotalTests} PASSED (${Math.round((grandTotalPassed / grandTotalTests) * 100)}%)`);
console.log('======================================================================');

if (hasFailure) {
  console.error('\nFAIL: One or more golden benchmarks failed.');
  process.exit(1);
} else {
  console.log(`\nSUCCESS: All ${grandTotalTests} physical engineering benchmarks across all 11 suites are green.`);
  process.exit(0);
}
