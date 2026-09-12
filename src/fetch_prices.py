"""
fetch_prices.py

Fetches historical adjusted daily closing prices for a list of stock
tickers from Yahoo Finance and saves them to a CSV file.

Usage:
    python fetch_prices.py <path_to_ticker_file>

Input:
    A plain text file containing stock tickers separated by whitespace
    (spaces, tabs, or newlines), located in 'portfolio.txt', e.g.:
        AAPL AMZN VTI

Output:
    data/prices.csv — a CSV of daily closing prices, one column per
    ticker, indexed by date, covering the trailing 5 years.
"""

import argparse
import pandas as pd
import yfinance as yf

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(
    description="Fetch historical stock prices for a list of tickers and save to CSV."
)
parser.add_argument(
    'filepath',
    type=str,
    help='Path to a csv file containing stock tickers (e.g. tickers.csv)'
)
args = parser.parse_args()

df = pd.read_csv(args.filepath, index_col='tickers')
tickers_ls = df.index.values
content = " ".join(tickers_ls)

# --- Fetch price data from Yahoo Finance ---
# yf.Tickers() is used here to validate/register the ticker symbols.
tickers = yf.Tickers(content)

# Downloads 5 years of daily OHLCV data for all tickers.
# Returns a MultiIndex DataFrame: top level = price type (Open/High/Low/Close/Volume),
# second level = ticker symbol.
data = pd.DataFrame(yf.download(content, period='5y', interval='1d'))

# Extract just the closing prices across all tickers, collapsing the
# MultiIndex down to a single-level DataFrame (columns = tickers).
closed_prices = data['Close']

# --- Save to disk ---
closed_prices.to_csv('data/prices.csv')