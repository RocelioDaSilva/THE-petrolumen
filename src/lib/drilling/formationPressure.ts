/**
 * Formation Pore Pressure and Fracture Gradient Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 6.
 */

export const NORMAL_PORE_PRESSURE_GRADIENTS = {
  gulfCoastSaltwater: 0.465, // psi / ft (typical Gulf of Mexico / saline)
  freshwater: 0.433,         // psi / ft
  northSea: 0.452,           // psi / ft
  westTexas: 0.433,          // psi / ft
};

export const NORMAL_OVERBURDEN_GRADIENT = 1.0; // psi / ft typical consolidated sed. basin

/**
 * 6.1 d-Exponent & Normalized dcs-Exponent
 * Sourced: Bourgoyne Ch. 6, Eq. 6.13 - 6.14
 * d = log10( ROP / (60 * N) ) / log10( 12 * WOB / (10^6 * Db) )
 * dcs = d * (rho_normal / rho_mud)
 */
export function calculateDExponent(
  ropFtHr: number,
  rpm: number,
  wobLbf: number,
  bitDiameterInches: number,
  currentMudWeightPpg: number,
  normalPorePressurePpg: number = 8.95 // 0.465 psi/ft = 8.95 ppg
): { dExp: number; dcsExp: number } {
  const r = Math.max(0.1, ropFtHr);
  const n = Math.max(1, rpm);
  const w = Math.max(100, wobLbf);
  const db = Math.max(1, bitDiameterInches);

  const num = Math.log10(r / (60 * n));
  const denom = Math.log10((12 * w) / (1000000 * db));

  if (Math.abs(denom) < 1e-4) {
    return { dExp: 1.0, dcsExp: 1.0 };
  }

  const d = num / denom;
  const dcs = d * (normalPorePressurePpg / Math.max(1, currentMudWeightPpg));

  return {
    dExp: Math.round(d * 1000) / 1000,
    dcsExp: Math.round(dcs * 1000) / 1000,
  };
}

/**
 * 6.2 Eaton's Method for Pore Pressure Prediction from dcs, Resistivity, or Sonic
 * Sourced: Bourgoyne Ch. 6, Section 6.3, Eq. 6.15 - 6.17
 */
export function porePressureEatonFromDcs(
  observedDcs: number,
  normalTrendDcs: number,
  depthFt: number,
  overburdenGradPsiFt: number = 1.0,
  normalPoreGradPsiFt: number = 0.465,
  eatonExponent: number = 1.2
): { porePressurePsi: number; poreGradientPsiFt: number; equivalentMudWeightPpg: number } {
  if (normalTrendDcs <= 0 || depthFt <= 0) {
    const normalP = normalPoreGradPsiFt * depthFt;
    return {
      porePressurePsi: Math.round(normalP),
      poreGradientPsiFt: normalPoreGradPsiFt,
      equivalentMudWeightPpg: Math.round((normalPoreGradPsiFt / 0.052) * 10) / 10,
    };
  }

  // Eaton Eq: (p/D) = (sigma_v/D) - [(sigma_v/D) - (p/D)_n] * (dcs_obs / dcs_norm)^1.2
  const ratio = Math.max(0.1, observedDcs / normalTrendDcs);
  const effectiveStressNorm = overburdenGradPsiFt - normalPoreGradPsiFt;
  const poreGrad = overburdenGradPsiFt - effectiveStressNorm * Math.pow(ratio, eatonExponent);
  const poreP = poreGrad * depthFt;
  const emw = poreGrad / 0.052;

  return {
    porePressurePsi: Math.round(poreP),
    poreGradientPsiFt: Math.round(poreGrad * 1000) / 1000,
    equivalentMudWeightPpg: Math.round(emw * 10) / 10,
  };
}

export function porePressureEatonFromResistivity(
  observedResistivity: number,
  normalTrendResistivity: number,
  depthFt: number,
  overburdenGradPsiFt: number = 1.0,
  normalPoreGradPsiFt: number = 0.465
): { porePressurePsi: number; equivalentMudWeightPpg: number } {
  const ratio = Math.max(0.01, observedResistivity / Math.max(0.01, normalTrendResistivity));
  const effectiveStressNorm = overburdenGradPsiFt - normalPoreGradPsiFt;
  const poreGrad = overburdenGradPsiFt - effectiveStressNorm * Math.pow(ratio, 1.2);
  const p = poreGrad * depthFt;
  return {
    porePressurePsi: Math.round(p),
    equivalentMudWeightPpg: Math.round((poreGrad / 0.052) * 10) / 10,
  };
}

export function porePressureEatonFromSonic(
  observedDeltaTUsFt: number,
  normalTrendDeltaTUsFt: number,
  depthFt: number,
  overburdenGradPsiFt: number = 1.0,
  normalPoreGradPsiFt: number = 0.465
): { porePressurePsi: number; equivalentMudWeightPpg: number } {
  // Sonic Eaton uses exponent 3.0: (Delta_t_norm / Delta_t_obs)^3.0
  const ratio = Math.max(0.01, normalTrendDeltaTUsFt / Math.max(0.01, observedDeltaTUsFt));
  const effectiveStressNorm = overburdenGradPsiFt - normalPoreGradPsiFt;
  const poreGrad = overburdenGradPsiFt - effectiveStressNorm * Math.pow(ratio, 3.0);
  const p = poreGrad * depthFt;
  return {
    porePressurePsi: Math.round(p),
    equivalentMudWeightPpg: Math.round((poreGrad / 0.052) * 10) / 10,
  };
}

/**
 * 6.3 Fracture Pressure & Fracture Gradient Models
 * Sourced: Bourgoyne Ch. 6, Section 6.4, Eq. 6.18 - 6.25
 */
export interface FractureGradientModelsResult {
  hubbertWillisPsiFt: number; // minimum horizontal stress (sigma_3)
  eatonPsiFt: number;         // with Poisson's ratio
  matthewsKellyPsiFt: number; // with matrix stress coefficient Ki
  christmanOffshorePsiFt?: number; // with water depth
  recommendedFractureGradientPpg: number;
}

export function calculateFractureGradients(
  depthFt: number,
  poreGradientPsiFt: number,
  overburdenGradPsiFt: number = 1.0,
  poissonsRatio: number = 0.40, // typical 0.35 - 0.45 for shales
  matrixStressCoeffKi: number = 0.65,
  offshoreWaterDepthFt?: number
): FractureGradientModelsResult {
  const pGrad = poreGradientPsiFt;
  const obGrad = overburdenGradPsiFt;

  // 1. Hubbert & Willis: F = (1/3) * (obGrad + 2 * pGrad)
  const hwGrad = (1 / 3) * (obGrad + 2 * pGrad);

  // 2. Eaton: F = (nu / (1 - nu)) * (obGrad - pGrad) + pGrad
  const nu = Math.min(0.49, Math.max(0.2, poissonsRatio));
  const eatonGrad = (nu / (1 - nu)) * (obGrad - pGrad) + pGrad;

  // 3. Matthews & Kelly: F = Ki * (obGrad - pGrad) + pGrad
  const mkGrad = matrixStressCoeffKi * (obGrad - pGrad) + pGrad;

  // 4. Christman Offshore (taking water column into account if applicable)
  let christmanGrad: number | undefined;
  if (offshoreWaterDepthFt && offshoreWaterDepthFt > 0) {
    const waterGrad = 0.444; // seawater psi/ft
    const airGap = 80; // ft
    const sedimentDepth = depthFt - offshoreWaterDepthFt - airGap;
    if (sedimentDepth > 0) {
      const obOffshorePsi = waterGrad * offshoreWaterDepthFt + 0.95 * sedimentDepth;
      const obOffshoreGrad = obOffshorePsi / depthFt;
      christmanGrad = (nu / (1 - nu)) * (obOffshoreGrad - pGrad) + pGrad;
    }
  }

  const recGrad = eatonGrad;

  return {
    hubbertWillisPsiFt: Math.round(hwGrad * 1000) / 1000,
    eatonPsiFt: Math.round(eatonGrad * 1000) / 1000,
    matthewsKellyPsiFt: Math.round(mkGrad * 1000) / 1000,
    christmanOffshorePsiFt: christmanGrad ? Math.round(christmanGrad * 1000) / 1000 : undefined,
    recommendedFractureGradientPpg: Math.round((recGrad / 0.052) * 10) / 10,
  };
}

/**
 * 6.4 Kick Tolerance Intensity & Volume
 * Sourced: Bourgoyne Ch. 6, Section 6.5
 */
export function calculateKickTolerance(
  casingShoeTvdFt: number,
  totalWellTvdFt: number,
  currentMudWeightPpg: number,
  shoeFractureGradPpg: number,
  targetInfluxGradientPsiFt: number = 0.12, // typical gas influx ~0.10 - 0.15 psi/ft
  annularCapacityBblFt: number = 0.045
): {
  kickToleranceIntensityPpg: number;
  maaspPsi: number;
  maximumKickVolumeBbl: number;
  isSafe: boolean;
} {
  // MAASP at casing shoe: (rho_frac - rho_mud) * 0.052 * D_shoe
  const maaspPsi = Math.max(0, (shoeFractureGradPpg - currentMudWeightPpg) * 0.052 * casingShoeTvdFt);

  // Kick tolerance intensity at total depth:
  // KTI = rho_frac_shoe - rho_mud * (D_shoe / D_total) or MAASP / (0.052 * D_total)
  const kti = maaspPsi / (0.052 * Math.max(1, totalWellTvdFt));

  // Maximum allowable influx height before casing shoe fractures:
  // L_k_max = MAASP / (0.052 * rho_mud - G_influx)
  const deltaGrad = currentMudWeightPpg * 0.052 - targetInfluxGradientPsiFt;
  let maxKickVol = 0;
  if (deltaGrad > 0) {
    const maxKickHeight = maaspPsi / deltaGrad;
    maxKickVol = maxKickHeight * annularCapacityBblFt;
  }

  return {
    kickToleranceIntensityPpg: Math.round(kti * 10) / 10,
    maaspPsi: Math.round(maaspPsi),
    maximumKickVolumeBbl: Math.round(maxKickVol * 10) / 10,
    isSafe: kti >= 0.5 && maxKickVol >= 10, // at least 0.5 ppg margin and 10 bbl kick volume
  };
}
