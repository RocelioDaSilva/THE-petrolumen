"""
Simple LAS reader and basic petrophysical computations
Usage: python las_reader.py --file data/example.las
"""
import lasio
import numpy as np
import pandas as pd
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    args = parser.parse_args()
    las = lasio.read(args.file)
    df = las.df()
    print(df.head())
    # Example: compute porosity from density log (rho_matrix=2.65, rho_fluid=1.0)
    if 'DEN' in df.columns:
        rho = df['DEN']
        phi = (2.65 - rho) / (2.65 - 1.0)
        df['porosity'] = phi
        print(df[['DEN','porosity']].head())
    df.to_csv('las_export.csv')
