/**
 * Directional Drilling Engine (Carter v3)
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Chapter 7.
 */

export function angleAveragingSurvey(
  md1Ft: number,
  inc1Deg: number,
  az1Deg: number,
  md2Ft: number,
  inc2Deg: number,
  az2Deg: number
): { dNorthFt: number; dEastFt: number; dTvdFt: number } {
  const deltaMd = md2Ft - md1Ft;
  const avgIncRad = (((inc1Deg + inc2Deg) / 2) * Math.PI) / 180;
  const avgAzRad = (((az1Deg + az2Deg) / 2) * Math.PI) / 180;

  const dN = deltaMd * Math.sin(avgIncRad) * Math.cos(avgAzRad);
  const dE = deltaMd * Math.sin(avgIncRad) * Math.sin(avgAzRad);
  const dV = deltaMd * Math.cos(avgIncRad);

  return {
    dNorthFt: Math.round(dN * 10) / 10,
    dEastFt: Math.round(dE * 10) / 10,
    dTvdFt: Math.round(dV * 10) / 10,
  };
}

export function radiusOfCurvatureSurvey(
  md1Ft: number,
  inc1Deg: number,
  az1Deg: number,
  md2Ft: number,
  inc2Deg: number,
  az2Deg: number
): { dNorthFt: number; dEastFt: number; dTvdFt: number } {
  const deltaMd = md2Ft - md1Ft;
  const I1 = (inc1Deg * Math.PI) / 180;
  const I2 = (inc2Deg * Math.PI) / 180;
  const A1 = (az1Deg * Math.PI) / 180;
  const A2 = (az2Deg * Math.PI) / 180;

  const dI = I2 - I1;
  const dA = A2 - A1;

  if (Math.abs(dI) < 1e-4 && Math.abs(dA) < 1e-4) {
    return angleAveragingSurvey(md1Ft, inc1Deg, az1Deg, md2Ft, inc2Deg, az2Deg);
  }

  const fcI = Math.abs(dI) > 1e-4 ? (Math.cos(I1) - Math.cos(I2)) / dI : Math.sin(I1);
  const fcA = Math.abs(dA) > 1e-4 ? (Math.sin(A2) - Math.sin(A1)) / dA : Math.cos(A1);

  const dV = Math.abs(dI) > 1e-4 ? (deltaMd * (Math.sin(I2) - Math.sin(I1))) / dI : deltaMd * Math.cos(I1);
  const dN = deltaMd * fcI * fcA;
  const dE = Math.abs(dA) > 1e-4 ? (deltaMd * fcI * (Math.cos(A1) - Math.cos(A2))) / dA : deltaMd * fcI * Math.sin(A1);

  return {
    dNorthFt: Math.round(dN * 10) / 10,
    dEastFt: Math.round(dE * 10) / 10,
    dTvdFt: Math.round(dV * 10) / 10,
  };
}

export function doglegSeverity(
  inc1Deg: number,
  az1Deg: number,
  inc2Deg: number,
  az2Deg: number,
  deltaMdFt: number
): { dlsDegPer100Ft: number } {
  const I1 = (inc1Deg * Math.PI) / 180;
  const I2 = (inc2Deg * Math.PI) / 180;
  const dA = ((az2Deg - az1Deg) * Math.PI) / 180;

  const cosDogleg = Math.cos(I1) * Math.cos(I2) + Math.sin(I1) * Math.sin(I2) * Math.cos(dA);
  const doglegRad = Math.acos(Math.max(-1, Math.min(1, cosDogleg)));
  const doglegDeg = (doglegRad * 180) / Math.PI;

  const dls = deltaMdFt > 0 ? (doglegDeg / deltaMdFt) * 100 : 0;
  return { dlsDegPer100Ft: Math.round(dls * 10) / 10 };
}

export function availableWOB(
  wCollarsLbFt: number,
  lengthCollarsFt: number,
  inclinationDeg: number,
  mwPpg: number,
  safetyFactor: number = 0.85
): number {
  const bf = (65.5 - mwPpg) / 65.5;
  const incRad = (inclinationDeg * Math.PI) / 180;
  const wob = wCollarsLbFt * lengthCollarsFt * bf * Math.cos(incRad) * safetyFactor;
  return Math.round(wob);
}

export function tvdApproximation(mdFt: number, inclinationDeg: number): number {
  const incRad = (inclinationDeg * Math.PI) / 180;
  return Math.round(mdFt * Math.cos(incRad));
}
