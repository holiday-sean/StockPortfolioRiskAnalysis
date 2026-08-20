"""
compute_returns.py

Reads historical adjusted daily closing prices for a list of stocks
and returns a computed list of the daily log returns for each stock.

Usage:
    python compute_prices.py <path_to_data_prices_file>

Input:
    A csv file containing the adjusted closing prices of tickers
    located in data folder. 

Output:
    data/returns.csv — a CSV of daily returns prices, one column per
    ticker, indexed by date, covering the trailing 5 years.
"""

import argparse
import datetime as dt
import pandas as pd
import numpy as np

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(
    description='Read stock prices to compute daily log returns & save it to CSV.'
)
parser.add_argument(
    'filepath',
    type=str,
    help='Path to a csv file containing closing prices for stock tickers (e.g. prices.csv)'
)
args = parser.parse_args()

df = pd.read_csv(args.filepath, index_col='Date')

log_returns = np.log(df / df.shift(periods=1))
log_returns = log_returns.dropna()
log_returns.to_csv('data/returns.csv')

