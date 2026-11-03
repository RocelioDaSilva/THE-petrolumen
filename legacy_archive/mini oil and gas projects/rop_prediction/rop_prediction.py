"""
ROP prediction skeleton using XGBoost / RandomForest
Usage: python rop_prediction.py --data data.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import argparse
import pandas as pd
from app.engines.drilling.rop import train_rop_model


def main(path: str) -> None:
    df = pd.read_csv(path)
    features = ['WOB', 'RPM', 'torque', 'mud_weight']
    model, metrics, _ = train_rop_model(df, features=features, target_col='ROP')
    print('Metrics:', metrics)
    if hasattr(model, 'save_model'):
        model.save_model('rop_xgb.json')
        print("Saved XGBoost model to rop_xgb.json")
    else:
        import joblib
        joblib.dump(model, 'rop_rf.pkl')
        print("Saved model to rop_rf.pkl")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    main(args.data)
