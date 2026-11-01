"""
Compute wellbore coordinates from MD/INC/AZI and plot 3D
Usage: python trajectory.py --data survey.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import argparse

from app.utils.math_utils import deg2rad, min_curvature
from app.engines.drilling.trajectory import compute_trajectory_minimum_curvature

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    x, y, z = min_curvature(df['md'].to_numpy(), df['inc'].to_numpy(), df['azi'].to_numpy())

    fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=-np.array(z), mode='lines+markers')])
    fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='TVD (m)'))
    fig.show()
