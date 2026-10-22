"""
ROP prediction skeleton using XGBoost
Usage: python rop_prediction.py --data data.csv
"""

import pandas as pd
import argparse
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


def main(path):
    df = pd.read_csv(path)
    # basic features example
    features = ['WOB','RPM','torque','mud_weight']
    df = df.fillna(method='ffill')
    X = df[features]
    y = df['ROP']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    print('RMSE:', mean_squared_error(y_test, preds, squared=False))
    model.save_model('rop_xgb.json')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    main(args.data)
