export type UnitSystem = 'field' | 'metric';

export const convert = (value: number, from: string, to: string): number => {
  if (from === to || !Number.isFinite(value)) return value;

  // Pressure
  if ((from === 'psi' || from === 'psia') && to === 'kPa') return value * 6.89476;
  if (from === 'kPa' && (to === 'psi' || to === 'psia')) return value / 6.89476;
  if ((from === 'psi' || from === 'psia') && to === 'bar') return value * 0.0689476;
  if (from === 'bar' && (to === 'psi' || to === 'psia')) return value / 0.0689476;
  if ((from === 'psi' || from === 'psia') && to === 'MPa') return value * 0.00689476;
  if (from === 'MPa' && (to === 'psi' || to === 'psia')) return value / 0.00689476;

  // Temperature
  if (from === 'F' && to === 'C') return ((value - 32) * 5) / 9;
  if (from === 'C' && to === 'F') return (value * 9) / 5 + 32;

  // Flow rate
  if ((from === 'STB/d' || from === 'bbl/day' || from === 'bbl/d') && (to === 'm3/d' || to === 'm3/day')) return value * 0.1589873;
  if ((from === 'm3/d' || from === 'm3/day') && (to === 'STB/d' || to === 'bbl/day' || to === 'bbl/d')) return value / 0.1589873;
  if (from === 'Mscf/d' && (to === 'm3/d' || to === 'm3/day')) return value * 28.3168;

  // Volume
  if (from === 'bbl' && to === 'm3') return value * 0.1589873;
  if (from === 'm3' && to === 'bbl') return value / 0.1589873;
  if (from === 'scf' && to === 'm3') return value * 0.0283168;
  if (from === 'm3' && to === 'scf') return value / 0.0283168;

  // Length
  if (from === 'ft' && to === 'm') return value * 0.3048;
  if (from === 'm' && to === 'ft') return value / 0.3048;
  if (from === 'in' && to === 'mm') return value * 25.4;
  if (from === 'mm' && to === 'in') return value / 25.4;

  // Density
  if ((from === 'lb/gal' || from === 'ppg') && (to === 'kg/m3' || to === 'kg/m²')) return value * 119.826;
  if ((to === 'lb/gal' || to === 'ppg') && (from === 'kg/m3' || from === 'kg/m²')) return value / 119.826;
  if ((from === 'lb/gal' || from === 'ppg') && to === 'g/cm3') return value * 0.119826;
  if (from === 'g/cm3' && (to === 'lb/gal' || to === 'ppg')) return value / 0.119826;

  // Viscosity (1 cP = 1 mPa·s)
  if (from === 'cP' && to === 'mPa·s') return value;
  if (from === 'mPa·s' && to === 'cP') return value;

  // Permeability (mD to m²)
  if (from === 'mD' && to === 'm2') return value * 9.869233e-16;
  if (from === 'm2' && to === 'mD') return value / 9.869233e-16;

  return value;
};
