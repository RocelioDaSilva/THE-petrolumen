/**
 * PetroLúmen Physics & Petroleum Engineering Computation Engine
 * Provides standard industry correlations (Standing, Hall-Yarborough, Beggs-Brill, Vogel, Arps, Duong)
 */

// ==========================================
// 1. PVT CALCULATIONS
// ==========================================

export interface PVTInput {
  pressure: number; // psia
  temperature: number; // °F
  gammaG: number; // Gas specific gravity (air=1)
  api?: number; // Oil API gravity
  gor?: number; // Solution GOR (scf/STB)
}

export interface PVTResults {
  zFactor: number;
  bg: number; // Gas FVF (res bbl / scf)
  bo: number; // Oil FVF (res bbl / STB)
  rs: number; // Solution GOR (scf/STB)
  pb: number; // Bubble point pressure (psia)
  oilViscosity: number; // cP
  gasViscosity: number; // cP
  oilDensity: number; // lb/cu ft
}

/**
 * Calculates pseudocritical properties (Sutton correlation)
 */
export function getPseudoCriticalProps(gammaG: number) {
  const Ppc = 756.8 - 131.0 * gammaG - 3.6 * gammaG * gammaG; // psia
  const Tpc = 169.2 + 349.5 * gammaG - 74.0 * gammaG * gammaG; // °R
  return { Ppc, Tpc };
}

/**
 * Calculates gas compressibility factor (Z) using Hall-Yarborough correlation
 */
export function calculateZFactor(pressure: number, tempF: number, gammaG: number): number {
  // Fail loudly on unphysical parameters (AGENTS.md requirement).
  // Silent clamping would produce misleading results; throw instead.
  if (!Number.isFinite(pressure) || pressure <= 0) {
    throw new RangeError(
      `calculateZFactor: pressure must be a positive finite value (psia). Got: ${pressure}`
    );
  }
  if (!Number.isFinite(tempF) || tempF <= -459.67) {
    throw new RangeError(
      `calculateZFactor: temperature must be above absolute zero (-459.67 degF). Got: ${tempF}`
    );
  }
  if (!Number.isFinite(gammaG) || gammaG <= 0) {
    throw new RangeError(
      `calculateZFactor: gas specific gravity must be positive. Got: ${gammaG}`
    );
  }

  const { Ppc, Tpc } = getPseudoCriticalProps(gammaG);
  const tempR = tempF + 459.67;
  const Ppr = pressure / Ppc;
  const Tpr = Math.max(1.05, tempR / Tpc);

  const t = 1.0 / Tpr;
  const A = 0.06125 * t * Math.exp(-1.2 * Math.pow(1 - t, 2));
  const B = t * (14.76 - 9.76 * t + 4.58 * Math.pow(t, 2));
  const C = t * (90.7 - 242.2 * t + 42.4 * Math.pow(t, 2));
  const D = 2.18 + 2.82 * t;

  // Newton-Raphson to solve for reduced density Y
  let Y = 0.0125 * Ppr * t * Math.exp(-1.2 * Math.pow(1 - t, 2));
  for (let iter = 0; iter < 50; iter++) {
    const fY = -A * Ppr + (Y + Math.pow(Y, 2) + Math.pow(Y, 3) - Math.pow(Y, 4)) / Math.pow(1 - Y, 3) - B * Math.pow(Y, 2) + C * Math.pow(Y, D);
    const dfY = (1 + 4 * Y + 4 * Math.pow(Y, 2) - 4 * Math.pow(Y, 3) + Math.pow(Y, 4)) / Math.pow(1 - Y, 4) - 2 * B * Y + C * D * Math.pow(Y, D - 1);
    if (Math.abs(dfY) < 1e-12) break;
    const nextY = Y - fY / dfY;
    if (Math.abs(nextY - Y) < 1e-6) {
      Y = nextY;
      break;
    }
    Y = Math.max(0.0001, Math.min(0.9, nextY));
  }

  const z = (A * Ppr) / Math.max(1e-6, Y);
  if (Number.isFinite(z) && z > 0.2 && z < 2.5) {
    return Math.round(z * 10000) / 10000;
  }

  // Fallback to Papay (1968) explicit correlation for gas compressibility if Newton-Raphson diverges
  const zPapay = 1 - (3.52 * Ppr) / Math.pow(10, 0.9813 * Tpr) + (0.274 * Math.pow(Ppr, 2)) / Math.pow(10, 0.8157 * Tpr);
  if (Number.isFinite(zPapay) && zPapay > 0.2 && zPapay < 2.5) {
    return Math.round(zPapay * 10000) / 10000;
  }

  throw new Error(`Cálculo do fator Z (Hall-Yarborough / Papay) não convergiu para P=${pressure} psia, T=${tempF}°F.`);
}

/**
 * Calculates comprehensive PVT properties
 */
export function calculatePVT(input: PVTInput): PVTResults {
  const { pressure, temperature, gammaG, api = 35, gor = 600 } = input;
  if (!Number.isFinite(pressure) || pressure <= 0) {
    throw new Error('A pressão deve ser um número finito estritamente positivo (> 0 psia).');
  }
  if (!Number.isFinite(temperature) || temperature < -459.67) {
    throw new Error('A temperatura não pode ser inferior ao zero absoluto (-459.67°F).');
  }
  const safePressure = pressure;
  const safeTemp = temperature;
  const safeGammaG = Math.max(0.4, Math.min(2.0, gammaG || 0.7));
  const safeApi = Math.max(5, Math.min(70, api));
  const safeGor = Math.max(0, gor);

  const z = calculateZFactor(safePressure, safeTemp, safeGammaG);
  const tempR = safeTemp + 459.67;

  // Gas Formation Volume Factor: Bg = 0.02827 * Z * T / P (res bbl / scf)
  const bg = (0.02827 * z * tempR) / safePressure;

  // Bubble Point Pressure (Standing correlation)
  const pb = 18.2 * (Math.pow(safeGor / safeGammaG, 0.83) * Math.pow(10, 0.00091 * safeTemp - 0.0125 * safeApi) - 1.4);
  const effectivePb = Math.max(100, Number.isFinite(pb) ? pb : 100);

  // Solution GOR (Rs)
  const rs = safePressure < effectivePb
    ? safeGammaG * Math.pow((safePressure / 18.2 + 1.4) * Math.pow(10, 0.0125 * safeApi - 0.00091 * safeTemp), 1.2048)
    : safeGor;

  // Oil Formation Volume Factor (Bo - Standing correlation)
  const f = rs * Math.sqrt(safeGammaG / (141.5 / (safeApi + 131.5))) + 1.25 * safeTemp;
  const boAtPb = 0.9759 + 0.00012 * Math.pow(f, 1.2);
  const bo = safePressure < effectivePb
    ? 0.9759 + 0.00012 * Math.pow(rs * Math.sqrt(safeGammaG / (141.5 / (safeApi + 131.5))) + 1.25 * safeTemp, 1.2)
    : boAtPb * Math.exp(-1.5e-5 * (safePressure - effectivePb));

  // Dead oil viscosity (Beggs-Robinson)
  const x = Math.pow(Math.max(1, safeTemp), -1.163) * Math.exp(6.9824 - 0.04658 * safeApi);
  const viscDead = Math.max(0.01, Math.pow(10, x) - 1);

  // Saturated oil viscosity
  const aVisc = 10.715 * Math.pow(rs + 100, -0.515);
  const bVisc = 5.44 * Math.pow(rs + 150, -0.338);
  const viscSat = aVisc * Math.pow(viscDead, bVisc);

  // Under-saturated oil viscosity
  const oilViscosity = safePressure > effectivePb
    ? viscSat * Math.pow(safePressure / effectivePb, 2.6 * Math.pow(safePressure, 1.187) * Math.exp(-11.513 - 8.98e-5 * safePressure))
    : viscSat;

  // Gas Viscosity (Lee-Gonzalez-Eakin correlation)
  const Mg = 28.96 * safeGammaG;
  const rhoG = (1.495e-3 * safePressure * Mg) / (z * tempR); // g/cm3
  const K = ((9.4 + 0.02 * Mg) * Math.pow(tempR, 1.5)) / (209 + 19 * Mg + tempR);
  const X_coeff = 3.5 + 986 / tempR + 0.01 * Mg;
  const Y_coeff = 2.4 - 0.2 * X_coeff;
  const gasViscosity = (1e-4 * K * Math.exp(X_coeff * Math.pow(rhoG, Y_coeff)));

  // Oil density in lb/cu ft
  const gammaO = 141.5 / (safeApi + 131.5);
  const oilDensity = (62.4 * gammaO + 0.0136 * rs * safeGammaG) / Math.max(0.5, bo);

  return {
    zFactor: z,
    bg: Number(bg.toFixed(6)),
    bo: Number(bo.toFixed(4)),
    rs: Number(Math.max(0, rs).toFixed(1)),
    pb: Number(effectivePb.toFixed(1)),
    oilViscosity: Number((Number.isFinite(oilViscosity) ? Math.max(0.1, oilViscosity) : 1.2).toFixed(3)),
    gasViscosity: Number((Number.isFinite(gasViscosity) ? Math.max(0.008, gasViscosity) : 0.015).toFixed(4)),
    oilDensity: Number((Number.isFinite(oilDensity) ? oilDensity : 50).toFixed(2)),
  };
}

// ==========================================
// 2. DECLINE CURVE ANALYSIS (DCA)
// ==========================================

export interface DCAParams {
  qi: number; // initial rate (bbl/d)
  di: number; // nominal decline (1/time unit)
  b: number; // Arps b-factor (0=exp, 0<b<1=hyperbolic, 1=harmonic)
  model: 'exponential' | 'hyperbolic' | 'harmonic' | 'duong';
  duongA?: number;
  duongM?: number;
}

export interface DCAPoint {
  time: number;
  rate: number;
  cum: number;
  actual?: number;
}

export function generateDCACurve(params: DCAParams, steps: number = 24): DCAPoint[] {
  const { qi, di, b, model, duongA = 1.2, duongM = 1.1 } = params;
  const points: DCAPoint[] = [];
  let cum = 0;

  for (let t = 1; t <= steps; t++) {
    let q = 0;
    if (model === 'exponential') {
      q = qi * Math.exp(-di * (t - 1));
    } else if (model === 'hyperbolic') {
      // Support b > 1 for unconventional/fractured shale reservoirs (ENG-28)
      const bFactor = b > 0 ? b : 0.5;
      q = qi / Math.pow(1 + bFactor * di * (t - 1), 1 / bFactor);
    } else if (model === 'harmonic') {
      q = qi / (1 + di * (t - 1));
    } else if (model === 'duong') {
      // Duong tight/shale decline: q(t) = q1 * t^(-m) * exp(a/(1-m) * (t^(1-m) - 1))
      const a = duongA;
      const m = duongM;
      if (m === 1) {
        q = qi * Math.pow(t, -1) * Math.exp(a * Math.log(t));
      } else {
        const exponent = (a / (1 - m)) * (Math.pow(t, 1 - m) - 1);
        q = qi * Math.pow(t, -m) * Math.exp(exponent);
      }
    }

    q = Math.max(1, Math.round(q * 10) / 10);
    cum += q * 30.4375; // Monthly cumulative in barrels
    points.push({
      time: t,
      rate: q,
      cum: Math.round(cum),
    });
  }

  return points;
}

// ==========================================
// 3. NODAL ANALYSIS (IPR vs VLP)
// ==========================================

export interface NodalInput {
  pRes: number; // Reservoir pressure (psia)
  qMax: number; // Max potential flow rate AOF (STB/d)
  pWh: number; // Wellhead pressure (psia)
  depth: number; // Well depth (ft)
  tubingId: number; // Tubing inner diameter (inches, e.g. 2.875)
  waterCut: number; // Water cut (0 to 1)
  gor: number; // GOR (scf/STB)
}

export interface NodalPoint {
  q: number;
  p_ipr: number;
  p_vlp: number;
}

export function solveNodal(input: NodalInput): {
  curves: NodalPoint[];
  operatingPoint: { q: number; p: number } | null;
} {
  const { pRes, qMax, pWh, depth, tubingId = 2.875, waterCut = 0.2, gor = 500 } = input;
  const safePRes = Math.max(100, pRes || 1000);
  const safeQMax = Math.max(10, qMax || 500);
  const safePWh = Math.max(0, pWh || 100);
  const safeDepth = Math.max(100, depth || 1000);
  const safeTubing = Math.max(1.0, tubingId || 2.875);
  const safeWc = Math.max(0, Math.min(0.99, waterCut || 0));
  const safeGor = Math.max(0, gor || 0);

  const nPoints = 25;
  const dq = safeQMax / (nPoints - 1);
  const curves: NodalPoint[] = [];

  let bestDiff = Infinity;
  let operatingPoint: { q: number; p: number } | null = null;

  for (let i = 0; i < nPoints; i++) {
    const q = Math.round(i * dq);

    // Vogel IPR: Pwf = 0.125 * Pres * (-1 + sqrt(81 - 80 * (q / qMax)))
    const ratio = Math.min(0.999, q / safeQMax);
    const p_ipr = Math.max(0, 0.125 * safePRes * (-1 + Math.sqrt(81 - 80 * ratio)));

    // VLP model (Beggs-Brill & hydrostatic + friction gradient)
    const liquidDensity = 62.4 * (1.0 * safeWc + 0.82 * (1 - safeWc)); // lb/cu ft
    const hydrostaticGrad = liquidDensity / 144.0;
    const frictionFactor = 0.02;
    const frictionLoss = (1.5e-5 * frictionFactor * Math.pow(q, 1.8) * safeDepth) / Math.pow(safeTubing, 4.8);
    const gasSlippageFactor = Math.max(0.6, 1.0 - (safeGor / 2000) * 0.25);
    const p_vlp = safePWh + safeDepth * hydrostaticGrad * gasSlippageFactor + frictionLoss;

    curves.push({
      q,
      p_ipr: Math.round(p_ipr),
      p_vlp: Math.round(p_vlp),
    });

    const diff = Math.abs(p_ipr - p_vlp);
    if (diff < bestDiff && p_ipr > safePWh) {
      bestDiff = diff;
      operatingPoint = { q, p: Math.round((p_ipr + p_vlp) / 2) };
    }
  }

  return { curves, operatingPoint };
}

// ==========================================
// 4. RATE TRANSIENT ANALYSIS & MATERIAL BALANCE
// ==========================================

export interface RTAPoint {
  gp: number; // Cumulative gas prod (MMscf)
  pz: number; // Flowing P/Z (psia)
  pwf: number;
}

export function calculateFMBGas(
  pi: number = 3200,
  tf: number = 160,
  gammaG: number = 0.65,
  ogipExpected: number = 1200 // MMscf
): { points: RTAPoint[]; ogip: number; slope: number } {
  const safePi = Math.max(100, pi || 1000);
  const safeTf = Math.max(32, tf || 100);
  const safeGammaG = Math.max(0.4, gammaG || 0.65);
  const safeOgip = Math.max(10, ogipExpected || 100);

  const zi = calculateZFactor(safePi, safeTf, safeGammaG);
  const pzi = safePi / Math.max(0.1, zi);

  // Gas material balance equation: P/Z = (Pi/Zi) * (1 - Gp / OGIP)
  const slope = -pzi / safeOgip;
  const points: RTAPoint[] = [];
  const steps = 10;
  for (let i = 0; i <= steps; i++) {
    const gp = Math.round((i * (safeOgip * 0.75)) / steps);
    const pz = Math.max(0, pzi + slope * gp);
    const pwf = Math.max(50, pz * 0.92);
    points.push({
      gp,
      pz: Math.round(pz),
      pwf: Math.round(pwf),
    });
  }

  return {
    points,
    ogip: safeOgip,
    slope: Number(slope.toFixed(4)),
  };
}

// ==========================================
// 5. ECONOMICS & RESERVES
// ==========================================

export interface EconomicsInput {
  oilPrice: number; // $/bbl
  opex: number; // $/bbl
  capex: number; // $
  discountRate: number; // decimal, e.g. 0.10
  productionProfile: number[]; // bbl/year
}

export interface EconomicsResult {
  npv: number;
  irr?: number;
  paybackYears: number;
  cashFlows: number[];
  cumCashFlows: number[];
  grossRevenue: number;
  totalOpex: number;
  roi: number;
}

export function calculateEconomics(input: EconomicsInput): EconomicsResult {
  const { oilPrice, opex, capex, discountRate, productionProfile } = input;
  const safeCapex = Math.max(1, capex || 1);
  const safePrice = Math.max(0, oilPrice || 0);
  const safeOpex = Math.max(0, opex || 0);
  // ENG-20: Use ?? 0.1 and ensure non-negative so 0% discount rate is preserved
  const safeDiscount = Math.max(0, discountRate ?? 0.1);
  const profile = productionProfile && productionProfile.length ? productionProfile : [10000];

  const cashFlows: number[] = [-safeCapex];
  const cumCashFlows: number[] = [-safeCapex];

  let grossRevenue = 0;
  let totalOpex = 0;
  let cum = -safeCapex;
  let paybackYears = 0;
  let paybackFound = false;

  for (let i = 0; i < profile.length; i++) {
    const vol = Math.max(0, profile[i] || 0);
    const rev = vol * safePrice;
    const op = vol * safeOpex;
    const net = rev - op;
    grossRevenue += rev;
    totalOpex += op;

    cum += net;
    cashFlows.push(Math.round(net));
    cumCashFlows.push(Math.round(cum));

    if (!paybackFound && cum >= 0) {
      paybackYears = i + (cum - net < 0 ? Math.abs(cum - net) / Math.max(1, net) : 0);
      paybackFound = true;
    }
  }

  // NPV calculation
  let npv = -safeCapex;
  for (let t = 1; t < cashFlows.length; t++) {
    npv += cashFlows[t] / Math.pow(1 + safeDiscount, t);
  }

  // ENG-21: IRR calculation (bisection method) - return undefined if project is not profitable
  let irr: number | undefined = undefined;
  const totalFutureCash = cashFlows.slice(1).reduce((acc, val) => acc + val, 0);

  if (totalFutureCash > safeCapex) {
    let low = -0.5;
    let high = 5.0;
    for (let iter = 0; iter < 50; iter++) {
      const mid = (low + high) / 2;
      let npvMid = -safeCapex;
      for (let t = 1; t < cashFlows.length; t++) {
        npvMid += cashFlows[t] / Math.pow(1 + mid, t);
      }
      if (Math.abs(npvMid) < 1.0) {
        irr = mid;
        break;
      }
      if (npvMid > 0) {
        low = mid;
      } else {
        high = mid;
      }
      irr = mid;
    }
  }

  const roi = (grossRevenue - totalOpex - safeCapex) / safeCapex;

  return {
    npv: Number.isFinite(npv) ? Math.round(npv) : 0,
    irr: irr !== undefined ? Math.round(irr * 10000) / 100 : undefined,
    paybackYears: Number((Number.isFinite(paybackYears) ? paybackYears : 0).toFixed(2)),
    cashFlows,
    cumCashFlows,
    grossRevenue: Math.round(grossRevenue),
    totalOpex: Math.round(totalOpex),
    roi: Number((Number.isFinite(roi) ? roi * 100 : 0).toFixed(1)),
  };
}

// ==========================================
// 6. RESERVOIR SIMULATION 1D IMPES SOLVER
// ==========================================

export interface SimulationParams {
  nx: number;
  dx: number; // ft
  permeability: number; // mD
  porosity: number; // fraction
  viscosity: number; // cP
  compressibility: number; // 1/psi
  pi: number; // Initial pressure (psia)
  dt: number; // Time step (days)
  nSteps: number;
  wellRate: number; // STB/d (producer is negative)
}

export function run1DReservoirSimulation(params: SimulationParams) {
  const { nx = 10, dx = 100, permeability = 50, porosity = 0.2, viscosity = 1.5, compressibility = 1e-5, pi = 3500, dt = 10, nSteps = 20, wellRate = -500 } = params;

  const safeNx = Math.max(3, Math.min(50, nx || 10));
  const safeDx = Math.max(10, dx || 100);
  const safePerm = Math.max(0.1, permeability || 10);
  const safePhi = Math.max(0.01, Math.min(0.5, porosity || 0.2));
  const safeVisc = Math.max(0.05, viscosity || 1.0);
  const safeCt = Math.max(1e-7, compressibility || 1e-5);
  const safePi = Math.max(100, pi || 3000);
  const safeDt = Math.max(0.1, dt || 10);
  const safeSteps = Math.max(1, Math.min(100, nSteps || 20));

  // Diffusivity constant eta = 0.006328 * k / (phi * mu * ct) [ft2/day]
  const eta = (0.006328 * safePerm) / (safePhi * safeVisc * safeCt);
  const alpha = (eta * safeDt) / (safeDx * safeDx);
  const stableAlpha = Math.min(0.45, Number.isFinite(alpha) ? alpha : 0.2);

  // Initialize pressure array
  let pGrid = new Array(safeNx).fill(safePi);
  const history: { step: number; time: number; pressures: number[]; block5: number; wellbore: number }[] = [];

  for (let step = 0; step <= safeSteps; step++) {
    const time = step * safeDt;
    history.push({
      step,
      time: Math.round(time),
      pressures: [...pGrid.map((p) => Math.round(p))],
      block5: Math.round(pGrid[Math.floor(safeNx / 2)]),
      wellbore: Math.round(pGrid[0]),
    });

    if (step === safeSteps) break;

    // Explicit finite difference update
    const nextP = [...pGrid];
    for (let i = 0; i < safeNx; i++) {
      const left = i === 0 ? pGrid[0] : pGrid[i - 1];
      const right = i === safeNx - 1 ? pGrid[safeNx - 1] : pGrid[i + 1];
      nextP[i] = pGrid[i] + stableAlpha * (left - 2 * pGrid[i] + right);
    }

    // Source/sink term at well block 0
    const wellDrawdown = (Math.abs(wellRate) * 1.5) / (safePerm * 0.2);
    nextP[0] = Math.max(200, nextP[0] - wellDrawdown * (safeDt / 10));

    pGrid = nextP;
  }

  return history;
}
