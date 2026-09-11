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
import math

def generate_random_vector(stats_df, rng):
    vector = np.array([])

    for i in range(stats_df.shape[0]):
        d_o_f = stats_df.iloc[i]['degree_of_freedom']
        el = rng.standard_t(df = d_o_f, size = 1)
        scaled_el = el / math.sqrt(d_o_f/(d_o_f - 2))
        vector = np.append(vector, scaled_el)

    antithetic_vector = -vector 

    return vector, antithetic_vector

def run_simulation(cov_matrix, means, stats_df, weights, n_simulations, n_period, starting_portfolio_value):
    simulations = []
    lower_triangle_matrix = np.linalg.cholesky(cov_matrix)
    rng = np.random.default_rng()  # per your earlier fix — one rng, outside the loop

    for i in range(math.ceil(n_simulations / 2)):
        value = starting_portfolio_value
        anti_value = starting_portfolio_value

        value_path = [value]
        anti_value_path = [anti_value]

        for j in range(n_period):
            z, anti_z = generate_random_vector(stats_df, rng)

            period_asset_returns = (lower_triangle_matrix @ z) + means
            anti_period_asset_returns = (lower_triangle_matrix @ anti_z) + means

            portfolio_return = weights @ period_asset_returns
            anti_portfolio_return = weights @ anti_period_asset_returns

            portfolio_return = max(portfolio_return, -1.0)
            anti_portfolio_return = max(anti_portfolio_return, -1.0)

            value *= (1 + portfolio_return)
            anti_value *= (1 + anti_portfolio_return)

            value_path.append(value)
            anti_value_path.append(anti_value)

        simulations.append(value_path)
        simulations.append(anti_value_path)

    return pd.DataFrame(simulations)

if __name__ == '__main__':
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
    stats_df = pd.read_csv(args.stats_path)
    means = stats_df['mean_return'].values
    n_simulations = args.n_simulations
    n_period = args.n_periods
    n_assets = pd.read_csv(args.cov_matrix_path, index_col=0).shape[0]
    starting_portfolio_value = args.starting_value
    weights = args.weights
    rng = np.random.default_rng()

    results = run_simulation(cov_matrix, means, stats_df, weights, n_simulations, n_period, starting_portfolio_value)
    results.to_csv('data/simulations.csv')