"""
Wrapper to read LAS or CSV for petrophysical analysis
Usage: python run_petrophysical.py --file data/example_logs.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import argparse
import os

try:
    import lasio
except Exception:
    lasio = None

import pandas as pd
from app.engines.petrophysics.porosity import calculate_density_porosity


def process_csv(path):
    df = pd.read_csv(path)
    print(df.head())
    if 'DEN' in df.columns:
        df['porosity'] = calculate_density_porosity(df['DEN'])
        print(df[['DEN','porosity']].head())
    out = 'las_export.csv'
    df.to_csv(out, index=False)
    print(f'Exported to {out}')


def process_las(path):
    if lasio is None:
        raise RuntimeError('lasio not installed. Install with `pip install lasio`')
    las = lasio.read(path)
    df = las.df()
    print(df.head())
    if 'DEN' in df.columns:
        df['porosity'] = calculate_density_porosity(df['DEN'])
        print(df[['DEN','porosity']].head())
    out = 'las_export.csv'
    df.to_csv(out)
    print(f'Exported to {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    path = args.file
    if path.lower().endswith('.csv'):
        process_csv(path)
    else:
        process_las(path)
