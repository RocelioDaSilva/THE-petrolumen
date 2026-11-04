"""Plotting helpers."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def plot_ipr_vogel(qmax, pbar, ax=None):
    from .ch03_ipr import vogel_pwf
    if ax is None:
        fig, ax = plt.subplots()
    q = np.linspace(0, qmax, 100)
    pwf = [vogel_pwf(qi, qmax, pbar) for qi in q]
    ax.plot(q, pwf, 'b-', lw=1.5)
    ax.set_xlabel("q (stb/day)"); ax.set_ylabel("p_wf (psia)")
    ax.set_title("Vogel IPR"); ax.grid(True, alpha=0.3)
    return ax

def plot_decline_model(model, qi, b, t_max=120, a=1.5, ax=None):
    from .ch08_decline import (exponential_rate, harmonic_rate,
                                hyperbolic_rate)
    if ax is None:
        fig, ax = plt.subplots()
    t = np.linspace(0, t_max, 200)
    if model == "exponential":
        q = [exponential_rate(qi, b, x) for x in t]
    elif model == "harmonic":
        q = [harmonic_rate(qi, b, x) for x in t]
    else:
        q = [hyperbolic_rate(qi, a, b, x) for x in t]
    ax.plot(t, q, 'b-', lw=1.5)
    ax.set_xlabel("Time"); ax.set_ylabel("q")
    ax.set_title(f"{model.capitalize()} decline")
    ax.grid(True, alpha=0.3)
    return ax

def plot_tpr_traverse(traverse, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(traverse[:, 1], traverse[:, 0], 'b-', lw=1.5)
    ax.invert_yaxis()
    ax.set_xlabel("Pressure (psia)"); ax.set_ylabel("Depth (ft)")
    ax.grid(True, alpha=0.3)
    return ax

def plot_nodal(ipr_q, ipr_p, tpr_q, tpr_p, op_q=None, op_p=None,
                ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(ipr_q, ipr_p, 'b-', label="IPR", lw=1.5)
    ax.plot(tpr_q, tpr_p, 'r--', label="TPR", lw=1.5)
    if op_q is not None and op_p is not None:
        ax.plot(op_q, op_p, 'ko', markersize=8)
    ax.set_xlabel("Rate (stb/day)"); ax.set_ylabel("p_wf (psia)")
    ax.legend(); ax.grid(True, alpha=0.3)
    return ax
