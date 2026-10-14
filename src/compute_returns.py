"""
compute_returns.py

Reads historical adjusted daily closing prices and computes the daily
log return of each stock.

Usage:
    python src/compute_returns.py <path_to_prices_csv>

Input:
    data/prices.csv — closing prices, one column per ticker, indexed by Date.

Output:
    data/returns.csv — daily log returns, one column per ticker, indexed
    by Date.
"""

import argparse
import pandas as pd

import core


def main():
    parser = argparse.ArgumentParser(
        description='Read stock prices to compute daily log returns & save it to CSV.'
    )
    parser.add_argument(
        'filepath',
        type=str,
        help='Path to a csv file containing closing prices for stock tickers (e.g. prices.csv)'
    )
    args = parser.parse_args()

    prices = pd.read_csv(args.filepath, index_col='Date')
    core.get_log_returns(prices).to_csv('data/returns.csv')


if __name__ == '__main__':
    main()
