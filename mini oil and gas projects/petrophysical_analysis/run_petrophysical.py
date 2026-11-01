"""
Wrapper to read LAS or CSV for petrophysical analysis
Usage: python run_petrophysical.py --file data/example_logs.csv
"""
import argparse
import os

try:
    import lasio
except Exception:
    lasio = None

import pandas as pd


def process_csv(path):
    df = pd.read_csv(path)
    print(df.head())
    if 'DEN' in df.columns:
        rho = df['DEN']
        phi = (2.65 - rho) / (2.65 - 1.0)
        df['porosity'] = phi
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
        rho = df['DEN']
        phi = (2.65 - rho) / (2.65 - 1.0)
        df['porosity'] = phi
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
