export type UnitSystem = 'field' | 'metric';

export const convert = (value: number, from: string, to: string): number => {
  if (from === 'psi' && to === 'kPa') return value * 6.89476;
  if (from === 'kPa' && to === 'psi') return value / 6.89476;
  if (from === 'F' && to === 'C') return (value - 32) * 5/9;
  if (from === 'C' && to === 'F') return (value * 9/5) + 32;
  return value;
};
