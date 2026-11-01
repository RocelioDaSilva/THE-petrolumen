"""
Driller method simulation script
Usage: python driller_sim.py
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from app.engines.drilling.driller_sim import simulate_driller_method

# Expose simulate for backwards compatibility
simulate = simulate_driller_method

if __name__ == '__main__':
    df = simulate_driller_method(duration_hours=48, dt_min=10, initial_rop=12)
    print(df.tail())
    if plt is not None:
        df.plot(x='time_h', y='md', title='MD vs time')
        df.plot(x='time_h', y='rop', title='ROP vs time')
        plt.show()
