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
import scipy

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

def get_degree_of_freedom(df):
    df_list = []
    for i in range(df.shape[1]):
        ticker_col = df.iloc[:, i]
        df_list.append(scipy.stats.t.fit(ticker_col.values)[0])

    df_list = pd.Series(df_list, index = df.columns)

    return df_list

stats = pd.DataFrame({
    "mean_return": df.mean(),
    "variance": df.var(), 
    "degree_of_freedom": get_degree_of_freedom(df)
})

cov = df.cov()

stats.to_csv('data/stats.csv')
cov.to_csv('data/covariance_matrix.csv')