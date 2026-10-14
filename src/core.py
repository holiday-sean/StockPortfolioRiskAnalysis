"""
core.py

In-memory building blocks for the Monte Carlo portfolio risk pipeline.

Every function takes and returns Python objects (DataFrames / arrays) and
never reads or writes files, so it can be called from the CLI scripts,
a Streamlit app, or tests without side effects.

Pipeline:
    get_prices -> get_log_returns -> get_stats -> simulate -> summarize
                                   \\-> get_risk_contributions
"""

import numpy as np
import pandas as pd
import scipy.stats


# ---------------------------------------------------------------- data

def get_prices(tickers, period='5y'):
    """Daily closing prices (dividend/split adjusted), one column per ticker.

    Rows with a missing price for any ticker are dropped so all dates align.
    Imported lazily so the rest of the module works without yfinance.
    """
    import yfinance as yf

    tickers = list(tickers)
    data = yf.download(" ".join(tickers), period=period, interval='1d',
                       auto_adjust=True, progress=False)
    if data is None or data.empty or 'Close' not in data:
        raise ValueError(f"No price data came back for: {', '.join(tickers)}. "
                         "Check the ticker symbols.")

    close = data['Close']
    if isinstance(close, pd.Series):          # single ticker comes back as a Series
        close = close.to_frame(tickers[0])

    # an unknown ticker comes back as an all-NaN (or missing) column
    bad = [t for t in tickers if t not in close.columns or close[t].isna().all()]
    if bad:
        raise ValueError(f"No price data found for: {', '.join(bad)}. "
                         "Check the ticker symbols.")

    return close[tickers].dropna(how='any')


def get_log_returns(prices):
    """Daily log returns: log(P_t / P_{t-1})."""
    return np.log(prices / prices.shift(1)).dropna()


def get_stats(returns):
    """Per-asset mean, variance and fitted Student's-t degrees of freedom,
    plus the covariance matrix of returns.

    Returns (stats_df, cov_df). stats_df is indexed by ticker with columns
    mean_return, variance, degree_of_freedom.
    """
    dof = pd.Series(
        [scipy.stats.t.fit(returns[col].values)[0] for col in returns.columns],
        index=returns.columns,
    )
    stats_df = pd.DataFrame({
        'mean_return': returns.mean(),
        'variance': returns.var(),
        'degree_of_freedom': dof,
    })
    return stats_df, returns.cov()


def normalize_weights(weights):
    """Scale a Series of non-negative weights (indexed by ticker) to sum to 1."""
    weights = weights.astype(float)
    if (weights < 0).any() or weights.sum() <= 0:
        raise ValueError("Weights must be non-negative and sum to more than 0.")
    return weights / weights.sum()


# ---------------------------------------------------------- simulation

def _cholesky(cov_matrix):
    """Cholesky factor of a covariance matrix. If it is numerically singular
    (e.g. two near-identical assets), add a tiny diagonal 'jitter' and retry."""
    cov_matrix = np.asarray(cov_matrix, dtype=float)
    scale = np.trace(cov_matrix) / len(cov_matrix)
    for eps in (0.0, 1e-10, 1e-8, 1e-6):
        try:
            return np.linalg.cholesky(cov_matrix + eps * scale * np.eye(len(cov_matrix)))
        except np.linalg.LinAlgError:
            continue
    raise ValueError("The covariance matrix is not positive definite. "
                     "Two or more assets are likely duplicates or perfectly correlated.")


def simulate(cov_matrix, means, dof, weights, n_simulations, n_periods,
             starting_value, seed=None, max_chunk_elems=5_000_000):
    """Vectorized Monte Carlo portfolio paths (same model as simulate_loop).

    Shocks are drawn for many trials at once as a (trials, periods, assets)
    array. Because the portfolio return is linear in the shocks,
        w . (L z + mu) = z . (L^T w) + w . mu
    so the per-asset return array is never built; each period collapses
    straight to one portfolio log return, and np.cumsum accumulates them
    (log returns add over time).

    Trials are generated in chunks of at most ~max_chunk_elems random draws
    (about 8 bytes each) to bound memory, so a small host can still run
    large simulations.

    Returns a DataFrame of shape (n_trials, n_periods + 1); column 0 is the
    starting value. n_trials is n_simulations rounded up to an even number
    (antithetic pairs).
    """
    means = np.asarray(means, dtype=float)
    weights = np.asarray(weights, dtype=float)
    dof = np.maximum(np.asarray(dof, dtype=float), 2.5)  # variance undefined at <= 2

    L = _cholesky(cov_matrix)
    rng = np.random.default_rng(seed)
    scale = np.sqrt(dof / (dof - 2))                      # t variance -> 1

    loading = L.T @ weights                               # (assets,)
    drift = weights @ means

    n_assets = len(means)
    n_pairs = (n_simulations + 1) // 2
    pairs_per_chunk = max(1, max_chunk_elems // (n_periods * n_assets))

    out = np.empty((2 * n_pairs, n_periods + 1))
    out[:, 0] = starting_value

    done = 0
    while done < n_pairs:
        k = min(pairs_per_chunk, n_pairs - done)
        z = rng.standard_t(dof, size=(k, n_periods, n_assets)) / scale
        port_ret = np.concatenate([z, -z]) @ loading + drift      # (2k, periods)
        rows = slice(2 * done, 2 * (done + k))
        out[rows, 1:] = starting_value * np.exp(np.cumsum(port_ret, axis=1))
        done += k

    return pd.DataFrame(out)


def simulate_loop(cov_matrix, means, dof, weights, n_simulations, n_periods,
                  starting_value, seed=None):
    """Reference implementation: plain Python loops, one day at a time.
    Slow; kept to check that simulate() reproduces the same distribution.

    Monte Carlo portfolio paths using correlated, unit-variance Student's-t
    shocks (independent t draws per asset passed through the Cholesky factor
    of the covariance matrix) with antithetic pairing.

    All asset inputs are 1-D/2-D arrays in the same ticker order.
    Returns a DataFrame of shape (n_trials, n_periods + 1); column 0 is the
    starting value. n_trials is n_simulations rounded up to an even number.
    """
    cov_matrix = np.asarray(cov_matrix, dtype=float)
    means = np.asarray(means, dtype=float)
    weights = np.asarray(weights, dtype=float)
    dof = np.maximum(np.asarray(dof, dtype=float), 2.5)  # variance undefined at <= 2

    L = np.linalg.cholesky(cov_matrix)
    rng = np.random.default_rng(seed)
    scale = np.sqrt(dof / (dof - 2))                      # t variance -> 1

    paths = []
    for _ in range((n_simulations + 1) // 2):
        value = anti_value = starting_value
        path, anti_path = [value], [anti_value]

        for _ in range(n_periods):
            z = rng.standard_t(dof) / scale               # one draw per asset
            port_ret = weights @ (L @ z + means)
            anti_port_ret = weights @ (L @ -z + means)

            # returns are log returns, so compound with exp, not (1 + r)
            value *= np.exp(port_ret)
            anti_value *= np.exp(anti_port_ret)
            path.append(value)
            anti_path.append(anti_value)

        paths.append(path)
        paths.append(anti_path)

    return pd.DataFrame(paths)


# ------------------------------------------------------------- metrics

def get_var_cvar(paths, conf_level=0.95):
    """VaR and CVaR of the total return (ending / starting - 1) across trials.
    Both are negative numbers when they represent a loss."""
    total_return = paths.iloc[:, -1] / paths.iloc[:, 0] - 1
    var = np.nanpercentile(total_return, (1 - conf_level) * 100)
    cvar = total_return[total_return < var].mean()
    return var, cvar


def get_prob_of_loss(paths):
    """Fraction of trials ending below their starting value."""
    return (paths.iloc[:, -1] < paths.iloc[:, 0]).mean()


def get_mdd(paths):
    """Max drawdown per trial using a running peak. Returns a Series."""
    peak = paths.cummax(axis=1)
    return ((paths - peak) / peak).min(axis=1)


def summarize(paths, conf_level=0.95):
    """Headline risk metrics as a dict."""
    var, cvar = get_var_cvar(paths, conf_level)
    mdd = get_mdd(paths)
    return {
        'conf_level': conf_level,
        'n_trials': paths.shape[0],
        'mean_ending_value': paths.iloc[:, -1].mean(),
        'VaR': var,
        'CVaR': cvar,
        'prob_of_loss': get_prob_of_loss(paths),
        'MDD_mean': mdd.mean(),
        'MDD_median': mdd.median(),
        'MDD_p5_worst_case': mdd.quantile(0.05),
    }


def get_risk_contributions(cov_df, weights):
    """Each asset's share of portfolio variance, in percent (sums to 100).

    cov_df: covariance DataFrame; weights: Series indexed by ticker.
    """
    w = weights.loc[cov_df.index]
    sigma_w = cov_df @ w
    port_var = w @ sigma_w
    return (w * sigma_w / port_var * 100).rename('contribution_percent')


# ----------------------------------------------------------- end to end

def analyze_portfolio(prices, weights, n_simulations, n_periods,
                      starting_value, conf_level=0.95, seed=None):
    """Run the whole analysis on an in-memory price table (no network, no files).

    prices:  DataFrame of closing prices, one column per ticker.
    weights: Series indexed by ticker (any positive scale; normalized here).

    Returns a dict with returns, stats, cov, weights, paths, summary,
    risk_contributions and mdd (per-trial max drawdown).
    """
    returns = get_log_returns(prices)
    stats_df, cov = get_stats(returns)
    w = normalize_weights(weights.loc[cov.index])

    paths = simulate(cov.values,
                     stats_df['mean_return'].values,
                     stats_df['degree_of_freedom'].values,
                     w.values,
                     n_simulations, n_periods, starting_value, seed=seed)

    return {
        'returns': returns,
        'stats': stats_df,
        'cov': cov,
        'weights': w,
        'paths': paths,
        'summary': summarize(paths, conf_level),
        'risk_contributions': get_risk_contributions(cov, w),
        'mdd': get_mdd(paths),
    }
