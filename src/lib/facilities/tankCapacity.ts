/**
 * Tank Capacity Engine
 * Sourced from Carter, Lyons & Lapeyrouse (5th Ed., 2023), Appendix A.
 */

export function rectangularTankCapacity(
  lengthFt: number,
  widthFt: number,
  heightFt: number,
  partialFluidHeightFt?: number
): { totalBbl: number; partialBbl: number } {
  const totalFt3 = lengthFt * widthFt * heightFt;
  const totalBbl = totalFt3 * 0.1781;
  const hPart = partialFluidHeightFt !== undefined ? Math.min(heightFt, partialFluidHeightFt) : heightFt;
  const partialBbl = lengthFt * widthFt * hPart * 0.1781;
  return {
    totalBbl: Math.round(totalBbl * 10) / 10,
    partialBbl: Math.round(partialBbl * 10) / 10,
  };
}

export function slopingRectangularTankCapacity(
  lengthFt: number,
  widthFt: number,
  heightDeepFt: number,
  heightShallowFt: number
): { totalBbl: number } {
  const avgHeight = (heightDeepFt + heightShallowFt) / 2;
  const totalBbl = lengthFt * widthFt * avgHeight * 0.1781;
  return { totalBbl: Math.round(totalBbl * 10) / 10 };
}

export function horizontalCylindricalTankCapacity(
  diameterFt: number,
  lengthFt: number,
  fluidDepthFt?: number
): { totalBbl: number; partialBbl: number } {
  const r = diameterFt / 2;
  const totalBbl = Math.PI * Math.pow(r, 2) * lengthFt * 0.1781;
  let partialBbl = totalBbl;
  if (fluidDepthFt !== undefined && fluidDepthFt < diameterFt) {
    const h = fluidDepthFt;
    const alpha = 2 * Math.acos((r - h) / r);
    const area = 0.5 * Math.pow(r, 2) * (alpha - Math.sin(alpha));
    partialBbl = area * lengthFt * 0.1781;
  }
  return {
    totalBbl: Math.round(totalBbl * 10) / 10,
    partialBbl: Math.round(partialBbl * 10) / 10,
  };
}

export function verticalCylindricalTankCapacity(
  diameterFt: number,
  heightFt: number,
  fluidDepthFt?: number
): { totalBbl: number; partialBbl: number } {
  const r = diameterFt / 2;
  const totalBbl = Math.PI * Math.pow(r, 2) * heightFt * 0.1781;
  const hPart = fluidDepthFt !== undefined ? Math.min(heightFt, fluidDepthFt) : heightFt;
  const partialBbl = Math.PI * Math.pow(r, 2) * hPart * 0.1781;
  return {
    totalBbl: Math.round(totalBbl * 10) / 10,
    partialBbl: Math.round(partialBbl * 10) / 10,
  };
}

export function taperedVerticalTankCapacity(
  bottomDiameterFt: number,
  topDiameterFt: number,
  heightFt: number
): { totalBbl: number } {
  const r1 = bottomDiameterFt / 2;
  const r2 = topDiameterFt / 2;
  const totalFt3 = (Math.PI * heightFt / 3) * (Math.pow(r1, 2) + Math.pow(r2, 2) + r1 * r2);
  const totalBbl = totalFt3 * 0.1781;
  return { totalBbl: Math.round(totalBbl * 10) / 10 };
}
