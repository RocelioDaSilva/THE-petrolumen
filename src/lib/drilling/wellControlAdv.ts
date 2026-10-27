/**
 * Advanced Well Control & Pressure Schedules Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 4.
 */

export interface SchedulePoint {
  stroke: number;
  drillpipePressurePsi: number;
  casingPressurePsi: number;
  stageDescription: string;
}

/**
 * 4.3 Influx Density from Shut-In Casing and Drillpipe Pressures
 * Sourced: Bourgoyne Ch. 4, Eq. 4.18
 * rho_k = rho_m - (SICP - SIDPP) / (0.052 * L_k)
 */
export function kickDensityFromPressures(
  sicpPsi: number,
  sidppPsi: number,
  mudWeightPpg: number,
  influxHeightFt: number
): { influxDensityPpg: number; influxType: 'Gas' | 'Oil / Condensate' | 'Saltwater' } {
  if (influxHeightFt <= 0) {
    return { influxDensityPpg: mudWeightPpg, influxType: 'Saltwater' };
  }
  const deltaP = sicpPsi - sidppPsi;
  const rawRhoK = mudWeightPpg - deltaP / (0.052 * influxHeightFt);
  const rhoK = Math.max(0.5, Math.round(rawRhoK * 100) / 100);

  let influxType: 'Gas' | 'Oil / Condensate' | 'Saltwater' = 'Gas';
  if (rhoK >= 8.0) {
    influxType = 'Saltwater';
  } else if (rhoK >= 4.0) {
    influxType = 'Oil / Condensate';
  }

  return {
    influxDensityPpg: rhoK,
    influxType,
  };
}

/**
 * Kick length from pit gain and annular capacity
 * Sourced: Bourgoyne Ch. 4, Eq. 4.16: L_k = V_k / C_ann
 */
export function kickLengthFromPitGain(pitGainBbl: number, annularCapacityBblFt: number): number {
  if (annularCapacityBblFt <= 0) return 0;
  return Math.round(pitGainBbl / annularCapacityBblFt);
}

/**
 * Minimum Kick Detection Volume
 * Sourced: Bourgoyne Ch. 4, Eq. 4.19: V_d = q * t_d
 */
export function kickDetectionVolume(pumpRateBpm: number, detectionDelayMinutes: number): number {
  return Math.round(pumpRateBpm * detectionDelayMinutes * 10) / 10;
}

/**
 * Detailed Wait & Weight (Engineer's Method) Drillpipe Pressure Schedule
 * Sourced: Bourgoyne Ch. 4, Section 4.8 & Fig. 4.39B
 */
export function generateWaitAndWeightSchedule(
  icpPsi: number,
  fcpPsi: number,
  sicpPsi: number,
  surfaceToBitStrokes: number,
  bitToSurfaceStrokes: number,
  intervalsCount: number = 10
): SchedulePoint[] {
  const points: SchedulePoint[] = [];

  // Stage 1: Pumping kill mud from surface to bit (Linear step-down from ICP to FCP)
  const stepStrokes = Math.max(10, Math.floor(surfaceToBitStrokes / intervalsCount));
  for (let s = 0; s <= surfaceToBitStrokes; s += stepStrokes) {
    const fraction = s / surfaceToBitStrokes;
    const dpPressure = icpPsi - fraction * (icpPsi - fcpPsi);
    // Casing pressure rises slightly as gas expands, then drops as kill mud enters annulus
    const casPressure = sicpPsi + Math.sin(fraction * Math.PI) * 150;

    points.push({
      stroke: s,
      drillpipePressurePsi: Math.round(dpPressure),
      casingPressurePsi: Math.round(casPressure),
      stageDescription: s === 0 ? 'Início do Amortecimento (ICP)' : 'Descida Linear de Pressão na Coluna',
    });
  }

  // Ensure exact surface-to-bit point is present
  if (points[points.length - 1].stroke !== surfaceToBitStrokes) {
    points.push({
      stroke: surfaceToBitStrokes,
      drillpipePressurePsi: fcpPsi,
      casingPressurePsi: sicpPsi + 50,
      stageDescription: 'Lama de Amortecimento Atinge a Broca (FCP)',
    });
  }

  // Stage 2: Pumping kill mud from bit to surface (Hold FCP constant on drillpipe)
  const totalStrokes = surfaceToBitStrokes + bitToSurfaceStrokes;
  const annulusStep = Math.max(10, Math.floor(bitToSurfaceStrokes / intervalsCount));

  for (let s = surfaceToBitStrokes + annulusStep; s <= totalStrokes; s += annulusStep) {
    const annFraction = (s - surfaceToBitStrokes) / bitToSurfaceStrokes;
    // Casing pressure drops smoothly to zero (or choke margin) as kill mud reaches surface
    const casPressure = Math.max(0, (1 - annFraction) * (sicpPsi + 50));

    points.push({
      stroke: s,
      drillpipePressurePsi: fcpPsi,
      casingPressurePsi: Math.round(casPressure),
      stageDescription: annFraction >= 0.99 ? 'Poço Amortecido com Sucesso' : 'Deslocamento no Anular a FCP Constante',
    });
  }

  return points;
}

/**
 * Detailed Driller's Method (Two-Circulation) Drillpipe Pressure Schedule
 * Sourced: Bourgoyne Ch. 4, Section 4.8 & Fig. 4.39A
 */
export function generateDrillersMethodSchedule(
  icpPsi: number,
  fcpPsi: number,
  sicpPsi: number,
  surfaceToBitStrokes: number,
  bitToSurfaceStrokes: number
): { firstCirculation: SchedulePoint[]; secondCirculation: SchedulePoint[] } {
  const firstCirc: SchedulePoint[] = [];
  const secondCirc: SchedulePoint[] = [];

  const totalWellStrokes = surfaceToBitStrokes + bitToSurfaceStrokes;

  // 1st Circulation: Circulate out influx with original mud weight (hold ICP constant on DP)
  for (let s = 0; s <= totalWellStrokes; s += Math.floor(totalWellStrokes / 5)) {
    const fraction = s / totalWellStrokes;
    const casPressure = fraction === 0 ? sicpPsi : Math.max(0, sicpPsi * (1 - fraction * 0.7));
    firstCirc.push({
      stroke: s,
      drillpipePressurePsi: icpPsi,
      casingPressurePsi: Math.round(casPressure),
      stageDescription: s === 0 ? '1ª Circ.: Expulsão do Influxo a ICP' : '1ª Circ.: Removendo Influxo do Anular',
    });
  }

  // 2nd Circulation: Displace original mud with Kill Mud Weight
  // Surface to bit: step down from ICP to FCP
  for (let s = 0; s <= surfaceToBitStrokes; s += Math.floor(surfaceToBitStrokes / 3)) {
    const frac = s / surfaceToBitStrokes;
    secondCirc.push({
      stroke: s,
      drillpipePressurePsi: Math.round(icpPsi - frac * (icpPsi - fcpPsi)),
      casingPressurePsi: Math.round(firstCirc[firstCirc.length - 1].casingPressurePsi),
      stageDescription: '2ª Circ.: Injeção da Lama de Amortecimento',
    });
  }

  // Bit to surface: hold FCP constant
  for (let s = surfaceToBitStrokes; s <= totalWellStrokes; s += Math.floor(bitToSurfaceStrokes / 3)) {
    const frac = (s - surfaceToBitStrokes) / bitToSurfaceStrokes;
    secondCirc.push({
      stroke: s,
      drillpipePressurePsi: fcpPsi,
      casingPressurePsi: Math.round(Math.max(0, 100 * (1 - frac))),
      stageDescription: frac >= 0.9 ? '2ª Circ.: Poço Amortecido' : '2ª Circ.: Preenchimento do Anular com KMW',
    });
  }

  return {
    firstCirculation: firstCirc,
    secondCirculation: secondCirc,
  };
}
