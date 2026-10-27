/**
 * PVT Input Sanitization & Validation Engine
 * Enforces strict scientific bounds, prevents division-by-zero,
 * and ensures unit consistency.
 */

export type PVTUnitSystem = 'field' | 'metric';

export interface RawPVTInput {
  pressure?: unknown;
  temperature?: unknown;
  volume?: unknown;
  gor?: unknown;
  apiGravity?: unknown;
  gasGravity?: unknown;
  unitSystem?: unknown;
}

export interface ValidatedPVTInput {
  pressure: number;      // psia
  temperature: number;   // °F
  volume?: number;       // bbl
  gor: number;           // scf/STB
  apiGravity: number;    // °API
  gasGravity: number;    // air = 1.0
  unitSystem: PVTUnitSystem;
}

export type SanitizedPVTResult =
  | { ok: true; value: ValidatedPVTInput }
  | { ok: false; errors: string[] };

/**
 * Validates that an input is a genuine finite number (rejects "1e", "1,000", null, NaN, Infinity)
 */
function isStrictFiniteNumber(val: unknown): val is number {
  if (typeof val === 'number') {
    return Number.isFinite(val);
  }
  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (trimmed === '' || trimmed.includes(',') || /[^\d.-]/.test(trimmed)) {
      return false;
    }
    const parsed = Number(trimmed);
    return Number.isFinite(parsed);
  }
  return false;
}

/**
 * Robust sanitizer for PVT inputs
 */
export function sanitizePVT(raw: unknown): SanitizedPVTResult {
  const errors: string[] = [];

  if (!raw || typeof raw !== 'object') {
    return { ok: false, errors: ['Entrada PVT inválida ou ausente.'] };
  }

  const input = raw as RawPVTInput;

  // 1. Unit System
  let unitSystem: PVTUnitSystem = 'field';
  if (input.unitSystem === 'metric' || input.unitSystem === 'field') {
    unitSystem = input.unitSystem;
  } else if (input.unitSystem !== undefined) {
    errors.push(`Sistema de unidades inválido: '${input.unitSystem}'. Use 'field' ou 'metric'.`);
  }

  // 2. Pressure check (fail loudly on <= 0, no silent clamp)
  if (!isStrictFiniteNumber(input.pressure)) {
    errors.push('Pressão deve ser um valor numérico válido.');
  } else {
    const p = Number(input.pressure);
    if (p <= 0) {
      errors.push(`Pressão deve ser estritamente positiva (> 0). Valor fornecido: ${p} ${unitSystem === 'metric' ? 'kPa' : 'psia'}.`);
    } else if (unitSystem === 'field' && (p < 14.7 || p > 25000)) {
      errors.push(`Pressão de reservatório fora da faixa operacional física (14.7 - 25,000 psia). Valor: ${p}`);
    }
  }

  // 3. Temperature check (below absolute zero check)
  if (!isStrictFiniteNumber(input.temperature)) {
    errors.push('Temperatura deve ser um valor numérico válido.');
  } else {
    const t = Number(input.temperature);
    if (unitSystem === 'field' && t <= -459.67) {
      errors.push(`Temperatura (${t}°F) está abaixo do zero absoluto (-459.67°F).`);
    } else if (unitSystem === 'metric' && t <= -273.15) {
      errors.push(`Temperatura (${t}°C) está abaixo do zero absoluto (-273.15°C).`);
    } else if (unitSystem === 'field' && (t < 32 || t > 500)) {
      errors.push(`Temperatura de reservatório fora da faixa operacional plausível (32 - 500°F). Valor: ${t}`);
    }
  }

  // 4. Gas Specific Gravity (air = 1.0)
  if (input.gasGravity !== undefined && !isStrictFiniteNumber(input.gasGravity)) {
    errors.push('Densidade relativa do gás (gammaG) deve ser um número.');
  } else if (input.gasGravity !== undefined) {
    const gg = Number(input.gasGravity);
    if (gg < 0.5 || gg > 2.0) {
      errors.push(`Densidade relativa do gás fora dos limites naturais de hidrocarbonetos (0.5 a 2.0). Valor: ${gg}`);
    }
  }

  // 5. Oil API Gravity
  if (input.apiGravity !== undefined && !isStrictFiniteNumber(input.apiGravity)) {
    errors.push('Grau API deve ser um número válido.');
  } else if (input.apiGravity !== undefined) {
    const api = Number(input.apiGravity);
    if (api <= 0 || api > 100) {
      errors.push(`Grau API do óleo deve estar entre 0° e 100° API. Valor: ${api}`);
    }
  }

  // 6. GOR (Solution Gas-Oil Ratio)
  if (input.gor !== undefined && !isStrictFiniteNumber(input.gor)) {
    errors.push('Razão Gás-Óleo (GOR) deve ser um número válido.');
  } else if (input.gor !== undefined) {
    const gor = Number(input.gor);
    if (gor < 0) {
      errors.push(`GOR não pode ser negativo. Valor: ${gor}`);
    }
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    value: {
      pressure: Number(input.pressure),
      temperature: Number(input.temperature),
      volume: input.volume !== undefined && isStrictFiniteNumber(input.volume) ? Number(input.volume) : undefined,
      gor: input.gor !== undefined ? Number(input.gor) : 600,
      apiGravity: input.apiGravity !== undefined ? Number(input.apiGravity) : 35,
      gasGravity: input.gasGravity !== undefined ? Number(input.gasGravity) : 0.72,
      unitSystem,
    },
  };
}
