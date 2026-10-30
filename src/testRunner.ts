/**
 * PetroLúmen Master Golden Benchmarks Test Runner
 * Executes all 32 verified benchmarks across Cormack, Bourgoyne, API 5C3, and Arnold & Stewart.
 */

import { runCormackGoldenTests } from './lib/drilling/__tests__/cormackGoldenTests';
import { runBourgoyneGoldenTests } from './lib/drilling/__tests__/bourgoyneGoldenTests';
import { runApi5c3GoldenTests } from './lib/drilling/__tests__/api5c3GoldenTests';
import { runArnoldStewartGoldenTests } from './lib/facilities/__tests__/arnoldStewartGoldenTests';

console.log('===============================================================');
console.log('PetroLúmen Verified Petroleum Engineering Benchmark Suite');
console.log('===============================================================\n');

let hasFailure = false;

// 1. Cormack Suite (7 tests)
const cormack = runCormackGoldenTests();
console.log(`[Cormack 2017] ${cormack.passedTests}/${cormack.totalTests} passed`);
for (const test of cormack.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}

// 2. Bourgoyne Suite (8 tests)
const bourgoyne = runBourgoyneGoldenTests();
console.log(`\n[Bourgoyne et al. 1986] ${bourgoyne.passedTests}/${bourgoyne.totalTests} passed`);
for (const test of bourgoyne.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}

// 3. API 5C3 & Rig Power Suite (7 tests)
const api5c3 = runApi5c3GoldenTests();
console.log(`\n[API Bulletin 5C3 & Teale 1962] ${api5c3.passedTests}/${api5c3.totalTests} passed`);
for (const test of api5c3.results) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.name}`);
  if (!test.passed) hasFailure = true;
}

// 4. Arnold & Stewart Suite (10 tests)
const arnoldStewart = runArnoldStewartGoldenTests();
const asPassed = arnoldStewart.filter((t) => t.passed).length;
console.log(`\n[Arnold & Stewart 2007] ${asPassed}/${arnoldStewart.length} passed`);
for (const test of arnoldStewart) {
  const symbol = test.passed ? '✓' : '✗';
  console.log(`  ${symbol} ${test.id}: ${test.description}`);
  if (!test.passed) hasFailure = true;
}

const totalCount = cormack.totalTests + bourgoyne.totalTests + api5c3.totalTests + arnoldStewart.length;
const totalPassed = cormack.passedTests + bourgoyne.passedTests + api5c3.passedTests + asPassed;

console.log('\n===============================================================');
console.log(`TOTAL BENCHMARK SCORE: ${totalPassed} / ${totalCount} PASSED (${Math.round((totalPassed / totalCount) * 100)}%)`);
console.log('===============================================================');

if (hasFailure) {
  console.error('\nFAIL: One or more golden benchmarks failed.');
  process.exit(1);
} else {
  console.log('\nSUCCESS: All 32 physical engineering benchmarks are green.');
  process.exit(0);
}
