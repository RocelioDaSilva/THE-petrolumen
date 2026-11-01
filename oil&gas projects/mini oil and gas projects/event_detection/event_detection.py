"""
Simple event detection using rolling z-score and IsolationForest
Usage: python event_detection.py --data data.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import argparse

from app.engines.analytics.event_detection import detect_zscore

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.data, parse_dates=[0], index_col=0)

    anomalies = detect_zscore(df, 'pressure', window=100, thresh=5.0)
    print('Anomaly timestamps (z-score):')
    print(anomalies)

    clf = IsolationForest(contamination=0.01, random_state=42)
    # Compatible with pandas >= 2.0 (ffill())
    df_filled = df.ffill()
    clf.fit(df_filled)
    preds = clf.predict(df_filled)
    df['anomaly_if'] = preds == -1
    print(df[df['anomaly_if']].head())
