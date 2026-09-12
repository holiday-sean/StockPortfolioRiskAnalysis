"""
analyze_convergence.py

Runs the Monte Carlo simulation at a sweep of increasing n_simulations
values to check whether key risk metrics have stabilized, or are still
noisy due to too few trials.

Usage:
    python src/analyze_convergence.py <path_to_covariance_matrix> <path_to_stats_csv> --weights_path <path_to_weights_csv>

Input:
    The same covariance matrix and stats CSVs used by simulate_portfolio.py.

Output:
    data/convergence.csv — one row per n_simulations value swept, with
    columns for mean ending value and the same risk metrics reported in
    simulation_summary.csv (VaR, CVaR, prob_of_loss, MDD stats). Intended
    to be plotted as a convergence chart (metric vs. n_simulations).
"""

import argparse
import pandas as pd

from simulate_portfolio import run_simulation
from visualize_results import get_var_cvar, get_prob_of_loss, get_mdd


def run_convergence_analysis(cov_matrix, means, stats_df, weights,
                              n_simulations_list, n_period,
                              starting_portfolio_value, conf_level):
    """
    Runs run_simulation() once per value in n_simulations_list, computing
    the same risk metrics as visualize_results.py at each size, so their
    stability (or lack of it) can be plotted against n_simulations.

    Returns a DataFrame with one row per n_simulations value.
    """
    rows = []

    for n_simulations in n_simulations_list:
        df = run_simulation(
            cov_matrix, means, stats_df, weights,
            n_simulations, n_period, starting_portfolio_value
        )

        var, cvar = get_var_cvar(df, conf_level)
        prob_of_loss = get_prob_of_loss(df)
        mdd_per_trial = get_mdd(df)

        rows.append({
            'n_simulations': n_simulations,
            'actual_n_trials': df.shape[0],  # antithetic pairing can round n_simulations up
            'mean_ending_value': df.iloc[:, -1].mean(),
            'VaR': var,
            'CVaR': cvar,
            'prob_of_loss': prob_of_loss,
            'MDD_mean': mdd_per_trial.mean(),
            'MDD_median': mdd_per_trial.median(),
            'MDD_p5_worst_case': mdd_per_trial.quantile(0.05),
        })

    return pd.DataFrame(rows)


if __name__ == '__main__':
    # --- Parse command-line arguments ---
    parser = argparse.ArgumentParser(
        description="Sweep n_simulations to check convergence of Monte Carlo risk metrics."
    )
    parser.add_argument('cov_matrix_path', type=str)
    parser.add_argument('stats_path', type=str)
    parser.add_argument('--weights-path', type=str, required=True,
                        help='Path to CSV with columns: tickers, freq_distribution')
    parser.add_argument('--n-simulations-list', type=int, nargs='+',
                        default=[100, 500, 1000, 5000, 10000],
                        help='n_simulations values to sweep (default: 100 500 1000 5000 10000)')
    parser.add_argument('--n-periods', type=int, default=365,
                        help='Number of periods to simulate (default: 365)')
    parser.add_argument('--starting-value', type=float, default=10000)
    parser.add_argument('--conf_level', type=float, default=0.95,
                        help='Confidence level for VaR/CVaR (default: 0.95)')

    args = parser.parse_args()

    cov_matrix = pd.read_csv(args.cov_matrix_path, index_col=0).values
    stats_df = pd.read_csv(args.stats_path)
    means = stats_df['mean_return'].values

    cov_df = pd.read_csv(args.cov_matrix_path, index_col=0)
    weights_df = pd.read_csv(args.weights_path, index_col='tickers')
    weights = weights_df.loc[cov_df.index, 'freq_distribution'].values

    results = run_convergence_analysis(
        cov_matrix, means, stats_df, weights,
        args.n_simulations_list, args.n_periods,
        args.starting_value, args.conf_level
    )

    results.to_csv('data/convergence.csv', index=False)