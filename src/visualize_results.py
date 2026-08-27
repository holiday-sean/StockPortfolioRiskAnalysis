"""
visualize_results.py

Reads Monte Carlo simulation paths and produces two outputs for Power BI:
a representative subset of raw paths, and a table of summary risk statistics.

Usage:
    python visualize_results.py <path_to_simulations_csv> [--conf_level 0.95] [--n_paths 500]

Input:
    data/simulations.csv — rows = trial_id, columns = period, values = portfolio value.

Output:
    data/simulation_paths.csv   — a random subset of full trial paths (for fan chart viz)
    data/simulation_summary.csv — one-row table of VaR, CVaR, probability of loss, and MDD stats
"""

import argparse
import numpy as np
import pandas as pd

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(
    description="Compute risk summary statistics and a representative path subset from simulation results."
)
parser.add_argument(
    'filepath',
    type=str,
    help='Path to simulations.csv (rows=trial_id, columns=period)'
)
parser.add_argument(
    '--conf_level',
    type=float,
    default=0.95,
    help='Confidence level for VaR/CVaR, e.g. 0.95 for 95%% confidence (default: 0.95)'
)
parser.add_argument(
    '--n_paths',
    type=int,
    default=500,
    help='Number of representative trial paths to export for Power BI (default: 500)'
)
parser.add_argument(
    '--random_state',
    type=int,
    default=42,
    help='Random seed for reproducible path sampling (default: 42)'
)
args = parser.parse_args()

df = pd.read_csv(args.filepath, index_col=0)


def get_path_subset(df: pd.DataFrame, n_paths: int, random_state: int) -> pd.DataFrame:
    """
    Selects a representative subset of trial paths for visualization.

    Combines a random sample with the trials at the extremes (min/max ending
    value) and near the 5th/95th percentile of ending value, so tail behavior
    isn't lost to random sampling alone.
    """
    n_paths = min(n_paths, df.shape[0])
    ending_values = df.iloc[:, -1]

    random_sample = df.sample(n=n_paths, random_state=random_state)

    tail_idx = pd.Index([
        ending_values.idxmin(),
        ending_values.idxmax(),
        (ending_values - ending_values.quantile(0.05)).abs().idxmin(),
        (ending_values - ending_values.quantile(0.95)).abs().idxmin(),
    ]).unique()

    subset = pd.concat([random_sample, df.loc[tail_idx]])
    subset = subset[~subset.index.duplicated(keep='first')]

    return subset


def get_var_cvar(df: pd.DataFrame, conf_level: float) -> tuple[float, float]:
    """
    Computes Value at Risk and Conditional Value at Risk on log returns
    (ending value vs. starting value) across all trials.

    conf_level=0.95 means a 5% one-sided tail (95% of outcomes are better
    than VaR); the entire excluded tail sits on the loss side.
    """
    first_day = df.iloc[:, 0]
    last_day = df.iloc[:, -1]

    input_dist = np.log(last_day / first_day)
    var = np.percentile(input_dist, (1 - conf_level) * 100)
    cvar = input_dist[input_dist < var].mean()

    return var, cvar


def get_prob_of_loss(df: pd.DataFrame) -> float:
    """Fraction of trials ending below their starting value."""
    first_day = df.iloc[:, 0]
    last_day = df.iloc[:, -1]

    return (last_day < first_day).mean()


def get_mdd(df: pd.DataFrame) -> pd.Series:
    """
    Max drawdown per trial: worst peak-to-trough decline along each path,
    using a running peak (not a fixed global peak or adjacent-period diff).
    """
    peak = df.cummax(axis=1)
    drawdown = (df - peak) / peak
    max_drawdown = drawdown.min(axis=1)

    return max_drawdown


# --- Step 1: representative path subset for Power BI fan chart ---
path_subset = get_path_subset(df, args.n_paths, args.random_state)
path_subset.to_csv('data/simulation_paths.csv')

# --- Step 2: summary risk statistics ---
var, cvar = get_var_cvar(df, args.conf_level)
prob_of_loss = get_prob_of_loss(df)
mdd_per_trial = get_mdd(df)

results = pd.DataFrame({
    'conf_level': [args.conf_level],
    'VaR': [var],
    'CVaR': [cvar],
    'prob_of_loss': [prob_of_loss],
    'MDD_mean': [mdd_per_trial.mean()],
    'MDD_median': [mdd_per_trial.median()],
    'MDD_p5_worst_case': [mdd_per_trial.quantile(0.05)],
})

results.to_csv('data/simulation_summary.csv', index=False)