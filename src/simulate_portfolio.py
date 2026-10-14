"""
simulate_portfolio.py

Runs the Monte Carlo simulation to generate a distribution of potential
portfolio values for risk analysis. The simulation itself lives in
core.simulate(); this script only handles files and arguments.

Usage:
    python src/simulate_portfolio.py <cov_matrix_csv> <stats_csv> --weights-path <weights_csv>
        [--n-simulations 1000] [--n-periods 365] [--starting-value 10000]

Input:
    data/covariance_matrix.csv, data/stats.csv, and a weights CSV with
    columns: tickers, freq_distribution.

Output:
    data/simulations.csv — one row per trial, one column per period
    (column 0 is the starting value).
"""

import argparse
import pandas as pd

import core


def main():
    parser = argparse.ArgumentParser(
        description="Run the Monte Carlo portfolio simulation."
    )
    parser.add_argument('cov_matrix_path', type=str)
    parser.add_argument('stats_path', type=str)
    parser.add_argument('--n-simulations', type=int, default=1000,
                        help='Number of Monte Carlo trials (default: 1000)')
    parser.add_argument('--n-periods', type=int, default=365,
                        help='Number of periods to simulate (default: 365)')
    parser.add_argument('--starting-value', type=float, default=10000)
    parser.add_argument('--weights-path', type=str, required=True,
                        help='Path to CSV with columns: tickers, freq_distribution')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible runs (default: none)')
    args = parser.parse_args()

    cov = pd.read_csv(args.cov_matrix_path, index_col=0)
    stats = pd.read_csv(args.stats_path, index_col=0)
    weights = pd.read_csv(args.weights_path, index_col='tickers')['freq_distribution']

    # align everything to the covariance matrix's ticker order
    paths = core.simulate(
        cov.values,
        stats.loc[cov.index, 'mean_return'].values,
        stats.loc[cov.index, 'degree_of_freedom'].values,
        weights.loc[cov.index].values,
        args.n_simulations, args.n_periods, args.starting_value,
        seed=args.seed,
    )
    paths.to_csv('data/simulations.csv')


if __name__ == '__main__':
    main()
