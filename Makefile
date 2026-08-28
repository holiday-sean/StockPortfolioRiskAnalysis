all: data/simulation_paths.csv

.PHONY: all clean

data: 
	mkdir -p data

data/prices.csv: src/fetch_prices.py tickers.txt | data
	python src/fetch_prices.py 'tickers.txt'

data/returns.csv: src/compute_returns.py data/prices.csv
	python src/compute_returns.py 'data/prices.csv'

data/stats.csv data/covariance_matrix.csv &: src/compute_statistics.py data/returns.csv
	python src/compute_statistics.py 'data/returns.csv'

data/simulations.csv: src/simulate_portfolio.py data/stats.csv data/covariance_matrix.csv
	python src/simulate_portfolio.py 'data/covariance_matrix.csv' 'data/stats.csv' --weights 0.6 0.4

data/simulation_paths.csv data/simulation_summary.csv &: src/visualize_results.py data/simulations.csv
	python src/visualize_results.py 'data/simulations.csv' 

clean:
	-rm -f data/*.csv

