"""
Train a simple sequence model for production forecasting
Usage: python train_lstm.py --data production.csv
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so app modules are resolvable
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import argparse
import numpy as np
import pandas as pd
from app.engines.analytics.sequences import create_sequences, normalize_timeseries


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    parser.add_argument('--window', type=int, default=6)
    args = parser.parse_args()

    df = pd.read_csv(args.data, parse_dates=[0])
    raw_prod = df['production'].to_numpy()

    arr, mean_val, std_val = normalize_timeseries(raw_prod)
    X, y = create_sequences(arr, window=args.window)
    print(f"Generated sequence dataset: X shape = {X.shape}, y shape = {y.shape}")

    try:
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense

        X_reshaped = X.reshape((X.shape[0], X.shape[1], 1))
        model = Sequential([LSTM(50, input_shape=(X_reshaped.shape[1], X_reshaped.shape[2])), Dense(1)])
        model.compile(optimizer='adam', loss='mse')
        model.fit(X_reshaped, y, epochs=5, batch_size=4)
        model.save('production_lstm.h5')
        print("Model trained and saved to production_lstm.h5")
    except ImportError:
        print("TensorFlow not installed. Sequence extraction completed successfully using analytics engine.")
