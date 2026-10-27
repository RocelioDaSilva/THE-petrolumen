/**
 * Directional Drilling & Minimum Curvature Trajectory Engine
 * Sourced from Bourgoyne, Millheim, Chenevert & Young,
 * "Applied Drilling Engineering" (SPE Textbook Series, Vol. 2, 1986), Chapter 8.
 */

export interface SurveyStation {
  measuredDepthFt: number; // MD
  inclinationDeg: number;  // Inc (from vertical: 0 to 90+)
  azimuthDeg: number;      // Azi (0 to 360 clockwise from North)
}

export interface ComputedSurveyPoint {
  md: number;
  inc: number;
  azi: number;
  tvd: number;
  north: number;
  east: number;
  verticalSection: number;
  doglegSeverityDeg100ft: number;
  closureDistanceFt: number;
  closureAzimuthDeg: number;
}

/**
 * 8.1 Minimum Curvature Survey Method (Industry & SPE Standard)
 * Sourced: Bourgoyne Ch. 8, Section 8.3, Eq. 8.1 - 8.6
 */
export function calculateMinimumCurvature(
  stations: SurveyStation[],
  verticalSectionAzimuthDeg?: number
): ComputedSurveyPoint[] {
  if (stations.length === 0) return [];

  const points: ComputedSurveyPoint[] = [];

  // Station 0 (surface)
  const s0 = stations[0];
  let curTvd = s0.measuredDepthFt * Math.cos((s0.inclinationDeg * Math.PI) / 180);
  let curNorth = 0;
  let curEast = 0;

  points.push({
    md: s0.measuredDepthFt,
    inc: s0.inclinationDeg,
    azi: s0.azimuthDeg,
    tvd: Math.round(curTvd * 10) / 10,
    north: 0,
    east: 0,
    verticalSection: 0,
    doglegSeverityDeg100ft: 0,
    closureDistanceFt: 0,
    closureAzimuthDeg: s0.azimuthDeg,
  });

  for (let i = 1; i < stations.length; i++) {
    const prev = stations[i - 1];
    const curr = stations[i];

    const dMD = Math.max(0.1, curr.measuredDepthFt - prev.measuredDepthFt);
    const i1 = (prev.inclinationDeg * Math.PI) / 180;
    const i2 = (curr.inclinationDeg * Math.PI) / 180;
    const a1 = (prev.azimuthDeg * Math.PI) / 180;
    const a2 = (curr.azimuthDeg * Math.PI) / 180;

    // Dogleg angle beta (Eq. 8.1)
    // cos(beta) = cos(I2 - I1) - sin(I1)*sin(I2)*(1 - cos(A2 - A1))
    const cosBeta = Math.cos(i2 - i1) - Math.sin(i1) * Math.sin(i2) * (1 - Math.cos(a2 - a1));
    const clampedCosBeta = Math.max(-1, Math.min(1, cosBeta));
    const beta = Math.acos(clampedCosBeta);

    // Ratio factor F = (2 / beta) * tan(beta / 2)
    let F = 1.0;
    if (beta > 1e-6) {
      F = (2 / beta) * Math.tan(beta / 2);
    }

    // Increments (Eq. 8.2 - 8.4)
    const dTVD = (dMD / 2) * (Math.cos(i1) + Math.cos(i2)) * F;
    const dNorth = (dMD / 2) * (Math.sin(i1) * Math.cos(a1) + Math.sin(i2) * Math.cos(a2)) * F;
    const dEast = (dMD / 2) * (Math.sin(i1) * Math.sin(a1) + Math.sin(i2) * Math.sin(a2)) * F;

    curTvd += dTVD;
    curNorth += dNorth;
    curEast += dEast;

    // Dogleg severity in degrees per 100 ft (Eq. 8.5)
    const dls = ((beta * 180) / Math.PI / dMD) * 100;

    // Closure distance and azimuth
    const closureDist = Math.sqrt(Math.pow(curNorth, 2) + Math.pow(curEast, 2));
    let closureAzi = (Math.atan2(curEast, curNorth) * 180) / Math.PI;
    if (closureAzi < 0) closureAzi += 360;

    // Vertical section projected onto user target azimuth (or closure azimuth)
    const vsAziRad = ((verticalSectionAzimuthDeg !== undefined ? verticalSectionAzimuthDeg : closureAzi) * Math.PI) / 180;
    const vs = curNorth * Math.cos(vsAziRad) + curEast * Math.sin(vsAziRad);

    points.push({
      md: curr.measuredDepthFt,
      inc: curr.inclinationDeg,
      azi: curr.azimuthDeg,
      tvd: Math.round(curTvd * 10) / 10,
      north: Math.round(curNorth * 10) / 10,
      east: Math.round(curEast * 10) / 10,
      verticalSection: Math.round(vs * 10) / 10,
      doglegSeverityDeg100ft: Math.round(dls * 100) / 100,
      closureDistanceFt: Math.round(closureDist * 10) / 10,
      closureAzimuthDeg: Math.round(closureAzi * 10) / 10,
    });
  }

  return points;
}

/**
 * 8.2 Well Planning: Type I (Build and Hold Profile)
 * Sourced: Bourgoyne Ch. 8, Section 8.4, Eq. 8.7 - 8.12
 */
export interface TypeIPlanResult {
  radiusOfCurvatureFt: number;
  maxInclinationDeg: number;
  measuredDepthAtEOBFt: number;   // End of Build
  trueVerticalDepthAtEOBFt: number;
  totalMeasuredDepthFt: number;
  tangentLengthFt: number;
}

export function planTypeIWell(
  targetTvdFt: number,
  targetDisplacementFt: number,
  kickOffPointFt: number,
  buildRateDegPer100ft: number = 3.0
): TypeIPlanResult {
  const kop = kickOffPointFt;
  const tvd = targetTvdFt;
  const x = targetDisplacementFt;
  const q = buildRateDegPer100ft;

  // Radius of curvature R = 180 * 100 / (pi * q) (Eq. 8.7)
  const R = (18000) / (Math.PI * q);

  // Geometric relation: (tvd - kop - R * sin(theta)) * tan(theta) + R * (1 - cos(theta)) = x
  // Solving for maximum inclination angle theta:
  // tan(phi) = (tvd - kop) / (x - R)
  const numerator = tvd - kop;
  const denominator = x - R;
  const phi = Math.atan2(numerator, denominator);
  const hypotenuse = Math.sqrt(Math.pow(numerator, 2) + Math.pow(denominator, 2));

  let thetaRad = 0;
  if (hypotenuse >= R) {
    const alpha = Math.asin(R / hypotenuse);
    thetaRad = phi - alpha;
  } else {
    // If target cannot be reached with given R, use direct arc
    thetaRad = Math.atan2(x, tvd - kop);
  }

  const thetaDeg = Math.max(1, Math.min(85, (thetaRad * 180) / Math.PI));
  const radFinal = (thetaDeg * Math.PI) / 180;

  // TVD and MD at End of Build (EOB)
  const tvdEOB = kop + R * Math.sin(radFinal);
  const mdEOB = kop + (thetaDeg / q) * 100;

  // Tangent section length
  const tangentLength = (tvd - tvdEOB) / Math.cos(radFinal);
  const totalMD = mdEOB + Math.max(0, tangentLength);

  return {
    radiusOfCurvatureFt: Math.round(R),
    maxInclinationDeg: Math.round(thetaDeg * 10) / 10,
    measuredDepthAtEOBFt: Math.round(mdEOB),
    trueVerticalDepthAtEOBFt: Math.round(tvdEOB),
    totalMeasuredDepthFt: Math.round(totalMD),
    tangentLengthFt: Math.round(Math.max(0, tangentLength)),
  };
}
