"""
Compute wellbore coordinates from MD/INC/AZI and plot 3D
Usage: python trajectory.py --data survey.csv
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import argparse

def deg2rad(d):
    return d * np.pi / 180.0

def min_curvature(md, inc, azi):
    # md, inc, azi arrays
    x = [0.0]
    y = [0.0]
    z = [0.0]
    for i in range(1, len(md)):
        md1, md0 = md[i], md[i-1]
        inc1, inc0 = deg2rad(inc[i]), deg2rad(inc[i-1])
        azi1, azi0 = deg2rad(azi[i]), deg2rad(azi[i-1])
        d_md = md1 - md0
        theta = np.arccos(np.cos(inc0)*np.cos(inc1) + np.sin(inc0)*np.sin(inc1)*np.cos(azi1-azi0))
        if abs(theta) < 1e-6:
            rf = 1.0
        else:
            rf = 2.0/theta * np.tan(theta/2.0)
        dx = d_md/2.0 * (np.sin(inc0)*np.cos(azi0) + np.sin(inc1)*np.cos(azi1)) * rf
        dy = d_md/2.0 * (np.sin(inc0)*np.sin(azi0) + np.sin(inc1)*np.sin(azi1)) * rf
        dz = d_md/2.0 * (np.cos(inc0) + np.cos(inc1)) * rf
        x.append(x[-1] + dx)
        y.append(y[-1] + dy)
        z.append(z[-1] + dz)
    return np.array(x), np.array(y), np.array(z)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    x,y,z = min_curvature(df['md'].to_numpy(), df['inc'].to_numpy(), df['azi'].to_numpy())

    fig = go.Figure(data=[go.Scatter3d(x=x, y=y, z=-z, mode='lines+markers')])
    fig.update_layout(scene=dict(xaxis_title='X (m)', yaxis_title='Y (m)', zaxis_title='TVD (m)'))
    fig.show()
