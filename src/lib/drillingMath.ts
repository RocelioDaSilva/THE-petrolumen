/**
 * PetroLúmen Drilling Calculations & Well Control Engine
 * Based on classic industry standards:
 * - "Formulas and Calculations for Drilling, Production, and Workover" (Norton J. Lapeyrouse)
 * - "An Introduction to Well Control Calculations for Drilling Operations" (Cormack)
 * - "Applied Drilling Engineering" (Bourgoyne et al.)
 */

// ==========================================
// 1. CALCULATION ENGINE & COMPANY ROUNDING RULES
// ==========================================

export const DRILLING_CONSTANTS = {
  PRESSURE_FACTOR: 0.052, // psi / (ppg * ft)
  CAPACITY_FACTOR: 1029.4, // in^2 * ft / bbl
  STEEL_DENSITY_FACTOR: 2747, // lb / bbl steel
  CUFT_TO_BBL: 0.1781, // bbl / ft^3
  BBL_TO_CUFT: 5.6146, // ft^3 / bbl
  M3_TO_BBL: 6.2905, // bbl / m^3
  BBL_TO_M3: 0.15897, // m^3 / bbl
  BAR_TO_PSI: 14.5038, // psi / bar
  PSI_TO_BAR: 0.0689476, // bar / psi
  METERS_TO_FEET: 3.28084, // ft / m
  FEET_TO_METERS: 0.3048, // m / ft
  PPG_TO_SG: 0.1198, // SG / ppg
  SG_TO_PPG: 8.3454, // ppg / SG
  GALLONS_TO_BBL: 0.02381, // bbl / gal (1/42)
  BBL_TO_GALLONS: 42, // gal / bbl
};

/**
 * Company Standard Rounding Rules:
 * - capacities: 4–5 decimal places
 * - volumes: 2 decimal places
 * - pump output: 3 decimal places
 * - strokes/time: whole numbers
 * - pressures: nearest psi (integer)
 * - mud weights: usually 2 decimals
 * - kill mud weight: ROUND UP to 1 decimal
 * - maximum mud weight: ROUND DOWN to 1 decimal
 */
export const RoundRules = {
  capacity: (val: number) => Number(val.toFixed(5)),
  volume: (val: number) => Number(val.toFixed(2)),
  pumpOutput: (val: number) => Number(val.toFixed(3)),
  strokes: (val: number) => Math.round(val),
  pressure: (val: number) => Math.round(val),
  mudWeight: (val: number) => Number(val.toFixed(2)),
  killMudWeight: (val: number) => Math.ceil(val * 10) / 10, // Round UP to 1 dec
  maxMudWeight: (val: number) => Math.floor(val * 10) / 10, // Round DOWN to 1 dec
};

// ==========================================
// 2. VOLUME ENGINE (Pits, Tubulars, Pumps, Trip Sheets)
// ==========================================

export interface RectangularPitInput {
  lengthFt: number;
  widthFt: number;
  depthFt: number;
}

export function calculatePitVolume(input: RectangularPitInput) {
  const { lengthFt, widthFt, depthFt } = input;
  // Volume (bbl) = L(ft) * W(ft) * D(ft) * 0.1781
  const volumeBbl = lengthFt * widthFt * depthFt * DRILLING_CONSTANTS.CUFT_TO_BBL;
  const bblPerFoot = depthFt > 0 ? volumeBbl / depthFt : 0;
  const volumeM3 = volumeBbl * DRILLING_CONSTANTS.BBL_TO_M3;

  return {
    volumeBbl: RoundRules.volume(volumeBbl),
    bblPerFoot: RoundRules.volume(bblPerFoot),
    volumeM3: RoundRules.volume(volumeM3),
    steps: [
      `Volume (bbl) = L (${lengthFt} ft) × W (${widthFt} ft) × D (${depthFt} ft) × 0.1781`,
      `= ${(lengthFt * widthFt * depthFt).toFixed(1)} ft³ × 0.1781 = ${volumeBbl.toFixed(2)} bbl`,
      `Bbl por pé = ${volumeBbl.toFixed(2)} bbl ÷ ${depthFt} ft = ${bblPerFoot.toFixed(2)} bbl/ft`,
    ],
  };
}

export function pipeCapacity(idInches: number): number {
  const safeId = Math.max(0.5, idInches);
  return RoundRules.capacity(Math.pow(safeId, 2) / DRILLING_CONSTANTS.CAPACITY_FACTOR);
}

export function annularCapacity(holeIdInches: number, pipeOdInches: number): number {
  const safeHole = Math.max(1, holeIdInches);
  const safePipe = Math.max(0.5, pipeOdInches);
  const diff = Math.max(0, Math.pow(safeHole, 2) - Math.pow(safePipe, 2));
  return RoundRules.capacity(diff / DRILLING_CONSTANTS.CAPACITY_FACTOR);
}

export function pipeDisplacement(weightLbFt: number): number {
  // Actual pipe displacement from weight: lb/ft ÷ 2747
  return RoundRules.capacity(weightLbFt / DRILLING_CONSTANTS.STEEL_DENSITY_FACTOR);
}

export function closedEndDisplacement(odInches: number): number {
  // Closed-End Displacement = OD^2 / 1029.4
  return RoundRules.capacity(Math.pow(odInches, 2) / DRILLING_CONSTANTS.CAPACITY_FACTOR);
}

export interface TriplexPumpInput {
  linerIdInches: number;
  strokeLengthInches: number;
  efficiencyPercent: number; // e.g. 97
  spm: number;
}

export function calculateTriplexPump(input: TriplexPumpInput) {
  const { linerIdInches, strokeLengthInches, efficiencyPercent, spm } = input;
  const strokeFt = strokeLengthInches / 12;
  const effFrac = efficiencyPercent / 100;
  // Pump Output (bbl/stk) = linerID^2 / 1029.4 * strokeLength(ft) * 3 * efficiency
  const bblPerStk = (Math.pow(linerIdInches, 2) / DRILLING_CONSTANTS.CAPACITY_FACTOR) * strokeFt * 3 * effFrac;
  const bblPerMin = bblPerStk * spm;
  const gpm = bblPerMin * 42;

  return {
    bblPerStk: RoundRules.pumpOutput(bblPerStk),
    bblPerMin: RoundRules.volume(bblPerMin),
    gpm: RoundRules.volume(gpm),
    steps: [
      `Curso em pés = ${strokeLengthInches}" ÷ 12 = ${strokeFt.toFixed(3)} ft`,
      `Output (bbl/stk) = (${linerIdInches}² ÷ 1029.4) × ${strokeFt.toFixed(3)} ft × 3 × ${(effFrac).toFixed(2)}`,
      `= ${(Math.pow(linerIdInches, 2) / 1029.4).toFixed(5)} × ${strokeFt.toFixed(3)} × 3 × ${effFrac} = ${bblPerStk.toFixed(3)} bbl/stk`,
      `Vazão (bbl/min) = ${bblPerStk.toFixed(3)} bbl/stk × ${spm} SPM = ${bblPerMin.toFixed(2)} bbl/min (${gpm.toFixed(1)} GPM)`,
    ],
  };
}

// Multi-section well volume builder
export interface TubularSection {
  name: string;
  type: "DP" | "HWDP" | "DC";
  od: number;
  id: number;
  weightLbFt: number;
  lengthFt: number;
}

export interface AnnularSection {
  name: string;
  holeOrCasingId: number;
  pipeOd: number;
  lengthFt: number;
}

export function calculateWellVolumes(
  tubulars: TubularSection[],
  annularSections: AnnularSection[],
  pumpOutputBblStk: number,
  spm: number
) {
  let totalStringVol = 0;
  let totalStringDisplacement = 0;
  const stringDetails = tubulars.map((t) => {
    const cap = pipeCapacity(t.id);
    const vol = cap * t.lengthFt;
    const dispPerFt = pipeDisplacement(t.weightLbFt);
    const dispVol = dispPerFt * t.lengthFt;
    totalStringVol += vol;
    totalStringDisplacement += dispVol;
    return {
      ...t,
      capacityBblFt: cap,
      volumeBbl: RoundRules.volume(vol),
      displacementBblFt: dispPerFt,
      displacementBbl: RoundRules.volume(dispVol),
    };
  });

  let totalAnnularVol = 0;
  const annularDetails = annularSections.map((a) => {
    const cap = annularCapacity(a.holeOrCasingId, a.pipeOd);
    const vol = cap * a.lengthFt;
    totalAnnularVol += vol;
    return {
      ...a,
      capacityBblFt: cap,
      volumeBbl: RoundRules.volume(vol),
    };
  });

  const totalWellVol = totalStringVol + totalAnnularVol;
  const safePump = Math.max(0.01, pumpOutputBblStk);
  const strokesToBit = RoundRules.strokes(totalStringVol / safePump);
  const timeToBit = spm > 0 ? RoundRules.strokes(strokesToBit / spm) : 0;

  const strokesBottomsUp = RoundRules.strokes(totalAnnularVol / safePump);
  const timeBottomsUp = spm > 0 ? RoundRules.strokes(strokesBottomsUp / spm) : 0;

  const totalCirculatingStrokes = strokesToBit + strokesBottomsUp;
  const totalCirculatingTime = spm > 0 ? RoundRules.strokes(totalCirculatingStrokes / spm) : 0;

  return {
    stringDetails,
    annularDetails,
    totalStringVol: RoundRules.volume(totalStringVol),
    totalStringDisplacement: RoundRules.volume(totalStringDisplacement),
    totalAnnularVol: RoundRules.volume(totalAnnularVol),
    totalWellVol: RoundRules.volume(totalWellVol),
    strokesToBit,
    timeToBit,
    strokesBottomsUp,
    timeBottomsUp,
    totalCirculatingStrokes,
    totalCirculatingTime,
  };
}

// Digital Trip Sheet Stand Tracker
export interface TripSheetEntry {
  standNumber: number;
  standLengthFt: number; // typically 90-93 ft
  isHwdpOrDc: boolean;
  isWetTrip: boolean;
  calculatedDisplacementBbl: number;
  actualTripTankBbl: number;
  cumulativeCalculatedBbl: number;
  cumulativeActualBbl: number;
  differenceBbl: number;
  status: "OK" | "WARNING_GAIN" | "WARNING_LOSS";
}

export function buildTripSheetRow(
  standNumber: number,
  standLengthFt: number,
  pipeDispBblFt: number,
  closedEndDispBblFt: number,
  isWetTrip: boolean,
  actualTankChangeBbl: number,
  prevCumCalc: number,
  prevCumActual: number,
  toleranceBbl: number = 1.5
): TripSheetEntry {
  const dispPerFt = isWetTrip ? closedEndDispBblFt : pipeDispBblFt;
  const standDisp = RoundRules.volume(dispPerFt * standLengthFt);
  const cumCalc = RoundRules.volume(prevCumCalc + standDisp);
  const cumActual = RoundRules.volume(prevCumActual + actualTankChangeBbl);
  const diff = RoundRules.volume(cumActual - cumCalc);

  let status: "OK" | "WARNING_GAIN" | "WARNING_LOSS" = "OK";
  if (diff > toleranceBbl) status = "WARNING_GAIN"; // hole taking less mud than expected -> swabbing / kick!
  else if (diff < -toleranceBbl) status = "WARNING_LOSS"; // hole taking more mud -> loss of circulation!

  return {
    standNumber,
    standLengthFt,
    isHwdpOrDc: false,
    isWetTrip,
    calculatedDisplacementBbl: standDisp,
    actualTripTankBbl: RoundRules.volume(actualTankChangeBbl),
    cumulativeCalculatedBbl: cumCalc,
    cumulativeActualBbl: cumActual,
    differenceBbl: diff,
    status,
  };
}

// ==========================================
// 3. PRESSURE ENGINE (Gradients, Tripping Loss, LOT, MAASP)
// ==========================================

export function calculateHydrostatic(mudWeight: number, tvd: number) {
  const gradient = mudWeight * DRILLING_CONSTANTS.PRESSURE_FACTOR;
  const hp = gradient * tvd;
  return {
    gradient: RoundRules.capacity(gradient),
    hp: RoundRules.pressure(hp),
    steps: [
      `Gradiente (psi/ft) = ${mudWeight} ppg × 0.052 = ${gradient.toFixed(4)} psi/ft`,
      `Pressão Hidrostática (psi) = ${gradient.toFixed(4)} psi/ft × ${tvd} ft = ${hp.toFixed(1)} psi`,
    ],
  };
}

export function calculatePressureChangeWithSpeed(pOld: number, spmOld: number, spmNew: number) {
  // P_new = P_old * (SPM_new / SPM_old)^2
  const ratio = spmOld > 0 ? spmNew / spmOld : 1;
  const pNew = pOld * Math.pow(ratio, 2);
  return {
    pNew: RoundRules.pressure(pNew),
    steps: [
      `Nova Pressão = ${pOld} psi × (${spmNew} ÷ ${spmOld})²`,
      `= ${pOld} psi × ${(ratio * ratio).toFixed(4)} = ${pNew.toFixed(1)} psi`,
    ],
  };
}

export function calculatePressureChangeWithMudWeight(pOld: number, mwOld: number, mwNew: number) {
  // P_new = P_old * (MW_new / MW_old)
  const ratio = mwOld > 0 ? mwNew / mwOld : 1;
  const pNew = pOld * ratio;
  return {
    pNew: RoundRules.pressure(pNew),
    steps: [
      `Nova Pressão = ${pOld} psi × (${mwNew} ÷ ${mwOld}) = ${pNew.toFixed(1)} psi`,
    ],
  };
}

export function calculateLOTAndMAASP(
  testMw: number,
  shoeTvd: number,
  lotSurfacePressure: number,
  currentMw: number
) {
  // Fracture Pressure = Test MW * 0.052 * Shoe TVD + LOT Pressure
  const testHpAtShoe = testMw * DRILLING_CONSTANTS.PRESSURE_FACTOR * shoeTvd;
  const fracturePressure = testHpAtShoe + lotSurfacePressure;
  const fractureGradient = fracturePressure / shoeTvd;

  // Max MW = LOT / (Shoe TVD * 0.052) + Test MW (ROUND DOWN to 1 decimal)
  const maxMwExact = lotSurfacePressure / (shoeTvd * DRILLING_CONSTANTS.PRESSURE_FACTOR) + testMw;
  const maxMw = RoundRules.maxMudWeight(maxMwExact);

  // MAASP = (Max MW - Current MW) * 0.052 * Shoe TVD
  const maasp = (maxMw - currentMw) * DRILLING_CONSTANTS.PRESSURE_FACTOR * shoeTvd;
  const isMaaspAlert = maasp <= 0 || currentMw >= maxMw;

  return {
    testHpAtShoe: RoundRules.pressure(testHpAtShoe),
    fracturePressure: RoundRules.pressure(fracturePressure),
    fractureGradient: RoundRules.capacity(fractureGradient),
    maxMw,
    maxMwExact: Number(maxMwExact.toFixed(2)),
    maasp: RoundRules.pressure(maasp),
    isMaaspAlert,
    steps: [
      `HP na Sapata no Teste = ${testMw} ppg × 0.052 × ${shoeTvd} ft = ${testHpAtShoe.toFixed(1)} psi`,
      `Pressão de Fratura = ${testHpAtShoe.toFixed(1)} psi + ${lotSurfacePressure} psi = ${fracturePressure.toFixed(1)} psi`,
      `Gradiente de Fratura = ${fracturePressure.toFixed(1)} psi ÷ ${shoeTvd} ft = ${fractureGradient.toFixed(4)} psi/ft`,
      `Densidade Máxima (Max MW) = ${lotSurfacePressure} ÷ (${shoeTvd} × 0.052) + ${testMw} = ${maxMwExact.toFixed(2)} → arredonda p/ baixo: ${maxMw} ppg`,
      `MAASP = (${maxMw} - ${currentMw}) × 0.052 × ${shoeTvd} ft = ${maasp.toFixed(1)} psi`,
    ],
  };
}

// Tripping pressure loss (swab/surge)
export function calculateTrippingPressureLoss(
  mudWeight: number,
  pipeDispBblFt: number,
  closedEndDispBblFt: number,
  casingCapBblFt: number,
  standLengthFt: number,
  numStands: number,
  isWetTrip: boolean
) {
  // Dry trip: deltaP/ft = (MW * 0.052 * PipeDisp) / (CasingCap - PipeDisp)
  // Wet trip: deltaP/ft = (MW * 0.052 * ClosedEndDisp) / (CasingCap - ClosedEndDisp)
  const disp = isWetTrip ? closedEndDispBblFt : pipeDispBblFt;
  const denom = Math.max(0.001, casingCapBblFt - disp);
  const deltaPPerFt = (mudWeight * DRILLING_CONSTANTS.PRESSURE_FACTOR * disp) / denom;
  const totalLength = standLengthFt * numStands;
  const totalDeltaP = deltaPPerFt * totalLength;

  return {
    deltaPPerFt: RoundRules.capacity(deltaPPerFt),
    totalDeltaP: RoundRules.pressure(totalDeltaP),
    steps: [
      `Tipo de Manobra: ${isWetTrip ? "Molhada (Wet - Closed End)" : "Seca (Dry - Open End)"}`,
      `Deslocamento do Tubo = ${disp.toFixed(5)} bbl/ft | Capacidade Revestimento = ${casingCapBblFt.toFixed(5)} bbl/ft`,
      `ΔP por pé = (${mudWeight} × 0.052 × ${disp.toFixed(5)}) ÷ (${casingCapBblFt.toFixed(5)} - ${disp.toFixed(5)}) = ${deltaPPerFt.toFixed(4)} psi/ft`,
      `Perda Total de Pressão = ${deltaPPerFt.toFixed(4)} psi/ft × (${standLengthFt} ft × ${numStands} stands) = ${totalDeltaP.toFixed(1)} psi`,
    ],
  };
}

// ==========================================
// 4. WELL-CONTROL ENGINE (Split Influx, Schedules, Formation P)
// ==========================================

export interface AdvancedWellControlInput {
  tvd: number;
  md: number;
  currentMw: number;
  casingShoeTvd: number;
  lotTestMw: number;
  lotSurfacePressure: number;
  sidpp: number;
  sicp: number;
  pitGainBbl: number;
  scrPressure: number;
  scrSpm: number;
  pumpOutputBblStk: number;
  dcLengthFt: number;
  dcOhAnnCapBblFt: number;
  dpOhAnnCapBblFt: number;
  drillStringStrokes: number;
}

export function calculateAdvancedWellControl(input: AdvancedWellControlInput) {
  const {
    tvd,
    currentMw,
    casingShoeTvd,
    lotTestMw,
    lotSurfacePressure,
    sidpp,
    sicp,
    pitGainBbl,
    scrPressure,
    drillStringStrokes,
    dcLengthFt,
    dcOhAnnCapBblFt,
    dpOhAnnCapBblFt,
  } = input;

  // 1. Formation Pressure: P_form = String HP + SIDPP
  const stringHp = currentMw * DRILLING_CONSTANTS.PRESSURE_FACTOR * tvd;
  const formationPressure = stringHp + sidpp;
  const formationGradient = formationPressure / tvd;
  const balanceMw = formationPressure / (tvd * DRILLING_CONSTANTS.PRESSURE_FACTOR);

  // 2. Kill Mud Weight: KMW = SIDPP / (TVD * 0.052) + Current MW (ROUND UP to 1 dec)
  const kmwExact = sidpp / (tvd * DRILLING_CONSTANTS.PRESSURE_FACTOR) + currentMw;
  const kmw = RoundRules.killMudWeight(kmwExact);

  // 3. Circulating Pressures
  const icp = RoundRules.pressure(scrPressure + sidpp);
  const fcp = RoundRules.pressure((kmw / currentMw) * scrPressure);

  // 4. Influx Height (Split across DC-OH and DP-OH if kick exceeds DC-OH volume)
  const dcOhCapacity = Math.max(0.001, dcOhAnnCapBblFt);
  const dpOhCapacity = Math.max(0.001, dpOhAnnCapBblFt);
  const dcOhVol = dcOhCapacity * dcLengthFt;

  let influxHeightFt = 0;
  let isSplitInflux = false;
  let dcHeightFt = 0;
  let dpHeightFt = 0;

  if (pitGainBbl <= dcOhVol) {
    influxHeightFt = pitGainBbl / dcOhCapacity;
    dcHeightFt = influxHeightFt;
  } else {
    isSplitInflux = true;
    dcHeightFt = dcLengthFt;
    const remainingKick = pitGainBbl - dcOhVol;
    dpHeightFt = remainingKick / dpOhCapacity;
    influxHeightFt = dcLengthFt + dpHeightFt;
  }

  // 5. Influx Gradient & Fluid Identification
  // Influx Gradient = (Current MW * 0.052) - ((SICP - SIDPP) / Influx Height)
  const safeInfluxHeight = Math.max(1, influxHeightFt);
  const influxGradient = (currentMw * DRILLING_CONSTANTS.PRESSURE_FACTOR) - ((sicp - sidpp) / safeInfluxHeight);
  const influxMw = influxGradient / DRILLING_CONSTANTS.PRESSURE_FACTOR;

  let influxType: "Gás" | "Óleo / Condensado" | "Água Salgada" = "Gás";
  if (influxMw < 2.5) influxType = "Gás";
  else if (influxMw <= 7.0) influxType = "Óleo / Condensado";
  else influxType = "Água Salgada";

  // 6. MAASP & LOT
  const lotCalc = calculateLOTAndMAASP(lotTestMw, casingShoeTvd, lotSurfacePressure, currentMw);

  // 7. Step-Down Circulating Pressure Schedule
  // psi / 100 strokes = (ICP - FCP) / SurfaceToBitStrokes * 100
  const safeStkToBit = Math.max(100, drillStringStrokes);
  const psiPer100Stk = ((icp - fcp) / safeStkToBit) * 100;

  const dynamicSchedule: { strokes: number; dpp: number }[] = [];
  const staticSchedule: { strokes: number; sidpp: number }[] = [];

  const step = Math.max(50, Math.round(safeStkToBit / 10));
  for (let s = 0; s <= safeStkToBit; s += step) {
    const ratio = s / safeStkToBit;
    const dpp = icp - ratio * (icp - fcp);
    const staticDpp = sidpp - ratio * sidpp;
    dynamicSchedule.push({ strokes: s, dpp: RoundRules.pressure(dpp) });
    staticSchedule.push({ strokes: s, sidpp: RoundRules.pressure(staticDpp) });
  }

  return {
    stringHp: RoundRules.pressure(stringHp),
    formationPressure: RoundRules.pressure(formationPressure),
    formationGradient: RoundRules.capacity(formationGradient),
    balanceMw: RoundRules.mudWeight(balanceMw),
    kmwExact: Number(kmwExact.toFixed(2)),
    kmw,
    icp,
    fcp,
    influxHeightFt: RoundRules.volume(influxHeightFt),
    isSplitInflux,
    dcHeightFt: RoundRules.volume(dcHeightFt),
    dpHeightFt: RoundRules.volume(dpHeightFt),
    influxGradient: RoundRules.capacity(influxGradient),
    influxMw: RoundRules.mudWeight(influxMw),
    influxType,
    lotCalc,
    psiPer100Stk: Number(psiPer100Stk.toFixed(1)),
    dynamicSchedule,
    staticSchedule,
  };
}

// ==========================================
// 5. HYDRAULICS & BIT JET OPTIMIZATION
// ==========================================

export interface HydraulicsInputs {
  mudWeight: number;
  flowRate: number;
  tvd: number;
  md: number;
  nozzleSizes: number[];
  plasticViscosity: number;
  yieldPoint: number;
  drillPipeOd: number;
  holeDiameter: number;
}

export function calculateHydraulics(inputs: HydraulicsInputs) {
  const {
    mudWeight,
    flowRate,
    tvd,
    nozzleSizes,
    plasticViscosity,
    yieldPoint,
    drillPipeOd,
    holeDiameter,
  } = inputs;

  const safeMw = Math.max(7, mudWeight);
  const safeQ = Math.max(50, flowRate);
  const safeTvd = Math.max(100, tvd);
  const safePv = Math.max(1, plasticViscosity);
  const safeYp = Math.max(1, yieldPoint);
  const safeHole = Math.max(3, holeDiameter);
  const safePipe = Math.max(2, drillPipeOd);

  const tfa = nozzleSizes.reduce((acc, size) => {
    const dInches = size / 32;
    return acc + (Math.PI / 4) * Math.pow(dInches, 2);
  }, 0);
  const safeTfa = Math.max(0.1, tfa);

  const bitPressureDrop = (8.311e-5 * safeMw * Math.pow(safeQ, 2)) / (Math.pow(0.95, 2) * Math.pow(safeTfa, 2));
  const bitHydraulicHorsepower = (bitPressureDrop * safeQ) / 1714;
  const bitArea = (Math.PI / 4) * Math.pow(safeHole, 2);
  const hhpPerSquareInch = bitHydraulicHorsepower / bitArea;
  const jetImpactForce = 0.01823 * safeQ * Math.sqrt(safeMw * Math.max(0, bitPressureDrop));
  const bitVelocity = (0.32086 * safeQ) / safeTfa;

  const dhMinusDp = Math.max(0.5, safeHole - safePipe);
  // Annular Bingham Plastic friction gradient: constant 200 for annulus (vs 225 for pipe) per API RP 13D & Bourgoyne Eq. 4.22
  const frictionGradient =
    (safePv * safeQ) / (60000 * Math.pow(dhMinusDp, 3)) + safeYp / (200 * dhMinusDp);
  const annularPressureLoss = Math.max(10, frictionGradient * safeTvd);
  const ecd = safeMw + annularPressureLoss / (DRILLING_CONSTANTS.PRESSURE_FACTOR * safeTvd);

  const av = (24.5 * safeQ) / (Math.pow(safeHole, 2) - Math.pow(safePipe, 2));
  const cci = (safeMw * (safePv + safeYp) * av) / 300000;
  const cuttingsTransportRatio = Math.min(95, Math.max(30, Math.round(55 + cci * 25)));

  return {
    tfa: RoundRules.capacity(safeTfa),
    bitPressureDrop: RoundRules.pressure(bitPressureDrop),
    bitHydraulicHorsepower: Number(bitHydraulicHorsepower.toFixed(1)),
    hhpPerSquareInch: Number(hhpPerSquareInch.toFixed(2)),
    jetImpactForce: RoundRules.pressure(jetImpactForce),
    bitVelocity: Number(bitVelocity.toFixed(1)),
    annularPressureLoss: RoundRules.pressure(annularPressureLoss),
    ecd: RoundRules.mudWeight(ecd),
    cuttingsTransportRatio,
    carryingCapacityIndex: Number(cci.toFixed(2)),
  };
}

export function generateLOTCurve(shoeTvd: number, mudWeight: number, leakOffPressure: number) {
  const safeShoeTvd = Math.max(500, shoeTvd);
  const safeMw = Math.max(7, mudWeight);
  const safeLop = Math.max(100, leakOffPressure);

  const lotEmw = Number((safeMw + safeLop / (DRILLING_CONSTANTS.PRESSURE_FACTOR * safeShoeTvd)).toFixed(2));
  const lotPressure = RoundRules.pressure(safeLop);

  const points: { pumpedBbl: number; pressure: number }[] = [];
  const nPoints = 12;
  const breakPointIdx = 8;

  for (let i = 0; i <= nPoints; i++) {
    const vol = Number((i * 0.25).toFixed(2));
    let p = 0;
    if (i <= breakPointIdx) {
      p = (i / breakPointIdx) * safeLop;
    } else {
      // Physical leak-off behavior: departure from linearity into microfracture propagation plateau (no artificial sine overshoot)
      const postRatio = (i - breakPointIdx) / (nPoints - breakPointIdx);
      p = safeLop + postRatio * 15;
    }
    points.push({ pumpedBbl: vol, pressure: RoundRules.pressure(p) });
  }

  return { points, lotEmw, lotPressure, maasp: lotPressure };
}
