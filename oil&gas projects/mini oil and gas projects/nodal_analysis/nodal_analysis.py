"""
Nodal analysis script
Usage: python nodal_analysis.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import numpy as np
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from app.engines.reservoir.nodal import ipr_vogel, tpr, find_operating_point

if __name__ == '__main__':
    # parâmetros de exemplo
    qi = 5000
    pr = 3000
    p_surf = 1000

    try:
        q_op = find_operating_point(qi=qi, pr=pr, p_surf=p_surf)
        print('Ponto de operação (q):', q_op)

        if plt is not None:
            qs = np.linspace(0, qi, 200)
            ipr_vals = [ipr_vogel(q, qi, pr, pr - tpr(q)) for q in qs]
            tpr_vals = [q for q in qs]

            plt.plot(qs, ipr_vals, label='IPR (f(pwf))')
            plt.plot(qs, tpr_vals, label='Vazão (q)')
            plt.axvline(q_op, color='k', linestyle='--', label=f'q_op={q_op:.1f}')
            plt.legend()
            plt.xlabel('q (bbl/day)')
            plt.ylabel('Taxa / função')
            plt.show()
    except Exception as e:
        print('Falha ao encontrar ponto de operação:', e)
