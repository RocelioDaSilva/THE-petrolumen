"""Chapter 8 -- Production Decline Analysis."""
import math
import numpy as np

def exponential_rate(qi, b, t): return qi*math.exp(-b*t)
def exponential_cum(qi, b, t): return (qi/b)*(1 - math.exp(-b*t))
def exponential_b_from_ln(q1, q2, t1, t2):
    return math.log(q1/q2)/(t2 - t1)
def exponential_b_from_np(q1, q2, np1, np2):
    return (q1 - q2)/(np2 - np1)
def harmonic_rate(q0, b, t): return q0/(1 + b*t)
def harmonic_cum(q0, b, t): return (q0/b)*math.log(1 + b*t)
def hyperbolic_rate(q0, a, b, t): return q0/(1 + (b/a)*t)**a
def hyperbolic_cum(q0, a, b, t):
    return (a*q0/(b*(a-1)))*(1 - (1 + (b/a)*t)**(1-a))

def identify_model(t, q) -> str:
    q = np.asarray(q, dtype=float)
    t = np.asarray(t, dtype=float)
    mask = (q > 0) & (t > 0)
    t, q = t[mask], q[mask]
    if len(t) < 5: return "unknown"
    def r2(yf, yt):
        sr = np.sum((yt - yf)**2)
        st = np.sum((yt - yt.mean())**2)
        return 1 - sr/st if st > 0 else 0
    lq = np.log(q); pe = np.polyfit(t, lq, 1)
    r2e = r2(np.polyval(pe, t), lq)
    rel = -np.gradient(q, t)/q
    if np.std(rel)/max(np.mean(rel), 1e-9) < 0.15:
        return "exponential"
    if r2e > 0.98: return "exponential"
    return "hyperbolic"
