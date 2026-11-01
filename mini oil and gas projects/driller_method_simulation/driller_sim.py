"""
Driller method simulation skeleton
Usage: python driller_sim.py
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def simulate(duration_hours=24, dt_min=1, initial_rop=10):
    steps = int(duration_hours * 60 / dt_min)
    times = np.arange(steps) * dt_min / 60.0
    rop = initial_rop * np.exp(-times/24.0)  # decay example
    md = np.cumsum(rop * dt_min/60.0)
    df = pd.DataFrame({'time_h': times, 'rop': rop, 'md': md})
    return df

if __name__ == '__main__':
    df = simulate(48, dt_min=10, initial_rop=12)
    print(df.tail())
    df.plot(x='time_h', y='md', title='MD vs time')
    df.plot(x='time_h', y='rop', title='ROP vs time')
    plt.show()
