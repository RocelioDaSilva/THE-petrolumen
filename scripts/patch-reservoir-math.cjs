const fs = require('fs');
let src = fs.readFileSync('src/lib/reservoirMath.ts', 'utf8');

// Find and replace the start of calculateZFactor to add guards before Ppr clamping
const oldLines = [
  'export function calculateZFactor(pressure: number, tempF: number, gammaG: number): number {\r\n',
  '  const { Ppc, Tpc } = getPseudoCriticalProps(gammaG);\r\n',
  '  const tempR = tempF + 459.67;\r\n',
  '  const Ppr = Math.max(0.05, pressure / Ppc);\r\n',
  '  const Tpr = Math.max(1.05, tempR / Tpc);',
].join('');

const newLines = [
  'export function calculateZFactor(pressure: number, tempF: number, gammaG: number): number {\r\n',
  '  // Fail loudly on unphysical parameters (AGENTS.md requirement).\r\n',
  '  // Silent clamping would produce misleading results; throw instead.\r\n',
  '  if (!Number.isFinite(pressure) || pressure <= 0) {\r\n',
  '    throw new RangeError(\r\n',
  '      `calculateZFactor: pressure must be a positive finite value (psia). Got: ${pressure}`\r\n',
  '    );\r\n',
  '  }\r\n',
  '  if (!Number.isFinite(tempF) || tempF <= -459.67) {\r\n',
  '    throw new RangeError(\r\n',
  '      `calculateZFactor: temperature must be above absolute zero (-459.67 degF). Got: ${tempF}`\r\n',
  '    );\r\n',
  '  }\r\n',
  '  if (!Number.isFinite(gammaG) || gammaG <= 0) {\r\n',
  '    throw new RangeError(\r\n',
  '      `calculateZFactor: gas specific gravity must be positive. Got: ${gammaG}`\r\n',
  '    );\r\n',
  '  }\r\n',
  '\r\n',
  '  const { Ppc, Tpc } = getPseudoCriticalProps(gammaG);\r\n',
  '  const tempR = tempF + 459.67;\r\n',
  '  const Ppr = pressure / Ppc;\r\n',
  '  const Tpr = Math.max(1.05, tempR / Tpc);',
].join('');

if (!src.includes(oldLines)) {
  console.error('TARGET NOT FOUND');
  // Show what we got around line 41
  const idx = src.indexOf('export function calculateZFactor');
  console.log('Actual content at function start:');
  console.log(JSON.stringify(src.substring(idx, idx + 250)));
  process.exit(1);
}

src = src.replace(oldLines, newLines);
fs.writeFileSync('src/lib/reservoirMath.ts', src);
console.log('DONE - guards added');
