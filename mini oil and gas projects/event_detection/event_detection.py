"""
Simple event detection using rolling z-score and IsolationForest
Usage: python event_detection.py --data data.csv
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import argparse


def detect_zscore(df, col, window=50, thresh=4.0):
    roll = df[col].rolling(window, min_periods=1, center=True).median()
    z = (df[col] - roll) / (df[col].rolling(window, min_periods=1).std().replace(0, np.nan))
    return df.index[np.abs(z) > thresh]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.data, parse_dates=[0], index_col=0)

    anomalies = detect_zscore(df, 'pressure', window=100, thresh=5.0)
    print('Anomaly timestamps (z-score):')
    print(anomalies)

    clf = IsolationForest(contamination=0.01, random_state=42)
    clf.fit(df.fillna(method='ffill'))
    preds = clf.predict(df.fillna(method='ffill'))
    df['anomaly_if'] = preds == -1
    print(df[df['anomaly_if']].head())
