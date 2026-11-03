"""
Simple LAS reader and basic petrophysical computations
Usage: python las_reader.py --file data/example.las
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import lasio
import numpy as np
import pandas as pd
import argparse

from app.engines.petrophysics.porosity import calculate_density_porosity

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    las = lasio.read(args.file)
    df = las.df()
    print(df.head())
    # Compute porosity from density log (rho_matrix=2.65, rho_fluid=1.0)
    if 'DEN' in df.columns:
        df['porosity'] = calculate_density_porosity(df['DEN'])
        print(df[['DEN','porosity']].head())
    df.to_csv('las_export.csv')
