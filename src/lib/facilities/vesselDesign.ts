/**
 * Pressure Vessel Mechanical Design Engine (ASME Section VIII Div. 1)
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapter 6: Mechanical Design of Pressure Vessels
 */

export interface SteelGrade {
  name: string;
  code: string;
  allowableStress1998Psi: number;
  allowableStress2007Psi: number;
  minTempF: number;
  maxTempF: number;
}

export const ASME_STEEL_GRADES: Record<string, SteelGrade> = {
  "SA-516-70": {
    name: "Carbon Steel Plate Grade 70",
    code: "SA-516 Gr 70",
    allowableStress1998Psi: 17500, // at 200°F (Ex. 6-1)
    allowableStress2007Psi: 20000,
    minTempF: -20,
    maxTempF: 650,
  },
  "SA-516-60": {
    name: "Carbon Steel Plate Grade 60",
    code: "SA-516 Gr 60",
    allowableStress1998Psi: 15000,
    allowableStress2007Psi: 17100,
    minTempF: -20,
    maxTempF: 650,
  },
  "SA-285-C": {
    name: "Low Pressure Carbon Steel Grade C",
    code: "SA-285 Gr C",
    allowableStress1998Psi: 13700,
    allowableStress2007Psi: 15700,
    minTempF: -20,
    maxTempF: 650,
  },
  "SA-36": {
    name: "Structural Carbon Steel",
    code: "SA-36",
    allowableStress1998Psi: 16600,
    allowableStress2007Psi: 16600,
    minTempF: -20,
    maxTempF: 650,
  },
};

export const STANDARD_PLATE_THICKNESSES = [
  0.25, 0.3125, 0.375, 0.4375, 0.5, 0.5625, 0.625, 0.6875, 0.75, 0.8125, 0.875, 0.9375, 1.0, 1.125, 1.25, 1.375,
  1.5, 1.75, 2.0,
];

/**
 * Table 6-1: Minimum Recommended MAWP from Operating Pressure
 */
export function calculateMinimumMAWP(operatingPressurePsig: number, hasPSH: boolean = true): number {
  let deltaP = 10;
  if (operatingPressurePsig < 50) {
    deltaP = 10;
  } else if (operatingPressurePsig <= 250) {
    deltaP = 25;
  } else if (operatingPressurePsig <= 500) {
    deltaP = operatingPressurePsig * 0.1;
  } else if (operatingPressurePsig <= 1000) {
    deltaP = 50;
  } else {
    deltaP = operatingPressurePsig * 0.05;
  }

  let pshCushion = 0;
  if (hasPSH) {
    pshCushion = Math.max(5, operatingPressurePsig * 0.05);
  }

  return Math.round(operatingPressurePsig + deltaP + pshCushion);
}

/**
 * Snaps a thickness to the next standard commercial plate size
 */
export function snapToCommercialPlate(requiredThicknessInches: number): number {
  for (const t of STANDARD_PLATE_THICKNESSES) {
    if (t >= requiredThicknessInches - 0.001) return t;
  }
  return Math.ceil(requiredThicknessInches * 16) / 16;
}

export interface VesselMechanicalDesignInput {
  designPressurePsig: number;
  operatingTempF?: number;
  insideDiameterInches: number; // or d in ft * 12
  seamToSeamLengthFt: number;
  headType: "2:1-ellipsoidal" | "hemispherical" | "cone-bottom";
  coneApexAngleDeg?: number; // e.g. 60 deg (half angle alpha = 30 deg)
  hasInternalCone?: boolean;
  materialKey?: string; // default "SA-516-70"
  jointEfficiency?: number; // default 0.85 (spot x-ray)
  corrosionAllowanceInches?: number; // default 0.25 (corrosive) or 0.125
  isVertical?: boolean;
  edition?: "1998" | "2007";
}

export interface VesselMechanicalDesignResult {
  shellThicknessCalcInches: number;
  shellThicknessPlateInches: number;
  headThicknessCalcInches: number;
  headThicknessPlateInches: number;
  coneThicknessCalcInches?: number;
  coneThicknessPlateInches?: number;
  skirtLengthFt: number;
  weights: {
    shellWeightLb: number;
    headsWeightLb: number;
    coneWeightLb: number;
    skirtWeightLb: number;
    internalsAndNozzlesLb: number;
    totalVesselWeightLb: number;
  };
  allowableStressPsi: number;
  maxInletVelocityFtS: number;
}

/**
 * Full ASME Section VIII Div. 1 Sizing & Vessel Weight Estimation
 * Traces directly to Arnold & Stewart Chapter 6, Example 6-1
 */
export function calculateVesselMechanicalDesign(
  input: VesselMechanicalDesignInput
): VesselMechanicalDesignResult {
  const {
    designPressurePsig,
    insideDiameterInches,
    seamToSeamLengthFt,
    headType,
    coneApexAngleDeg = 60,
    hasInternalCone = false,
    materialKey = "SA-516-70",
    jointEfficiency = 0.85,
    corrosionAllowanceInches = 0.25,
    isVertical = true,
    edition = "1998",
  } = input;

  const mat = ASME_STEEL_GRADES[materialKey] || ASME_STEEL_GRADES["SA-516-70"];
  const S = edition === "1998" ? mat.allowableStress1998Psi : mat.allowableStress2007Psi;
  const E = jointEfficiency;
  const P = designPressurePsig;
  const d = insideDiameterInches;
  const r = d / 2;
  const CA = corrosionAllowanceInches;

  // Eq. 6-1: Cylindrical Shell Thickness
  // t_shell = (P * r) / (S * E - 0.6 * P)
  const tShellPressure = (P * r) / (S * E - 0.6 * P);
  const tShellReq = tShellPressure + CA;
  const tShellPlate = snapToCommercialPlate(tShellReq);

  // Eq. 6-2: 2:1 Ellipsoidal Head Thickness
  // t_ellip = (P * d) / (2 * S * E - 0.2 * P)
  const tHeadPressure = (P * d) / (2 * S * E - 0.2 * P);
  const tHeadReq = tHeadPressure + CA;
  const tHeadPlate = snapToCommercialPlate(tHeadReq);

  // Eq. 6-4: Cone Thickness (alpha is half apex angle)
  const alphaRad = (coneApexAngleDeg / 2) * (Math.PI / 180);
  const tConePressure = (P * d) / (2 * Math.cos(alphaRad) * (S * E - 0.6 * P));
  const tConeReq = tConePressure + CA;
  const tConePlate = snapToCommercialPlate(tConeReq);

  // Shell weight: Eq. 6-5a: W = 11 * d * t * L
  let effectiveShellLengthFt = seamToSeamLengthFt;
  if (hasInternalCone) {
    // Shell extends down to enclose internal cone
    const coneHeightFt = (d / 2 / 12) / Math.tan(alphaRad);
    effectiveShellLengthFt += Math.round(coneHeightFt * 10) / 10;
  }
  const shellWeightLb = Math.round(11 * d * tShellPlate * effectiveShellLengthFt);

  // Head weight: Eq. 6-6a: W ≈ 0.34 * t * d^2 + 1.9 * t * d
  const singleHeadWeight = Math.round(0.34 * tHeadPlate * Math.pow(d, 2) + 1.9 * tHeadPlate * d);
  const numHeads = headType === "cone-bottom" ? 1 : 2;
  const headsWeightLb = singleHeadWeight * numHeads;

  // Cone weight: Eq. 6-7a: W = (0.23 * t * d^2) / sin(alpha)
  let coneWeightLb = 0;
  if (headType === "cone-bottom") {
    coneWeightLb = Math.round((0.23 * tConePlate * Math.pow(d, 2)) / Math.sin(alphaRad));
  } else if (hasInternalCone) {
    // Internal 1/4" thin cone
    coneWeightLb = Math.round((0.23 * 0.25 * Math.pow(d, 2)) / Math.sin(alphaRad));
  }

  // Skirt weight: Eqs. 6-8a & 6-9a
  let skirtLengthFt = 0;
  if (isVertical) {
    if (headType === "cone-bottom") {
      skirtLengthFt = Math.round(((0.5 * d) / (12 * Math.tan(alphaRad)) + 2) * 10) / 10;
    } else {
      skirtLengthFt = Math.round(((0.25 * d) / 12 + 2) * 10) / 10;
    }
  }
  const skirtWeightLb = isVertical ? Math.round(11 * d * 0.5 * skirtLengthFt) : 0;

  // Internals and nozzles ~ 5,000 lb standard estimate (or 10% subtotal)
  const subtotal = shellWeightLb + headsWeightLb + coneWeightLb + skirtWeightLb;
  const internalsAndNozzlesLb = Math.max(5000, Math.round(subtotal * 0.1));
  const totalVesselWeightLb = subtotal + internalsAndNozzlesLb;

  // Eq. 6-10a: Maximum inlet nozzle fluid velocity Vin <= sqrt(3500 / rho_f)
  // With typical fluid density ~ 50 lb/ft3:
  const maxInletVelocityFtS = Math.round(Math.sqrt(3500 / 50) * 10) / 10;

  return {
    shellThicknessCalcInches: Math.round(tShellReq * 1000) / 1000,
    shellThicknessPlateInches: tShellPlate,
    headThicknessCalcInches: Math.round(tHeadReq * 1000) / 1000,
    headThicknessPlateInches: tHeadPlate,
    coneThicknessCalcInches: headType === "cone-bottom" ? Math.round(tConeReq * 1000) / 1000 : undefined,
    coneThicknessPlateInches: headType === "cone-bottom" ? tConePlate : undefined,
    skirtLengthFt,
    weights: {
      shellWeightLb,
      headsWeightLb,
      coneWeightLb,
      skirtWeightLb,
      internalsAndNozzlesLb,
      totalVesselWeightLb,
    },
    allowableStressPsi: S,
    maxInletVelocityFtS,
  };
}
