export type UnitSystem = 'field' | 'metric';

export const convert = (value: number, from: string, to: string): number => {
  if (from === to) return value;
  // Pressure
  if (from === 'psi' && to === 'kPa') return value * 6.89476;
  if (from === 'kPa' && to === 'psi') return value / 6.89476;
  if (from === 'psi' && to === 'bar') return value * 0.0689476;
  if (from === 'bar' && to === 'psi') return value / 0.0689476;

  // Temperature
  if (from === 'F' && to === 'C') return ((value - 32) * 5) / 9;
  if (from === 'C' && to === 'F') return (value * 9) / 5 + 32;

  // Flow rate
  if (from === 'STB/d' && to === 'm3/d') return value * 0.158987;
  if (from === 'm3/d' && to === 'STB/d') return value / 0.158987;
  if (from === 'Mscf/d' && to === 'm3/d') return value * 28.3168;

  // Volume
  if (from === 'bbl' && to === 'm3') return value * 0.158987;
  if (from === 'm3' && to === 'bbl') return value / 0.158987;
  if (from === 'scf' && to === 'm3') return value * 0.0283168;

  // Length
  if (from === 'ft' && to === 'm') return value * 0.3048;
  if (from === 'm' && to === 'ft') return value / 0.3048;

  return value;
};
