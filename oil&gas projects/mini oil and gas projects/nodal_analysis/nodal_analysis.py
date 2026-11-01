"""
Nodal analysis skeleton
Usage: python nodal_analysis.py
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

# Exemplo simplificado de IPR (Vogel) para poços com vazão de óleo mecanicamente limitado
def ipr_vogel(q, qi, pr, pwf):
    # esta é uma aproximação demonstrativa
    # Vogel (para reservatórios saturados de óleo): q/q_max = 1 - 0.2*(pwf/pr) - 0.8*(pwf/pr)**2
    # inverter para q = f(pwf) é normalmente necessário; aqui usamos forma simplificada
    return qi * (1 - 0.2 * (pwf / pr) - 0.8 * (pwf / pr) ** 2)

# TPR (tubing performance) como função de q: perda de carga > função quadrática
def tpr(q, a=0.002, b=10):
    # P_surf + perda = P_wf ; usamos uma forma simples P_drop = a*q^2 + b*q
    return a * q ** 2 + b * q

if __name__ == '__main__':
    # parâmetros de exemplo
    qi = 5000
    pr = 3000
    p_surf = 1000

    # encontrar q tal que ipr_vogel(q) - (pr - tpr(q)) = 0 (ponto de equilíbrio)
    def residual(q):
        pwf = pr - tpr(q)
        return ipr_vogel(q, qi, pr, pwf) - q

    try:
        q_op = brentq(residual, 1, qi)
        print('Ponto de operação (q):', q_op)

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
