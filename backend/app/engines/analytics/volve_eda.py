"""
Volve dataset EDA skeleton
Usage: python volve_eda.py --data data/volve
"""
import pandas as pd
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', required=True)
    args = parser.parse_args()
    # Simplified example: list files
    files = os.listdir(args.data)
    print('Files:', files)
    # User should implement EDA steps specific to Volve dataset
