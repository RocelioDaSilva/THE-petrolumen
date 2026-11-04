"""Matplotlib helpers reproducing book figures."""
from __future__ import annotations
import matplotlib.pyplot as plt
import numpy as np


def plot_ipr_vogel(qmax: float, pbar: float, ax=None):
    """Reproduce Fig. 3.5 / 3.9 / 3.11."""
    from .ch03_ipr import vogel_pwf
    if ax is None:
        _, ax = plt.subplots()
    q = np.linspace(0, qmax, 100)
    pwf = [vogel_pwf(qi, qmax, pbar) for qi in q]
    ax.plot(q, pwf, 'b-', lw=1.5)
    ax.set_xlabel("q (stb/day)")
    ax.set_ylabel("p_wf (psia)")
    ax.set_title("Vogel IPR")
    ax.grid(True, alpha=0.3)
    return ax


def plot_decline_model(model, qi, b, t_max=120, a=1.5, ax=None):
    """Reproduce Figs. 8.7â€“8.14."""
    from .ch08_decline import (exponential_rate, harmonic_rate,
                                hyperbolic_rate)
    if ax is None:
        _, ax = plt.subplots()
    t = np.linspace(0, t_max, 200)
    if model == "exponential":
        q = [exponential_rate(qi, b, x) for x in t]
    elif model == "harmonic":
        q = [harmonic_rate(qi, b, x) for x in t]
    else:
        q = [hyperbolic_rate(qi, a, b, x) for x in t]
    ax.plot(t, q, 'b-', lw=1.5)
    ax.set_xlabel("Time")
    ax.set_ylabel("q")
    ax.set_title(f"{model.capitalize()} decline")
    ax.grid(True, alpha=0.3)
    return ax