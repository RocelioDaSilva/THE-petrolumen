"""
ECD calculator script
Usage: python ecd_calc.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.engines.drilling.ecd import pressure_from_density, hydrostatic_pressure_bar

if __name__ == '__main__':
    rho = 1200  # kg/m3
    depth = 3000  # m
    p = pressure_from_density(rho, depth)
    p_bar = hydrostatic_pressure_bar(rho, depth)
    print(f'Pressure (Pa): {p:.2e}, Pressure (bar): {p_bar:.2f}')
