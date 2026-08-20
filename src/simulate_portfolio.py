"""
simulate_portfolio.py

Uses the Monte Carlo algorithim to generate a distribution of the
potential value of a portfolio for future risk analysis.

Usage:
    python simulate_portfolio.py 

Input:
    The file pathway to the covariance matrix of stocks, saved in the 
    data folder (e.g. covariance_matrix.csv)

    The file pathway to the aggregate statistcs of stocks, saved in the 
    data folder (e.g. stats.csv)

    The number of simulations, which determines the size of the distribution

    The period (in days), in other words, how far in time are you looking in
    for the portfolio 

    Your portfolio starting value (a float number)

    The weights - the proportion of your starting value that is allocated to
    each stocks. Inputed as a list. 

Output:
    data/simulations.csv — a CSV representing the distribution of a portfolio
    of the following shape (n_simulations, n_period)

"""


import numpy as np
import pandas as pd
import argparse

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(
    description="Inputting the corresponding parameters for the monte carlo algo"
)

parser.add_argument('cov_matrix_path', type=str)
parser.add_argument('stats_path', type=str)
parser.add_argument('--n-simulations', type=int, default=1000,
                     help='Number of Monte Carlo trials (default: 1000)')
parser.add_argument('--n-periods', type=int, default=365,
                     help='Number of periods to simulate (default: 365)')
parser.add_argument('--starting-value', type=float, default=10000)
parser.add_argument('--weights', type=float, nargs='+', required=True,
                     help='Portfolio weights per asset, e.g. --weights 0.6 0.4')

args = parser.parse_args()

cov_matrix = pd.read_csv(args.cov_matrix_path, index_col=0).values
means = pd.read_csv(args.stats_path)['mean_return'].values
n_simulations = args.n_simulations
n_period = args.n_periods
n_assets = pd.read_csv(args.cov_matrix_path, index_col=0).shape[0]
starting_portfolio_value = args.starting_value
weights = args.weights

all_simulations = []

lower_triangle_matrix = np.linalg.cholesky(cov_matrix)

def generate_random_vector():
    rng = np.random.default_rng()
    return rng.standard_normal(size = n_assets)

for i in range(n_simulations):
    value = starting_portfolio_value
    value_path = [value]

    for j in range(n_period):
        z = generate_random_vector()
        period_asset_returns = (lower_triangle_matrix @ z) + means

        portfolio_return = weights @ period_asset_returns
        value *= (1 + portfolio_return)
        value_path.append(value)

    all_simulations.append(value_path)

results = pd.DataFrame(all_simulations)

results.to_csv('data/simulations.csv')