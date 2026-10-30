/**
 * PetroLúmen Master Golden Benchmarks Test Runner
 * Executes all 64 verified benchmarks across Cormack, Bourgoyne, API 5C3, Arnold & Stewart, and Carter et al.
 */

import { runCormackGoldenTests } from './lib/drilling/__tests__/cormackGoldenTests';
import { runBourgoyneGoldenTests } from './lib/drilling/__tests__/bourgoyneGoldenTests';
import { runApi5c3GoldenTests } from './lib/drilling/__tests__/api5c3GoldenTests';
import { runArnoldStewartGoldenTests } from './lib/facilities/__tests__/arnoldStewartGoldenTests';
import { runCarterCementsGoldenTests } from './lib/drilling/__tests__/carterCementsGoldenTests';
import { runCarterFluidsGoldenTests } from './lib/drilling/__tests__/carterFluidsGoldenTests';
import { runCarterHydraulicsGoldenTests } from './lib/drilling/__tests__/carterHydraulicsGoldenTests';
import { runCarterPhase7GoldenTests } from './lib/drilling/__tests__/carterPhase7GoldenTests';
import { runCarterPhase8GoldenTests } from './lib/drilling/__tests__/carterPhase8GoldenTests';
import { runCarterRigOpsGoldenTests } from './lib/drilling/__tests__/carterRigOpsGoldenTests';
import { runCarterStuckPipeGoldenTests } from './lib/drilling/__tests__/carterStuckPipeGoldenTests';
import { runCarterWellControlGoldenTests } from './lib/drilling/__tests__/carterWellControlGoldenTests';

console.log('===============================================================');
console.log('PetroLúmen Verified Petroleum Engineering Benchmark Suite');
console.log('===============================================================\n');

let hasFailure = false;
let totalPassed = 0;
let totalCount = 0;

// 1. Cormack Suite (7 tests)
const cormack = runCormackGoldenTests();
console.log(`[Cormack 2017] ${cormack.passedTests}/${cormack.totalTests} passed`);
for (const test of cormack.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}
totalPassed += cormack.passedTests;
totalCount += cormack.totalTests;

// 2. Bourgoyne Suite (8 tests)
const bourgoyne = runBourgoyneGoldenTests();
console.log(`\n[Bourgoyne et al. 1986] ${bourgoyne.passedTests}/${bourgoyne.totalTests} passed`);
for (const test of bourgoyne.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}
totalPassed += bourgoyne.passedTests;
totalCount += bourgoyne.totalTests;

// 3. API 5C3 & Rig Power Suite (7 tests)
const api5c3 = runApi5c3GoldenTests();
console.log(`\n[API Bulletin 5C3 & Teale 1962] ${api5c3.passedTests}/${api5c3.totalTests} passed`);
for (const test of api5c3.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}
totalPassed += api5c3.passedTests;
totalCount += api5c3.totalTests;

// 4. Arnold & Stewart Suite (10 tests)
const arnoldStewart = runArnoldStewartGoldenTests();
const asPassed = arnoldStewart.filter((t) => t.passed).length;
console.log(`\n[Arnold & Stewart 2007] ${asPassed}/${arnoldStewart.length} passed`);
for (const test of arnoldStewart) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.description}`);
  if (!test.passed) hasFailure = true;
}
totalPassed += asPassed;
totalCount += arnoldStewart.length;

// Helper to log Carter suites
function logCarterSuite(title: string, results: { id: string; description: string; passed: boolean }[]) {
  const passed = results.filter((t) => t.passed).length;
  console.log(`\n[${title}] ${passed}/${results.length} passed`);
  for (const test of results) {
    const symbol = test.passed ? '✓' : '✗';
    console.log(`  ${symbol} ${test.id}: ${test.description}`);
    if (!test.passed) hasFailure = true;
  }
  totalPassed += passed;
  totalCount += results.length;
}

// 5. Carter et al. Suites (32 tests across 8 categories)
logCarterSuite('Carter 2023 - Cementing', runCarterCementsGoldenTests());
logCarterSuite('Carter 2023 - Drilling Fluids', runCarterFluidsGoldenTests());
logCarterSuite('Carter 2023 - Hydraulics', runCarterHydraulicsGoldenTests());
logCarterSuite('Carter 2023 - Phase 7 Casing', runCarterPhase7GoldenTests());
logCarterSuite('Carter 2023 - Phase 8 Directional', runCarterPhase8GoldenTests());
logCarterSuite('Carter 2023 - Rig Operations', runCarterRigOpsGoldenTests());
logCarterSuite('Carter 2023 - Stuck Pipe', runCarterStuckPipeGoldenTests());
logCarterSuite('Carter 2023 - Well Control', runCarterWellControlGoldenTests());

console.log('\n===============================================================');
console.log(`TOTAL BENCHMARK SCORE: ${totalPassed} / ${totalCount} PASSED (${Math.round((totalPassed / totalCount) * 100)}%)`);
console.log('===============================================================');

if (hasFailure) {
  console.error('\nFAIL: One or more golden benchmarks failed.');
  process.exit(1);
} else {
  console.log(`\nSUCCESS: All ${totalCount} physical engineering benchmarks are green.`);
  process.exit(0);
}
