/**
 * Numerical Solvers & Root-Finding Algorithms
 * Sourced from Bourgoyne et al., "Applied Drilling Engineering" (SPE, 1986).
 * Used for Colebrook friction factors, gas-cut mud integration, particle slip velocities,
 * and iterative pressure schedules.
 */

export interface RootFindOptions {
  maxIterations?: number;
  tolerance?: number;
}

/**
 * Robust Bisection + Secant root finder (Brent-inspired bracketed solver)
 * Solves f(x) = 0 on [a, b] where f(a) * f(b) <= 0.
 */
export function findRootBrent(
  f: (x: number) => number,
  a: number,
  b: number,
  options: RootFindOptions = {}
): number {
  const maxIter = options.maxIterations ?? 100;
  const tol = options.tolerance ?? 1e-7;

  let fa = f(a);
  let fb = f(b);

  if (Math.abs(fa) < tol) return a;
  if (Math.abs(fb) < tol) return b;

  if (fa * fb > 0) {
    // If not bracketed, perform an intelligent expansion search
    let step = (b - a) / 10;
    let found = false;
    for (let i = 0; i < 20; i++) {
      const mid = a + i * step;
      const fmid = f(mid);
      if (fa * fmid <= 0) {
        b = mid;
        fb = fmid;
        found = true;
        break;
      }
    }
    if (!found) {
      // Fallback: return midpoint if unable to bracket
      return (a + b) / 2;
    }
  }

  let c = a;
  let fc = fa;
  let d = b - a;
  let e = d;

  for (let iter = 0; iter < maxIter; iter++) {
    if (fb * fc > 0) {
      c = a;
      fc = fa;
      d = b - a;
      e = d;
    }

    if (Math.abs(fc) < Math.abs(fb)) {
      a = b;
      b = c;
      c = a;
      fa = fb;
      fb = fc;
      fc = fa;
    }

    const m = 0.5 * (c - b);
    const toler = 2 * 1e-12 * Math.max(Math.abs(b), 1) + 0.5 * tol;

    if (Math.abs(m) <= toler || Math.abs(fb) < tol) {
      return b;
    }

    if (Math.abs(e) >= toler && Math.abs(fa) > Math.abs(fb)) {
      let s = fb / fa;
      let p: number;
      let q: number;

      if (a === c) {
        // Secant method
        p = 2 * m * s;
        q = 1 - s;
      } else {
        // Inverse quadratic interpolation
        q = fa / fc;
        const r = fb / fc;
        p = s * (2 * m * q * (q - r) - (b - a) * (r - 1));
        q = (q - 1) * (r - 1) * (s - 1);
      }

      if (p > 0) q = -q;
      p = Math.abs(p);

      if (2 * p < Math.min(3 * m * q - Math.abs(toler * q), Math.abs(e * q))) {
        e = d;
        d = p / q;
      } else {
        d = m;
        e = d;
      }
    } else {
      d = m;
      e = d;
    }

    a = b;
    fa = fb;

    if (Math.abs(d) > toler) {
      b += d;
    } else {
      b += m > 0 ? toler : -toler;
    }
    fb = f(b);
  }

  return b;
}

/**
 * Newton-Raphson iterative solver with analytical or numerical derivative
 */
export function newtonRaphson(
  f: (x: number) => number,
  df?: (x: number) => number,
  x0: number = 0.02,
  options: RootFindOptions = {}
): number {
  const maxIter = options.maxIterations ?? 50;
  const tol = options.tolerance ?? 1e-7;
  let x = x0;

  for (let i = 0; i < maxIter; i++) {
    const fx = f(x);
    if (Math.abs(fx) < tol) return x;

    const derivative = df ? df(x) : (f(x + 1e-6) - f(x - 1e-6)) / 2e-6;
    if (Math.abs(derivative) < 1e-14) break;

    const step = fx / derivative;
    x -= step;
    if (Math.abs(step) < tol) return x;
  }
  return x;
}

/**
 * Two-point Power Law rheology parameter fit for arbitrary rotational viscometer speeds
 * Given (N1, theta1) and (N2, theta2):
 * n = log(theta2 / theta1) / log(N2 / N1)
 * K = 510 * theta / (1.703 * N)^n
 * Sourced: Bourgoyne Ch. 2, Eq. 2.4-2.5
 */
export function fitPowerLaw(
  n1Rpm: number,
  theta1: number,
  n2Rpm: number,
  theta2: number
): { n: number; K: number } {
  if (n1Rpm <= 0 || n2Rpm <= 0 || theta1 <= 0 || theta2 <= 0) {
    return { n: 1.0, K: 0 };
  }
  const n = Math.log(theta2 / theta1) / Math.log(n2Rpm / n1Rpm);
  // Shear rate gamma_dot = 1.703 * RPM (sec^-1)
  // Shear stress tau = 5.11 * theta (dynes/cm^2) = 1.066 * theta (lbf/100ft^2)
  // Consistency index K in equivalent cP:
  const gamma1 = 1.7033 * n1Rpm;
  const K = (510 * theta1) / Math.pow(gamma1, n);

  return {
    n: Math.round(n * 1000) / 1000,
    K: Math.round(K * 10) / 10,
  };
}

/**
 * Numerical Integration (Simpson's 1/3 Rule)
 */
export function integrateSimpsons(
  f: (x: number) => number,
  a: number,
  b: number,
  intervals: number = 20
): number {
  const n = intervals % 2 === 0 ? intervals : intervals + 1;
  const h = (b - a) / n;
  let sum = f(a) + f(b);

  for (let i = 1; i < n; i++) {
    const x = a + i * h;
    sum += i % 2 === 0 ? 2 * f(x) : 4 * f(x);
  }

  return (h / 3) * sum;
}
