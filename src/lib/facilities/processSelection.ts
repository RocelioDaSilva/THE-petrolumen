/**
 * Process Selection, Stage Separation, Crude Stabilization & Utilities Engine
 * Sourced from Arnold & Stewart, "Surface Production Operations", Vol. 1 (3rd ed.)
 * Chapters 1, 2, and 8
 */

export interface CompressorStageDesign {
  stageRatio: number;
  numberOfStages: number;
  suctionPressurePsia: number;
  dischargePressurePsia: number;
  interstagePressuresPsia: number[];
  recommendedCompressorType: "Reciprocating" | "Centrifugal";
  estimatedHp: number;
}

/**
 * Eq. 2-2: Compressor Stage Ratio R = (Pd / Ps)^(1/n)
 * Also recommends optimal number of stages and intermediate pressures
 */
export function calculateCompressorStages(
  psPsia: number,
  pdPsia: number,
  flowRateMmscfd: number = 10,
  maxRatioPerStage: number = 3.8
): CompressorStageDesign {
  const overallRatio = pdPsia / psPsia;
  // Choose n stages such that R <= maxRatioPerStage (typically 3.6 to 4.0)
  let n = 1;
  while (Math.pow(overallRatio, 1 / n) > maxRatioPerStage && n < 6) {
    n++;
  }

  const R = Math.pow(overallRatio, 1 / n);
  const interstage: number[] = [];
  let currentP = psPsia;
  for (let i = 0; i <= n; i++) {
    interstage.push(Math.round(currentP));
    currentP *= R;
  }

  // Estimated HP: GPSA rule of thumb ~ 22 HP / (MMscfd * stage) for typical R ~ 3.5
  const estimatedHp = Math.round(flowRateMmscfd * n * 22 * (R / 3.0));

  let compressorType: "Reciprocating" | "Centrifugal" = "Reciprocating";
  if (estimatedHp > 3500 && R < 2.8) {
    compressorType = "Centrifugal";
  }

  return {
    stageRatio: Math.round(R * 100) / 100,
    numberOfStages: n,
    suctionPressurePsia: psPsia,
    dischargePressurePsia: pdPsia,
    interstagePressuresPsia: interstage,
    recommendedCompressorType: compressorType,
    estimatedHp,
  };
}

/**
 * Table 2-2: Stage Separation Guidelines
 * Recommends number of separation stages based on initial separator pressure
 */
export function recommendSeparationStages(initialSepPressurePsig: number): {
  recommendedStages: number;
  stagePressureGuidePsig: number[];
  rationale: string;
} {
  if (initialSepPressurePsig <= 125) {
    return {
      recommendedStages: 1,
      stagePressureGuidePsig: [initialSepPressurePsig, 0],
      rationale: "Vazões e pressões baixas: 1 estágio de alta/baixa pressão seguido de tanque atmosférico.",
    };
  } else if (initialSepPressurePsig <= 300) {
    return {
      recommendedStages: 2,
      stagePressureGuidePsig: [initialSepPressurePsig, 50, 0],
      rationale: "Pressão moderada: 2 estágios (ex: 250 psig -> 50 psig -> tanque).",
    };
  } else if (initialSepPressurePsig <= 500) {
    return {
      recommendedStages: 2,
      stagePressureGuidePsig: [initialSepPressurePsig, 65, 0],
      rationale: "Pressão intermediária: 2 estágios com vaso de baixa a 50-65 psig.",
    };
  } else if (initialSepPressurePsig <= 1000) {
    return {
      recommendedStages: 3,
      stagePressureGuidePsig: [initialSepPressurePsig, 250, 50, 0],
      rationale: "Alta pressão: 3 estágios (HP -> IP -> LP -> tanque) maximizam recuperação de líquidos leves e minimizam potência de compressão.",
    };
  } else {
    return {
      recommendedStages: 4,
      stagePressureGuidePsig: [initialSepPressurePsig, 500, 150, 40, 0],
      rationale: "Pressão muito alta (>1000 psig): 3 a 4 estágios recomendados para evitar perda de intermediários e manter estabilidade.",
    };
  }
}

/**
 * Table 2-3: Tank Breathing Loss Estimation (bbl/year)
 */
export function estimateTankBreathingLoss(tankCapacityBbl: number): {
  openVentLossBblYr: number;
  pressureValveLossBblYr: number;
  barrelsSavedBblYr: number;
  percentSaved: number;
} {
  // Arnold & Stewart Table 2-3 interpolation
  let openVent = 0;
  let pValve = 0;

  if (tankCapacityBbl <= 5000) {
    const frac = tankCapacityBbl / 5000;
    openVent = 235 * frac;
    pValve = 154 * frac;
  } else if (tankCapacityBbl <= 10000) {
    const frac = (tankCapacityBbl - 5000) / 5000;
    openVent = 235 + (441 - 235) * frac;
    pValve = 154 + (297 - 154) * frac;
  } else if (tankCapacityBbl <= 20000) {
    const frac = (tankCapacityBbl - 10000) / 10000;
    openVent = 441 + (625 - 441) * frac;
    pValve = 297 + (570 - 297) * frac;
  } else {
    const frac = Math.min(2.5, (tankCapacityBbl - 20000) / 35000);
    openVent = 625 + (2000 - 625) * frac;
    pValve = 570 + (1382 - 570) * frac;
  }

  const saved = openVent - pValve;
  const pct = openVent > 0 ? (saved / openVent) * 100 : 0;

  return {
    openVentLossBblYr: Math.round(openVent),
    pressureValveLossBblYr: Math.round(pValve),
    barrelsSavedBblYr: Math.round(saved),
    percentSaved: Math.round(pct * 10) / 10,
  };
}

/**
 * Control Valve Flow Coefficient Cv (Liquid)
 * Cv = Q * sqrt(SG / Delta_P)
 */
export function calculateControlValveCv(
  flowRateGpm: number,
  deltaPPsi: number,
  sgLiquid: number = 0.85
): {
  cv: number;
  recommendedValveSizeInches: number;
  failMode: "FC (Fail Close)" | "FO (Fail Open)";
} {
  const safeDP = Math.max(1, deltaPPsi);
  const cv = flowRateGpm * Math.sqrt(sgLiquid / safeDP);

  // Approximate valve body size lookup from Cv
  let valveSize = 1.0;
  if (cv > 250) valveSize = 4.0;
  else if (cv > 140) valveSize = 3.0;
  else if (cv > 60) valveSize = 2.0;
  else if (cv > 30) valveSize = 1.5;
  else valveSize = 1.0;

  return {
    cv: Math.round(cv * 10) / 10,
    recommendedValveSizeInches: valveSize,
    failMode: "FC (Fail Close)",
  };
}
