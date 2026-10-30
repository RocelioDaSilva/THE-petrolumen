import { describe, it, expect } from 'vitest';
import { convert } from '../units';

describe('Unit Conversion Engine', () => {
  it('converts pressure accurately between psi, kPa, and bar', () => {
    // 1000 psi to kPa (1 psi = 6.89476 kPa)
    const kpa = convert(1000, 'psi', 'kPa');
    expect(kpa).toBeCloseTo(6894.76, 1);

    const psi = convert(kpa, 'kPa', 'psi');
    expect(psi).toBeCloseTo(1000, 1);

    const bar = convert(1000, 'psi', 'bar');
    expect(bar).toBeCloseTo(68.95, 1);
  });

  it('converts temperature accurately between F and C', () => {
    // 212 F is 100 C
    const boilC = convert(212, 'F', 'C');
    expect(boilC).toBeCloseTo(100, 2);

    // 32 F is 0 C
    const freezeC = convert(32, 'F', 'C');
    expect(freezeC).toBeCloseTo(0, 2);
  });

  it('converts flow rate between STB/d and m3/d', () => {
    const m3 = convert(1000, 'STB/d', 'm3/d');
    expect(m3).toBeCloseTo(158.987, 1);
  });

  it('converts length between ft and m', () => {
    const meters = convert(1000, 'ft', 'm');
    expect(meters).toBeCloseTo(304.8, 1);
  });
});
