/**
 * Advanced Drilling Hydraulics Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 4.
 */

import { findRootBrent } from '../math/solvers';
import { PIPE_ROUGHNESS } from '../math/tables';

export type RheologyModel = 'newtonian' | 'bingham' | 'power-law';

export interface ComplexColumnSegment {
  name: string;
  topDepthFt: number;
  bottomDepthFt: number;
  mudWeightPpg: number;
}

/**
 * 4.1 Hydrostatic in Complex Multiphase / Multidensity Columns
 * Sourced: Bourgoyne Ch. 4, Eq. 4.7
 */
export function hydrostaticComplex(segments: ComplexColumnSegment[], surfacePressurePsi: number = 0): number {
  let hp = surfacePressurePsi;
  for (const seg of segments) {
    const deltaZ = Math.max(0, seg.bottomDepthFt - seg.topDepthFt);
    hp += 0.052 * seg.mudWeightPpg * deltaZ;
  }
  return Math.round(hp);
}

/**
 * Hydrostatic pressure of a static gas column
 * Sourced: Bourgoyne Ch. 4, Eq. 4.6: p = p0 * exp( (0.01875 * gamma_g * (D - D0)) / (z_avg * T_avg) )
 */
export function hydrostaticGasColumn(
  p0Psia: number,
  gasSpecificGravity: number,
  bottomDepthFt: number,
  topDepthFt: number = 0,
  zAvg: number = 0.85,
  tAvgRankine: number = 560 // 100 °F
): number {
  const deltaD = Math.max(0, bottomDepthFt - topDepthFt);
  const exponent = (0.01875 * gasSpecificGravity * deltaD) / (zAvg * tAvgRankine);
  const p = p0Psia * Math.exp(exponent);
  return Math.round(p);
}

/**
 * Equivalent mud density in lbm/gal
 * Sourced: Bourgoyne Ch. 4, Eq. 4.8: rho_e = p / (0.052 * D)
 */
export function equivalentDensity(pressurePsi: number, tvdFt: number): number {
  if (tvdFt <= 0) return 0;
  return Math.round((pressurePsi / (0.052 * tvdFt)) * 100) / 100;
}

/**
 * 4.2 Annular Equivalent Diameters
 * Sourced: Bourgoyne Ch. 4, Section 4.5
 */
export const AnnularEquivalentDiameter = {
  // Hydraulic radius method: d_hyd = d2 - d1
  hydraulicRadius: (holeIdIn: number, pipeOdIn: number): number => {
    return Math.max(0.1, holeIdIn - pipeOdIn);
  },
  // Lamb / Exact laminar method: d_lamb = sqrt(d2^2 + d1^2 - (d2^2 - d1^2)/ln(d2/d1))
  lamb: (holeIdIn: number, pipeOdIn: number): number => {
    if (holeIdIn <= pipeOdIn || pipeOdIn <= 0) return 0.1;
    const ratio = holeIdIn / pipeOdIn;
    const d2sq = Math.pow(holeIdIn, 2);
    const d1sq = Math.pow(pipeOdIn, 2);
    const val = d2sq + d1sq - (d2sq - d1sq) / Math.log(ratio);
    return Math.round(Math.sqrt(Math.max(0.01, val)) * 1000) / 1000;
  },
  // Slot flow approximation: d_slot = 0.816 * (d2 - d1)
  slot: (holeIdIn: number, pipeOdIn: number): number => {
    return Math.round(0.816 * Math.max(0.1, holeIdIn - pipeOdIn) * 1000) / 1000;
  },
  // Crittendon method: d_crit = sqrt(d2^2 - d1^2)
  crittendon: (holeIdIn: number, pipeOdIn: number): number => {
    return Math.round(Math.sqrt(Math.max(0.01, Math.pow(holeIdIn, 2) - Math.pow(pipeOdIn, 2))) * 1000) / 1000;
  },
};

/**
 * 4.3 Flow Regimes & Reynolds Numbers
 * Sourced: Bourgoyne Ch. 4, Eq. 4.40 - 4.59
 */
export function reynoldsNewtonian(rhoPpg: number, vFtS: number, dInches: number, muCp: number): number {
  if (muCp <= 0) return 999999;
  return Math.round((928 * rhoPpg * vFtS * dInches) / muCp);
}

export function reynoldsBingham(rhoPpg: number, vFtS: number, dInches: number, muPCp: number): number {
  if (muPCp <= 0) return 999999;
  return Math.round((928 * rhoPpg * vFtS * dInches) / muPCp);
}

export function hedstromNumber(rhoPpg: number, tauYLbf100ft2: number, dInches: number, muPCp: number): number {
  if (muPCp <= 0) return 0;
  const nHe = (37100 * rhoPpg * tauYLbf100ft2 * Math.pow(dInches, 2)) / Math.pow(muPCp, 2);
  return Math.round(nHe);
}

/**
 * Critical Reynolds Number for Bingham Plastic using Hedstrom correlation
 * Sourced: Bourgoyne Ch. 4, Fig. 4.25 / Eq. 4.46
 */
export function criticalReynoldsBingham(hedstrom: number): number {
  if (hedstrom <= 0) return 2100;
  // Approximation from Fig. 4.25: N_Re_c increases with N_He
  const nRec = 2100 + 1.2 * Math.pow(hedstrom, 0.45);
  return Math.round(Math.min(10000, nRec));
}

export function reynoldsPowerLaw(
  rhoPpg: number,
  vFtS: number,
  dInches: number,
  K: number,
  n: number
): number {
  if (K <= 0) return 999999;
  const denom = K * Math.pow(Math.max(0.01, (3 * n + 1) / (4 * n)), n);
  const num = 89100 * rhoPpg * Math.pow(vFtS, 2 - n) * Math.pow(dInches / 12, n);
  return Math.round(num / denom);
}

/**
 * 4.4 Fanning Friction Factor via Colebrook-White equation
 * Sourced: Bourgoyne Ch. 4, Eq. 4.47
 * 1 / sqrt(f) = -4.0 * log10( (epsilon / (3.7 * d)) + (1.255 / (N_Re * sqrt(f))) )
 */
export function fanningFrictionFactorColebrook(
  reynolds: number,
  pipeDiameterInches: number,
  roughnessInches: number = PIPE_ROUGHNESS.commercialSteelInches
): number {
  if (reynolds < 2100) {
    // Laminar Fanning friction factor: 16 / N_Re
    return Math.max(0.004, 16 / Math.max(1, reynolds));
  }

  const relRoughness = roughnessInches / pipeDiameterInches;

  // Solve for f using Brent's method
  const fRoot = findRootBrent(
    (f) => {
      if (f <= 0) return 999;
      const left = 1 / Math.sqrt(f);
      const right = -4.0 * Math.log10(relRoughness / 3.7 + 1.255 / (reynolds * Math.sqrt(f)));
      return left - right;
    },
    0.002,
    0.05,
    { tolerance: 1e-6 }
  );

  return Math.round(fRoot * 100000) / 100000;
}

/**
 * Dodge-Metzner Turbulent Friction Factor for Power-Law fluids
 * Sourced: Bourgoyne Ch. 4, Eq. 4.62
 */
export function fanningFrictionFactorPowerLaw(reynolds: number, n: number): number {
  if (reynolds < 2100) {
    return 16 / Math.max(1, reynolds);
  }
  // Blasius-like approximation for pseudoplastics: f = a / (N_Re)^b
  const a = (Math.log10(n) + 3.93) / 50;
  const b = (1.75 - Math.log10(n)) / 7;
  const f = a / Math.pow(reynolds, b);
  return Math.round(Math.max(0.003, f) * 100000) / 100000;
}

/**
 * 4.5 Pressure Loss Gradients (Laminar & Turbulent)
 * Sourced: Bourgoyne Ch. 4, Sections 4.4 & 4.5
 */
export interface PressureLossGradientResult {
  regime: 'Laminar' | 'Turbulent';
  reynolds: number;
  gradientPsiFt: number; // psi / ft
  totalPressureLossPsi: number;
}

/**
 * Flow in Drillpipe or Casing (Internal circular conduit)
 */
export function pipePressureLoss(
  flowGpm: number,
  pipeIdInches: number,
  pipeLengthFt: number,
  mudWeightPpg: number,
  model: RheologyModel = 'bingham',
  rheo: { muCp?: number; muPCp?: number; tauY?: number; K?: number; n?: number } = { muPCp: 20, tauY: 10 }
): PressureLossGradientResult {
  const d = Math.max(0.5, pipeIdInches);
  // Velocity in pipe: v = q / (2.448 * d^2) in ft/s
  const vFtS = flowGpm / (2.448 * Math.pow(d, 2));

  let grad = 0;
  let reynolds = 0;
  let isTurbulent = false;

  if (model === 'newtonian') {
    const mu = rheo.muCp || 20;
    reynolds = reynoldsNewtonian(mudWeightPpg, vFtS, d, mu);
    isTurbulent = reynolds >= 2100;
    if (!isTurbulent) {
      // Laminar Newtonian: dp/dl = mu * v / (1500 * d^2)
      grad = (mu * vFtS) / (1500 * Math.pow(d, 2));
    }
  } else if (model === 'bingham') {
    const muP = rheo.muPCp || 20;
    const tauY = rheo.tauY || 10;
    reynolds = reynoldsBingham(mudWeightPpg, vFtS, d, muP);
    const nHe = hedstromNumber(mudWeightPpg, tauY, d, muP);
    const nRec = criticalReynoldsBingham(nHe);
    isTurbulent = reynolds >= nRec;
    if (!isTurbulent) {
      // Laminar Bingham: dp/dl = (muP * v) / (1500 * d^2) + tauY / (225 * d)
      grad = (muP * vFtS) / (1500 * Math.pow(d, 2)) + tauY / (225 * d);
    }
  } else {
    // Power-law
    const K = rheo.K || 300;
    const n = rheo.n || 0.65;
    reynolds = reynoldsPowerLaw(mudWeightPpg, vFtS, d, K, n);
    isTurbulent = reynolds >= 2100;
    if (!isTurbulent) {
      // Laminar Power-Law: Bourgoyne Eq. 4.54
      const term1 = (K * Math.pow(vFtS, n)) / (144000 * Math.pow(d, 1 + n));
      const term2 = Math.pow((3 * n + 1) / (0.0416 * n), n);
      grad = term1 * term2;
    }
  }

  if (isTurbulent) {
    const f = fanningFrictionFactorColebrook(reynolds, d);
    // Turbulent: dp/dl = 2 * f * rho * v^2 / (25.8 * d) -> with Fanning: dp/dl = f * rho * v^2 / (25.8 * d)
    grad = (f * mudWeightPpg * Math.pow(vFtS, 2)) / (25.8 * d);
  }

  const totalP = grad * pipeLengthFt;
  return {
    regime: isTurbulent ? 'Turbulent' : 'Laminar',
    reynolds,
    gradientPsiFt: Math.round(grad * 10000) / 10000,
    totalPressureLossPsi: Math.round(totalP),
  };
}

/**
 * Flow in Annulus between Hole/Casing ID and Pipe OD
 */
export function annularPressureLoss(
  flowGpm: number,
  holeIdInches: number,
  pipeOdInches: number,
  lengthFt: number,
  mudWeightPpg: number,
  model: RheologyModel = 'bingham',
  rheo: { muCp?: number; muPCp?: number; tauY?: number; K?: number; n?: number } = { muPCp: 20, tauY: 10 }
): PressureLossGradientResult {
  const dHyd = AnnularEquivalentDiameter.hydraulicRadius(holeIdInches, pipeOdInches);
  // Annular velocity: v = q / (2.448 * (d2^2 - d1^2)) in ft/s
  const denomArea = Math.max(0.1, Math.pow(holeIdInches, 2) - Math.pow(pipeOdInches, 2));
  const vFtS = flowGpm / (2.448 * denomArea);

  let grad = 0;
  let reynolds = 0;
  let isTurbulent = false;

  if (model === 'bingham') {
    const muP = rheo.muPCp || 20;
    const tauY = rheo.tauY || 10;
    reynolds = reynoldsBingham(mudWeightPpg, vFtS, dHyd, muP);
    const nHe = hedstromNumber(mudWeightPpg, tauY, dHyd, muP);
    const nRec = criticalReynoldsBingham(nHe);
    isTurbulent = reynolds >= nRec;
    if (!isTurbulent) {
      // Laminar Bingham Annulus: dp/dl = (muP * v) / (1000 * dHyd^2) + tauY / (200 * dHyd)
      grad = (muP * vFtS) / (1000 * Math.pow(dHyd, 2)) + tauY / (200 * dHyd);
    }
  } else {
    // Default / Newtonian / Power-law
    const muP = rheo.muPCp || rheo.muCp || 20;
    reynolds = reynoldsNewtonian(mudWeightPpg, vFtS, dHyd, muP);
    isTurbulent = reynolds >= 2100;
    if (!isTurbulent) {
      grad = (muP * vFtS) / (1000 * Math.pow(dHyd, 2));
    }
  }

  if (isTurbulent) {
    const f = fanningFrictionFactorColebrook(reynolds, dHyd);
    grad = (f * mudWeightPpg * Math.pow(vFtS, 2)) / (21.1 * dHyd);
  }

  return {
    regime: isTurbulent ? 'Turbulent' : 'Laminar',
    reynolds,
    gradientPsiFt: Math.round(grad * 10000) / 10000,
    totalPressureLossPsi: Math.round(grad * lengthFt),
  };
}

/**
 * 4.6 Bit Hydraulics & Jet Nozzle Mechanics
 * Sourced: Bourgoyne Ch. 4, Eq. 4.31 - 4.37
 */
export interface BitHydraulicsResult {
  totalNozzleAreaSqIn: number;
  nozzleVelocityFtS: number;
  bitPressureDropPsi: number;
  hydraulicHorsepowerBit: number;
  hydraulicHorsepowerPerSqIn: number; // HSI
  jetImpactForceLbf: number;
}

export function calculateBitHydraulics(
  flowGpm: number,
  mudWeightPpg: number,
  nozzleSizes32nds: number[],
  bitDiameterInches: number = 8.5,
  dischargeCoeffCd: number = 0.95
): BitHydraulicsResult {
  // Total nozzle area At = sum( pi/4 * (d_i / 32)^2 )
  let totalArea = 0;
  for (const n of nozzleSizes32nds) {
    if (n > 0) {
      const dIn = n / 32;
      totalArea += (Math.PI / 4) * Math.pow(dIn, 2);
    }
  }
  const At = Math.max(0.01, totalArea);

  // Nozzle velocity: v_n = q / (3.117 * At) in ft/s (Bourgoyne Eq. 4.31)
  const vn = flowGpm / (3.117 * At);

  // Bit pressure drop: delta_pb = (rho * q^2) / (10858 * At^2 * Cd^2) (Bourgoyne Eq. 4.34)
  const deltaPb = (mudWeightPpg * Math.pow(flowGpm, 2)) / (10858 * Math.pow(At, 2) * Math.pow(dischargeCoeffCd, 2));

  // Hydraulic horsepower at bit: HHP_b = (delta_pb * q) / 1714
  const hhpBit = (deltaPb * flowGpm) / 1714;

  // HHP per square inch of hole area (HSI)
  const bitArea = (Math.PI / 4) * Math.pow(bitDiameterInches, 2);
  const hsi = hhpBit / bitArea;

  // Jet Impact Force: JIF = (rho * q * v_n) / 1930 in lbf (Bourgoyne Eq. 4.37)
  const jif = (mudWeightPpg * flowGpm * vn) / 1930;

  return {
    totalNozzleAreaSqIn: Math.round(At * 1000) / 1000,
    nozzleVelocityFtS: Math.round(vn),
    bitPressureDropPsi: Math.round(deltaPb),
    hydraulicHorsepowerBit: Math.round(hhpBit),
    hydraulicHorsepowerPerSqIn: Math.round(hsi * 100) / 100,
    jetImpactForceLbf: Math.round(jif),
  };
}

/**
 * Optimum Nozzle Sizing for Maximum Bit Hydraulic Horsepower or Maximum Jet Impact Force
 * Sourced: Bourgoyne Ch. 4, Section 4.7
 */
export function optimumNozzleSelection(
  surfacePumpPressurePsi: number,
  mudWeightPpg: number,
  flowGpm: number,
  criterion: 'max-bit-hhp' | 'max-impact-force',
  parasiticExponentM: number = 1.8,
  dischargeCoeffCd: number = 0.95
): { optimumBitDeltaPPsi: number; requiredNozzleAreaSqIn: number; suggestedNozzles32nds: number[] } {
  // At maximum bit horsepower: delta_pb = (m / (m + 1)) * P_pump
  // At maximum impact force: delta_pb = (m / (m + 2)) * P_pump
  let optimumBitDeltaP: number;
  if (criterion === 'max-bit-hhp') {
    optimumBitDeltaP = (parasiticExponentM / (parasiticExponentM + 1)) * surfacePumpPressurePsi;
  } else {
    optimumBitDeltaP = (parasiticExponentM / (parasiticExponentM + 2)) * surfacePumpPressurePsi;
  }

  // Required nozzle area At = sqrt( (rho * q^2) / (10858 * Cd^2 * delta_pb) )
  const areaSq = (mudWeightPpg * Math.pow(flowGpm, 2)) / (10858 * Math.pow(dischargeCoeffCd, 2) * optimumBitDeltaP);
  const reqArea = Math.sqrt(Math.max(0.001, areaSq));

  // Determine standard 3-nozzle combination matching reqArea
  // 3 equal nozzles: Area_each = At / 3 -> d_each = sqrt(4 * Area_each / pi) * 32
  const dEach32nds = Math.round(Math.sqrt((4 * (reqArea / 3)) / Math.PI) * 32);

  return {
    optimumBitDeltaPPsi: Math.round(optimumBitDeltaP),
    requiredNozzleAreaSqIn: Math.round(reqArea * 1000) / 1000,
    suggestedNozzles32nds: [dEach32nds, dEach32nds, dEach32nds],
  };
}

/**
 * 4.7 Gel Breaking Pressure to Resume Mud Circulation
 * Sourced: Bourgoyne Ch. 4, Eq. 4.77 - 4.78
 */
export function gelBreakPressure(
  gelStrengthLbf100ft2: number,
  pipeLengthFt: number,
  pipeIdInches: number,
  holeIdInches: number,
  pipeOdInches: number
): { pipeDeltaPPsi: number; annulusDeltaPPsi: number; totalPumpPressureToBreakGelPsi: number } {
  // Inside drillpipe: deltaP = (4 * tau_g * L) / (300 * d)
  const dpPipe = (4 * gelStrengthLbf100ft2 * pipeLengthFt) / (300 * pipeIdInches);
  // In annulus: deltaP = (4 * tau_g * L) / (300 * (d2 - d1))
  const dHyd = Math.max(0.1, holeIdInches - pipeOdInches);
  const dpAnnulus = (4 * gelStrengthLbf100ft2 * pipeLengthFt) / (300 * dHyd);

  return {
    pipeDeltaPPsi: Math.round(dpPipe),
    annulusDeltaPPsi: Math.round(dpAnnulus),
    totalPumpPressureToBreakGelPsi: Math.round(dpPipe + dpAnnulus),
  };
}

/**
 * 4.8 Surge & Swab Pressure (Bourgoyne Steady & Inertial Model)
 * Sourced: Bourgoyne Ch. 4, Section 4.10, Eq. 4.90 - 4.99
 */
export function calculateSurgeSwabPressure(
  pipeSpeedFtMin: number, // positive for tripping in (surge), negative for tripping out (swab)
  isClosedPipe: boolean,
  mudWeightPpg: number,
  plasticViscosityCp: number,
  yieldPointLbf100ft2: number,
  pipeOdInches: number,
  casingIdInches: number,
  sectionLengthFt: number,
  pipeAccFtS2: number = 0
): { viscousPressurePsi: number; inertialPressurePsi: number; totalSurgePressurePsi: number } {
  const vPipeFtS = pipeSpeedFtMin / 60;
  const d2 = casingIdInches;
  const d1 = pipeOdInches;
  const dHyd = d2 - d1;

  // Clinging constant Kc (ratio of mud dragged by moving pipe)
  // For laminar Bingham: Kc ≈ 0.45 for typical d1/d2 ~ 0.55
  const Kc = 0.45;

  let vEffFtS = 0;
  if (isClosedPipe) {
    // Closed pipe displaces fluid upward in annulus: v_eff = v_p * (d1^2 / (d2^2 - d1^2) + Kc)
    const areaRatio = Math.pow(d1, 2) / Math.max(0.1, Math.pow(d2, 2) - Math.pow(d1, 2));
    vEffFtS = Math.abs(vPipeFtS) * (areaRatio + Kc);
  } else {
    // Open pipe: only clinging effect drags mud
    vEffFtS = Math.abs(vPipeFtS) * Kc;
  }

  // Viscous pressure loss in annulus due to effective velocity
  const gradViscous = (plasticViscosityCp * vEffFtS) / (1000 * Math.pow(dHyd, 2)) + yieldPointLbf100ft2 / (200 * dHyd);
  const pViscous = gradViscous * sectionLengthFt;

  // Inertial surge during pipe acceleration (Bourgoyne Eq. 4.99)
  // delta_p_inertial = rho * a_p * L / (g_c) * (area ratio)
  let pInertial = 0;
  if (Math.abs(pipeAccFtS2) > 0 && isClosedPipe) {
    const areaRatio = Math.pow(d1, 2) / Math.max(0.1, Math.pow(d2, 2) - Math.pow(d1, 2));
    // in field units:
    pInertial = (mudWeightPpg * pipeAccFtS2 * sectionLengthFt * areaRatio) / 19.32;
  }

  const total = pViscous + pInertial;
  const sign = pipeSpeedFtMin >= 0 ? 1 : -1;

  return {
    viscousPressurePsi: Math.round(sign * pViscous),
    inertialPressurePsi: Math.round(sign * pInertial),
    totalSurgePressurePsi: Math.round(sign * total),
  };
}

/**
 * 4.9 Cuttings Slip Velocity & Transport Ratio
 * Sourced: Bourgoyne Ch. 4, Eq. 4.102 - 4.109
 */
export function calculateCuttingsTransport(
  annularVelocityFtMin: number,
  mudWeightPpg: number,
  plasticViscosityCp: number,
  yieldPointLbf100ft2: number,
  cuttingDiameterInches: number = 0.25,
  cuttingDensityPpg: number = 21.7 // 2.6 SG rock cuttings
): { slipVelocityFtMin: number; netVelocityFtMin: number; transportRatioPct: number; isAdequate: boolean } {
  const dS = cuttingDiameterInches;
  const deltaRho = Math.max(0.1, cuttingDensityPpg - mudWeightPpg);

  // Apparent viscosity for cutting slip (Chien model, Eq. 4.109)
  const muApp = plasticViscosityCp + (5 * yieldPointLbf100ft2 * dS);

  // Slip velocity in ft/min using intermediate particle slip correlation:
  // v_sl = 175 * d_s * (delta_rho)^0.667 / (rho_f^0.333 * mu^0.333)
  const num = 175 * dS * Math.pow(deltaRho, 0.667);
  const denom = Math.pow(mudWeightPpg, 0.333) * Math.pow(Math.max(1, muApp), 0.333);
  const vSlipFtMin = Math.min(annularVelocityFtMin * 0.9, num / denom);

  const netVelocity = Math.max(0, annularVelocityFtMin - vSlipFtMin);
  const transportRatio = annularVelocityFtMin > 0 ? (netVelocity / annularVelocityFtMin) * 100 : 0;

  return {
    slipVelocityFtMin: Math.round(vSlipFtMin),
    netVelocityFtMin: Math.round(netVelocity),
    transportRatioPct: Math.round(transportRatio * 10) / 10,
    isAdequate: transportRatio >= 50, // Standard rule of thumb: >=50% transport efficiency required
  };
}
