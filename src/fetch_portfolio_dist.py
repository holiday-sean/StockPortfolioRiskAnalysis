import pandas as pd
import numpy as np

df = pd.read_csv('tickers.csv', index_col='tickers')

total_shares = np.sum(df['num_shares'])

df['freq_distribution'] = df['num_shares'] / total_shares

df['freq_distribution'].to_csv('data/weights.csv')