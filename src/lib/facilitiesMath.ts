/**
 * PetroLúmen Surface Production & Facilities Engineering Engine
 * Based on "Surface Production Operations - Design of Oil Handling Systems and Facilities"
 * (Ken Arnold & Maurice Stewart)
 */

// ==========================================
// 1. TWO-PHASE & THREE-PHASE SEPARATOR SIZING
// ==========================================

export interface SeparatorInput {
  orientation: "horizontal" | "vertical";
  phases: "2-phase" | "3-phase";
  oilRateBopd: number; // bopd
  gasRateMmscfd: number; // MMscfd
  waterRateBwpd: number; // bwpd
  operatingPressurePsia: number; // psia
  operatingTemperatureF: number; // °F
  oilApi: number; // °API
  gasGravity: number; // air = 1.0
  waterGravity: number; // water = 1.05
  liquidRetentionTimeMin: number; // minutes (typically 3-5 min)
  dropletCutoffMicrons: number; // microns (typically 100-140)
}

export interface SeparatorResult {
  vesselDiameterInches: number;
  seamToSeamLengthFt: number;
  slendernessRatio: number; // L/D (typically 3 to 5 for horizontal)
  gasCapacityMmscfd: number;
  liquidCapacityBpd: number;
  terminalVelocityFtSec: number;
  retentionVolumeBbl: number;
  weirHeightInches?: number;
  oilWaterInterfaceInches?: number;
}

export function sizeSeparator(input: SeparatorInput): SeparatorResult {
  const {
    orientation,
    phases,
    oilRateBopd,
    gasRateMmscfd,
    waterRateBwpd,
    operatingPressurePsia,
    operatingTemperatureF,
    oilApi,
    gasGravity,
    liquidRetentionTimeMin = 3,
    dropletCutoffMicrons = 100,
  } = input;

  const safeP = Math.max(14.7, operatingPressurePsia);
  const safeT = Math.max(32, operatingTemperatureF);
  const tempR = safeT + 459.67;
  const safeQo = Math.max(10, oilRateBopd);
  const safeQg = Math.max(0.1, gasRateMmscfd);
  const safeQw = phases === "3-phase" ? Math.max(0, waterRateBwpd) : 0;
  const totalLiquid = safeQo + safeQw;
  const safeRet = Math.max(1, liquidRetentionTimeMin);

  // Density calculations
  // Gas density: rho_g = (28.96 * gammaG * P) / (Z * R * T)
  const zApprox = 0.9;
  const gasDensity = (28.96 * gasGravity * safeP) / (zApprox * 10.73 * tempR); // lb/cu ft
  // Oil density: 141.5 / (API + 131.5) * 62.4
  const gammaO = 141.5 / (oilApi + 131.5);
  const oilDensity = gammaO * 62.4; // lb/cu ft
  const liquidDensity = oilDensity;

  // Terminal velocity (Souders-Brown / Schiller-Naumann):
  // Vt = 0.0119 * sqrt((rho_L - rho_g) / rho_g) * K_factor
  const kFactor = 0.167; // GPSA mist extractor factor
  const densityRatio = Math.max(1, (liquidDensity - gasDensity) / Math.max(0.01, gasDensity));
  const terminalVelocity = kFactor * Math.sqrt(densityRatio); // ft/sec

  // Liquid retention volume required
  // V_liq = Q_liq * t_r / 1440 (in bbl)
  const retentionVolumeBbl = (totalLiquid * safeRet) / 1440;
  const retentionVolumeCuFt = retentionVolumeBbl * 5.615;

  let vesselDiameterInches = 36;
  let seamToSeamLengthFt = 10;

  if (orientation === "horizontal") {
    // Horizontal separator:
    // Diameter based on Arnold & Stewart empirical balance:
    // d^2 * Leff >= 420 * Q_liq * t_r
    // Start with slenderness ratio L/D ~ 4.0
    // d (inches), L (ft) -> L = 4 * d / 12 = d / 3
    const reqFactor = 420 * totalLiquid * safeRet;
    const estDiameterInches = Math.pow(reqFactor / (4 / 12), 1 / 3);
    // Standard shell diameters (increments of 6 inches: 24, 30, 36, 42, 48, 54, 60, 72, 84, 96...)
    vesselDiameterInches = Math.max(24, Math.round(estDiameterInches / 6) * 6);
    const estLengthFt = (reqFactor / Math.pow(vesselDiameterInches, 2)) * 1.25; // add 25% for gas space
    seamToSeamLengthFt = Math.max(8, Math.round(estLengthFt * 2) / 2);
  } else {
    // Vertical separator:
    // Diameter based on gas velocity:
    // d^2 >= 5040 * (T * Z * Q_g / P) * sqrt(rho_g / (rho_L - rho_g))
    const gasReq = 5040 * ((tempR * zApprox * safeQg) / safeP) * (1 / terminalVelocity);
    vesselDiameterInches = Math.max(24, Math.round(Math.sqrt(gasReq) / 6) * 6);
    // Length based on liquid volume:
    const crossAreaSqFt = (Math.PI / 4) * Math.pow(vesselDiameterInches / 12, 2);
    const liquidHeightFt = retentionVolumeCuFt / crossAreaSqFt;
    seamToSeamLengthFt = Math.max(8, Math.round((liquidHeightFt + 5) * 2) / 2); // 5 ft for gas & mist pad
  }

  const slendernessRatio = Number((seamToSeamLengthFt / (vesselDiameterInches / 12)).toFixed(1));

  // Max capacities with chosen vessel size
  const gasCapacityMmscfd = Number(
    (
      (Math.PI / 4) *
      Math.pow(vesselDiameterInches / 12, 2) *
      0.5 *
      terminalVelocity *
      (safeP / (tempR * zApprox * 10.73)) *
      (1 / 1000) *
      0.024
    ).toFixed(2)
  );

  const liquidCapacityBpd = Number(((vesselDiameterInches * seamToSeamLengthFt * 1440) / (420 * safeRet)).toFixed(0));

  // 3-Phase specific levels
  const weirHeightInches = phases === "3-phase" ? Math.round(vesselDiameterInches * 0.6) : undefined;
  const oilWaterInterfaceInches = phases === "3-phase" ? Math.round(vesselDiameterInches * 0.35) : undefined;

  return {
    vesselDiameterInches,
    seamToSeamLengthFt,
    slendernessRatio,
    gasCapacityMmscfd: Math.max(safeQg * 1.3, gasCapacityMmscfd),
    liquidCapacityBpd: Math.max(totalLiquid * 1.2, liquidCapacityBpd),
    terminalVelocityFtSec: Number(terminalVelocity.toFixed(2)),
    retentionVolumeBbl: Number(retentionVolumeBbl.toFixed(1)),
    weirHeightInches,
    oilWaterInterfaceInches,
  };
}

// ==========================================
// 2. GLYCOL DEHYDRATION (TEG CONTACTOR)
// ==========================================

export interface DehydrationInputs {
  gasFlowRateMmscfd: number;
  operatingPressurePsia: number;
  inletGasTemperatureF: number;
  outletDewPointTargetF: number; // e.g. 20 °F
  tegCirculationRateGalPerLbWater: number; // 2.5 - 3.5 gal TEG/lb H2O
}

export interface DehydrationResults {
  inletWaterContentLbMmscf: number;
  outletWaterContentLbMmscf: number;
  waterRemovedLbDay: number;
  tegCirculationRateGpm: number;
  contactorDiameterInches: number;
  glycolReboilerDutyBtuHr: number;
}

export function sizeTEGDehydration(inputs: DehydrationInputs): DehydrationResults {
  const {
    gasFlowRateMmscfd,
    operatingPressurePsia,
    inletGasTemperatureF,
    outletDewPointTargetF = 20,
    tegCirculationRateGalPerLbWater = 3.0,
  } = inputs;

  const safeP = Math.max(100, operatingPressurePsia);
  const safeT = Math.max(40, inletGasTemperatureF);
  const safeQg = Math.max(0.1, gasFlowRateMmscfd);

  // Saturated water content (McKetta & Wehe approximation):
  // W = (A / P) + B where A and B are empirical temperature functions
  const inletWaterContent = (47400 / safeP) * Math.exp(0.0315 * safeT);
  const outletWaterContent = (47400 / safeP) * Math.exp(0.0315 * outletDewPointTargetF);

  const waterRemovedPerMmscf = Math.max(0, inletWaterContent - outletWaterContent);
  const waterRemovedLbDay = waterRemovedPerMmscf * safeQg;

  // TEG Circulation Rate: GPM = (W_removed_lb_day * gal_per_lb) / (24 * 60)
  const tegCirculationRateGpm = (waterRemovedLbDay * tegCirculationRateGalPerLbWater) / 1440;

  // Contactor column diameter (Souders-Brown velocity):
  // D = sqrt(4 * Q_g / (pi * V_allowable))
  const vAllowable = 0.15 * Math.sqrt((70 - 2.5) / 2.5); // ~0.78 ft/s
  const areaReq = (safeQg * 1e6) / (86400 * 35.31 * vAllowable * (safeP / 14.7));
  const contactorDiameterInches = Math.max(18, Math.round(Math.sqrt((4 * areaReq) / Math.PI) * 12));

  // Reboiler Duty: ~2000 Btu/gal TEG circulated
  const reboilerDutyBtuHr = tegCirculationRateGpm * 60 * 2000;

  return {
    inletWaterContentLbMmscf: Number(inletWaterContent.toFixed(1)),
    outletWaterContentLbMmscf: Number(outletWaterContent.toFixed(1)),
    waterRemovedLbDay: Number(waterRemovedLbDay.toFixed(1)),
    tegCirculationRateGpm: Number(tegCirculationRateGpm.toFixed(2)),
    contactorDiameterInches,
    glycolReboilerDutyBtuHr: Number(reboilerDutyBtuHr.toFixed(0)),
  };
}
