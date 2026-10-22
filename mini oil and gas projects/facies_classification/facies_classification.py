"""
Facies classification - baseline with RandomForest
Usage: python facies_classification.py --data path/to/logs.csv
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import joblib
import argparse

def main(path):
    df = pd.read_csv(path)
    # expected columns: depth, gamma, resistivity, density, porosity, facies
    features = ['gamma','resistivity','density','porosity']
    X = df[features].fillna(df[features].median())
    y = df['facies']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    print(classification_report(y_test, preds))
    joblib.dump(clf, 'facies_rf.pkl')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    main(args.data)
