"""
Facies classification - baseline with RandomForest
Usage: python facies_classification.py --data path/to/logs.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[3] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import argparse
import joblib
import pandas as pd
from app.engines.petrophysics.facies import train_facies_classifier


def main(path: str) -> None:
    df = pd.read_csv(path)
    features = ['gamma', 'resistivity', 'density', 'porosity']
    clf, report, _ = train_facies_classifier(df, features=features, target_col='facies')
    print("Classification Report:")
    for label, metrics in report.items():
        if isinstance(metrics, dict):
            print(f"  Class {label}: precision={metrics.get('precision', 0):.2f}, recall={metrics.get('recall', 0):.2f}")
    joblib.dump(clf, 'facies_rf.pkl')
    print("Saved model to facies_rf.pkl")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    main(args.data)
