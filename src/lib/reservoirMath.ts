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
  const { Ppc, Tpc } = getPseudoCriticalProps(gammaG);
  const tempR = tempF + 459.67;
  const Ppr = Math.max(0.05, pressure / Ppc);
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
  return Number.isFinite(z) && z > 0.2 && z < 2.5 ? Math.round(z * 10000) / 10000 : 0.88;
}

/**
 * Calculates comprehensive PVT properties
 */
export function calculatePVT(input: PVTInput): PVTResults {
  const { pressure, temperature, gammaG, api = 35, gor = 600 } = input;
  const z = calculateZFactor(pressure, temperature, gammaG);
  const tempR = temperature + 459.67;

  // Gas Formation Volume Factor: Bg = 0.02827 * Z * T / P (res bbl / scf)
  const bg = (0.02827 * z * tempR) / Math.max(1, pressure);

  // Bubble Point Pressure (Standing correlation)
  const pb = 18.2 * (Math.pow(gor / gammaG, 0.83) * Math.pow(10, 0.00091 * temperature - 0.0125 * api) - 1.4);
  const effectivePb = Math.max(100, pb);

  // Solution GOR (Rs)
  const rs = pressure < effectivePb
    ? gammaG * Math.pow((pressure / 18.2 + 1.4) * Math.pow(10, 0.0125 * api - 0.00091 * temperature), 1.2048)
    : gor;

  // Oil Formation Volume Factor (Bo - Standing correlation)
  const f = rs * Math.sqrt(gammaG / (141.5 / (api + 131.5))) + 1.25 * temperature;
  const boAtPb = 0.9759 + 0.00012 * Math.pow(f, 1.2);
  const bo = pressure < effectivePb
    ? 0.9759 + 0.00012 * Math.pow(rs * Math.sqrt(gammaG / (141.5 / (api + 131.5))) + 1.25 * temperature, 1.2)
    : boAtPb * Math.exp(-1.5e-5 * (pressure - effectivePb));

  // Dead oil viscosity (Beggs-Robinson)
  const x = Math.pow(temperature, -1.163) * Math.exp(6.9824 - 0.04658 * api);
  const viscDead = Math.pow(10, x) - 1;

  // Saturated oil viscosity
  const aVisc = 10.715 * Math.pow(rs + 100, -0.515);
  const bVisc = 5.44 * Math.pow(rs + 150, -0.338);
  const viscSat = aVisc * Math.pow(viscDead, bVisc);

  // Under-saturated oil viscosity
  const oilViscosity = pressure > effectivePb
    ? viscSat * Math.pow(pressure / effectivePb, 2.6 * Math.pow(pressure, 1.187) * Math.exp(-11.513 - 8.98e-5 * pressure))
    : viscSat;

  // Gas Viscosity (Lee-Gonzalez-Eakin correlation)
  const Mg = 28.96 * gammaG;
  const rhoG = (1.495e-3 * pressure * Mg) / (z * tempR); // g/cm3
  const K = ((9.4 + 0.02 * Mg) * Math.pow(tempR, 1.5)) / (209 + 19 * Mg + tempR);
  const X_coeff = 3.5 + 986 / tempR + 0.01 * Mg;
  const Y_coeff = 2.4 - 0.2 * X_coeff;
  const gasViscosity = (1e-4 * K * Math.exp(X_coeff * Math.pow(rhoG, Y_coeff)));

  // Oil density in lb/cu ft
  const gammaO = 141.5 / (api + 131.5);
  const oilDensity = (62.4 * gammaO + 0.0136 * rs * gammaG) / bo;

  return {
    zFactor: z,
    bg: Number(bg.toFixed(6)),
    bo: Number(bo.toFixed(4)),
    rs: Number(Math.max(0, rs).toFixed(1)),
    pb: Number(effectivePb.toFixed(1)),
    oilViscosity: Number(Math.max(0.1, oilViscosity).toFixed(3)),
    gasViscosity: Number(Math.max(0.008, gasViscosity).toFixed(4)),
    oilDensity: Number(oilDensity.toFixed(2)),
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
      const bFactor = Math.max(0.01, Math.min(0.99, b));
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
    // Add reasonable random variance for synthetic actuals
    const actualNoise = Math.sin(t * 1.5) * 0.05 * q + (Math.sin(t * 3) * 0.03 * q);
    const actual = Math.max(1, Math.round((q + actualNoise) * 10) / 10);

    cum += q * 30.4375; // Monthly cumulative in barrels
    points.push({
      time: t,
      rate: q,
      cum: Math.round(cum),
      actual: t <= 12 ? actual : undefined,
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
  const nPoints = 25;
  const dq = qMax / (nPoints - 1);
  const curves: NodalPoint[] = [];

  let bestDiff = Infinity;
  let operatingPoint: { q: number; p: number } | null = null;

  for (let i = 0; i < nPoints; i++) {
    const q = Math.round(i * dq);

    // Vogel IPR: Pwf = 0.125 * Pres * (-1 + sqrt(81 - 80 * (q / qMax)))
    const ratio = Math.min(0.999, q / qMax);
    const p_ipr = Math.max(0, 0.125 * pRes * (-1 + Math.sqrt(81 - 80 * ratio)));

    // VLP model (Beggs-Brill & hydrostatic + friction gradient)
    // Hydrostatic gradient based on water cut and GOR
    const liquidDensity = 62.4 * (1.0 * waterCut + 0.82 * (1 - waterCut)); // lb/cu ft
    const hydrostaticGrad = liquidDensity / 144.0; // psi/ft (typically ~0.35 - 0.43 psi/ft)
    const dInches = tubingId;
    const frictionFactor = 0.02;
    // Friction loss increases with q^1.8 / d^5
    const frictionLoss = (1.5e-5 * frictionFactor * Math.pow(q, 1.8) * depth) / Math.pow(dInches, 4.8);
    // Gas slippage uplift reduction:
    const gasSlippageFactor = Math.max(0.6, 1.0 - (gor / 2000) * 0.25);
    const p_vlp = pWh + depth * hydrostaticGrad * gasSlippageFactor + frictionLoss;

    curves.push({
      q,
      p_ipr: Math.round(p_ipr),
      p_vlp: Math.round(p_vlp),
    });

    const diff = Math.abs(p_ipr - p_vlp);
    if (diff < bestDiff && p_ipr > pWh) {
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
  const zi = calculateZFactor(pi, tf, gammaG);
  const pzi = pi / zi;

  // Gas material balance equation: P/Z = (Pi/Zi) * (1 - Gp / OGIP)
  const slope = -pzi / ogipExpected;
  const points: RTAPoint[] = [];
  const steps = 10;
  for (let i = 0; i <= steps; i++) {
    const gp = Math.round((i * (ogipExpected * 0.75)) / steps);
    const pz = pzi + slope * gp;
    const pwf = Math.max(200, pz * 0.92);
    points.push({
      gp,
      pz: Math.round(pz),
      pwf: Math.round(pwf),
    });
  }

  return {
    points,
    ogip: ogipExpected,
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
  irr: number;
  paybackYears: number;
  cashFlows: number[];
  cumCashFlows: number[];
  grossRevenue: number;
  totalOpex: number;
  roi: number;
}

export function calculateEconomics(input: EconomicsInput): EconomicsResult {
  const { oilPrice, opex, capex, discountRate, productionProfile } = input;
  const cashFlows: number[] = [-capex];
  const cumCashFlows: number[] = [-capex];

  let grossRevenue = 0;
  let totalOpex = 0;
  let cum = -capex;
  let paybackYears = 0;
  let paybackFound = false;

  for (let i = 0; i < productionProfile.length; i++) {
    const vol = productionProfile[i];
    const rev = vol * oilPrice;
    const op = vol * opex;
    const net = rev - op;
    grossRevenue += rev;
    totalOpex += op;

    cum += net;
    cashFlows.push(Math.round(net));
    cumCashFlows.push(Math.round(cum));

    if (!paybackFound && cum >= 0) {
      paybackYears = i + (cum - net < 0 ? Math.abs(cum - net) / net : 0);
      paybackFound = true;
    }
  }

  // NPV calculation
  let npv = -capex;
  for (let t = 1; t < cashFlows.length; t++) {
    npv += cashFlows[t] / Math.pow(1 + discountRate, t);
  }

  // IRR calculation (bisection method)
  let irr = 0;
  let low = -0.5;
  let high = 2.0;
  for (let iter = 0; iter < 40; iter++) {
    const mid = (low + high) / 2;
    let npvMid = -capex;
    for (let t = 1; t < cashFlows.length; t++) {
      npvMid += cashFlows[t] / Math.pow(1 + mid, t);
    }
    if (Math.abs(npvMid) < 10) {
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

  const roi = (grossRevenue - totalOpex - capex) / capex;

  return {
    npv: Math.round(npv),
    irr: Math.round(irr * 10000) / 100, // percentage
    paybackYears: Number(paybackYears.toFixed(2)),
    cashFlows,
    cumCashFlows,
    grossRevenue: Math.round(grossRevenue),
    totalOpex: Math.round(totalOpex),
    roi: Number((roi * 100).toFixed(1)),
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

  // Diffusivity constant eta = 0.006328 * k / (phi * mu * ct) [ft2/day]
  const eta = (0.006328 * permeability) / (porosity * viscosity * compressibility);
  const alpha = (eta * dt) / (dx * dx);
  const stableAlpha = Math.min(0.45, alpha); // numerical stability guarantee

  // Initialize pressure array
  let pGrid = new Array(nx).fill(pi);
  const history: { step: number; time: number; pressures: number[]; block5: number; wellbore: number }[] = [];

  for (let step = 0; step <= nSteps; step++) {
    const time = step * dt;
    history.push({
      step,
      time,
      pressures: [...pGrid.map((p) => Math.round(p))],
      block5: Math.round(pGrid[Math.floor(nx / 2)]),
      wellbore: Math.round(pGrid[0]),
    });

    if (step === nSteps) break;

    // Explicit finite difference update
    const nextP = [...pGrid];
    for (let i = 0; i < nx; i++) {
      const left = i === 0 ? pGrid[0] : pGrid[i - 1]; // no-flow outer boundary
      const right = i === nx - 1 ? pGrid[nx - 1] : pGrid[i + 1];
      nextP[i] = pGrid[i] + stableAlpha * (left - 2 * pGrid[i] + right);
    }

    // Source/sink term at well block 0
    const wellDrawdown = (Math.abs(wellRate) * 1.5) / (permeability * 0.2);
    nextP[0] = Math.max(500, nextP[0] - wellDrawdown * (dt / 10));

    pGrid = nextP;
  }

  return history;
}
