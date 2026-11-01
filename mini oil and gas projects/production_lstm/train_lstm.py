"""
Train a simple LSTM for production forecasting
Usage: python train_lstm.py --data production.csv
"""
import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import ModelCheckpoint
import argparse


def create_sequences(arr, window=12):
    X, y = [], []
    for i in range(len(arr)-window):
        X.append(arr[i:i+window])
        y.append(arr[i+window])
    return np.array(X), np.array(y)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    df = pd.read_csv(args.data, parse_dates=[0])
    arr = df['production'].fillna(method='ffill').to_numpy()
    arr = (arr - arr.mean()) / arr.std()
    X, y = create_sequences(arr, window=12)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = Sequential([LSTM(50, input_shape=(X.shape[1], X.shape[2])), Dense(1)])
    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=20, batch_size=16)
    model.save('production_lstm.h5')
