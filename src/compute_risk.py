"""
compute_risk.py

Computes each asset's percentage contribution to total portfolio variance.

Usage:
    python src/compute_risk.py <covariance_matrix_csv> <weights_csv>

Input:
    data/covariance_matrix.csv and data/weights.csv (columns: tickers, freq_distribution).

Output:
    data/risk_contribution.csv — columns: asset, contribution_percent (sums to 100).
"""

import argparse
import pandas as pd

import core


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('covariance_matrix_path', type=str, help='Path to covariance_matrix.csv')
    parser.add_argument('weights_path', type=str, help='Path to weights.csv')
    args = parser.parse_args()

    cov = pd.read_csv(args.covariance_matrix_path, index_col=0)
    weights = pd.read_csv(args.weights_path, index_col=0).iloc[:, 0]

    contribution = core.get_risk_contributions(cov, weights)

    pd.DataFrame({
        'asset': contribution.index,
        'contribution_percent': contribution.values,
    }).to_csv('data/risk_contribution.csv', index=False)


if __name__ == '__main__':
    main()
