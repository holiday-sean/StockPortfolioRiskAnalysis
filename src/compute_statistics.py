"""
compute_statistics.py

Computes per-stock summary statistics and the covariance matrix from
daily log returns.

Usage:
    python src/compute_statistics.py <path_to_returns_csv>

Input:
    data/returns.csv — daily log returns, one column per ticker.

Output:
    data/stats.csv — per-ticker mean_return, variance, degree_of_freedom
    (fitted Student's t).

    data/covariance_matrix.csv — covariance matrix of all tickers, used
    by the Monte Carlo simulation.
"""

import argparse
import pandas as pd

import core


def main():
    parser = argparse.ArgumentParser(
        description='Compute summary statistics and covariance from log returns.'
    )
    parser.add_argument(
        'filepath',
        type=str,
        help='Path to a csv file of log returns (e.g. returns.csv)'
    )
    args = parser.parse_args()

    returns = pd.read_csv(args.filepath, index_col='Date')
    stats, cov = core.get_stats(returns)

    stats.to_csv('data/stats.csv')
    cov.to_csv('data/covariance_matrix.csv')


if __name__ == '__main__':
    main()
