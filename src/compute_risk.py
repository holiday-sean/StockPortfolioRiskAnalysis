"""
"""
import pandas as pd
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('covariance_matrix_path', type=str, help='Path to covariance_matrix.csv')
    parser.add_argument('weights_path', type=str, help='Path to weights.csv')
    args = parser.parse_args()

    cov_matrix = pd.read_csv(args.covariance_matrix_path, index_col=0)
    weights = pd.read_csv(args.weights_path, index_col=0)

    sigma_w = cov_matrix @ weights
    portfolio_variance = (weights.T @ cov_matrix @ weights).iloc[0, 0]

    contribution = (weights * sigma_w) / portfolio_variance

    risk_contribution = pd.DataFrame({
        'asset': weights.index,
        'contribution_percent': contribution.iloc[:, 0].values
    })

    risk_contribution.to_csv('data/risk_contribution.csv', index=False)