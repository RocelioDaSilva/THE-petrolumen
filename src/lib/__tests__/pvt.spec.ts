import { describe, it, expect } from 'vitest';
import {
  calculateZFactor,
  calculatePVT,
  getPseudoCriticalProps,
} from '../reservoirMath';

describe('PVT Engineering Calculations', () => {
  it('calculates realistic gas compressibility Z-factor', () => {
    // Typical reservoir condition: P = 3000 psia, T = 180 degF, SG = 0.65
    const z = calculateZFactor(3000, 180, 0.65);
    expect(z).toBeGreaterThan(0.7);
    expect(z).toBeLessThan(1.0);
  });

  it('calculates pseudo-critical properties correctly (Sutton)', () => {
    const { Ppc, Tpc } = getPseudoCriticalProps(0.65);
    expect(Ppc).toBeCloseTo(670, 0);
    expect(Tpc).toBeCloseTo(365, 0);
  });

  it('calculates comprehensive PVT properties within physical limits', () => {
    const results = calculatePVT({
      pressure: 2500,
      temperature: 160,
      gammaG: 0.7,
      api: 32,
      gor: 450,
    });

    expect(results.zFactor).toBeGreaterThan(0.7);
    expect(results.zFactor).toBeLessThan(1.0);
    expect(results.bo).toBeGreaterThan(1.1);
    expect(results.bo).toBeLessThan(1.8);
    expect(results.bg).toBeGreaterThan(0.005);
    expect(results.oilViscosity).toBeGreaterThan(0.1);
    expect(results.oilViscosity).toBeLessThan(50);
  });
});
