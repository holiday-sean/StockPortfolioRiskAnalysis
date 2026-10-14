"""
fetch_prices.py

Fetches historical adjusted daily closing prices for a list of stock
tickers from Yahoo Finance and saves them to a CSV file.

Usage:
    python src/fetch_prices.py <path_to_tickers_csv>

Input:
    tickers.csv with a 'tickers' column (one ticker per row).

Output:
    data/prices.csv — daily closing prices, one column per ticker,
    indexed by date, covering the trailing 5 years.
"""

import argparse
import pandas as pd

import core


def main():
    parser = argparse.ArgumentParser(
        description="Fetch historical stock prices for a list of tickers and save to CSV."
    )
    parser.add_argument(
        'filepath',
        type=str,
        help='Path to a csv file containing stock tickers (e.g. tickers.csv)'
    )
    args = parser.parse_args()

    tickers = pd.read_csv(args.filepath, index_col='tickers').index.tolist()
    core.get_prices(tickers, period='5y').to_csv('data/prices.csv')


if __name__ == '__main__':
    main()
