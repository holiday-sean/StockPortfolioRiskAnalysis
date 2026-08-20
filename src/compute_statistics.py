"""
compute_statistics.py

Fetches historical adjusted daily closing prices for a list of stock
tickers from Yahoo Finance and saves them to a CSV file.

Usage:
    python compute_statistics.py <path_to_returns_file>

Input:
    A plain text file containing log returns for stocks stored in the
    'data' folder as 'returns.csv'

Output:
    data/stats.csv — a CSV of summary statistics, one column per
    ticker, containing....

    data/covariance_matrix.csv - a CSV containing a covariance matrix of
    all stocks for monte algorithm later on 
"""

import argparse
import datetime as dt
import pandas as pd
import numpy as np

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(
    description='Fetch stock log returns for a list of tickers and save to CSV.'
)
parser.add_argument(
    'filepath',
    type=str,
    help='Path to a text file (e.g. returns.csv)'
)
args = parser.parse_args()

df = pd.read_csv(args.filepath, index_col='Date')

stats = pd.DataFrame({
    "mean_return": df.mean(),
    "variance": df.var()
})

cov = df.cov()

stats.to_csv('data/stats.csv')
cov.to_csv('data/covariance_matrix.csv')