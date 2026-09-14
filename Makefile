all: data/simulation_paths.csv data/convergence.csv

.PHONY: all clean

data: 
	mkdir -p data

data/weights.csv: src/fetch_portfolio_dist.py tickers.csv
	python src/fetch_portfolio_dist.py 'tickers.csv'

data/prices.csv: src/fetch_prices.py tickers.csv | data
	python src/fetch_prices.py 'tickers.csv'

data/returns.csv: src/compute_returns.py data/prices.csv
	python src/compute_returns.py 'data/prices.csv'

data/stats.csv data/covariance_matrix.csv &: src/compute_statistics.py data/returns.csv
	python src/compute_statistics.py 'data/returns.csv'

data/simulations.csv: src/simulate_portfolio.py data/stats.csv data/covariance_matrix.csv data/weights.csv
	python src/simulate_portfolio.py 'data/covariance_matrix.csv' 'data/stats.csv' --weights-path 'data/weights.csv'

data/simulation_paths.csv data/simulation_summary.csv data/mdd_distribution.csv &: src/visualize_results.py data/simulations.csv
	python src/visualize_results.py 'data/simulations.csv' 

data/convergence.csv: src/analyze_convergence.py data/covariance_matrix.csv data/stats.csv
	python src/analyze_convergence.py 'data/covariance_matrix.csv' 'data/stats.csv' --weights-path 'data/weights.csv'

clean:
	-rm -f data/*.csv

