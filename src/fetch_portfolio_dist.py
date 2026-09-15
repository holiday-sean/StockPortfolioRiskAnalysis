import pandas as pd
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('tickers_path', type=str, help='Path to tickers.csv')
    args = parser.parse_args()

    df = pd.read_csv(args.tickers_path, index_col='tickers')

    total_shares = np.sum(df['num_shares'])

    df['freq_distribution'] = df['num_shares'] / total_shares

    df['freq_distribution'].to_csv('data/weights.csv')