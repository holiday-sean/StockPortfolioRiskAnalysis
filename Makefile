all: data/simulation_paths.csv data/convergence.csv data/risk_contribution.csv

.PHONY: all clean

data:
	mkdir -p data

data/weights.csv: src/fetch_portfolio_dist.py tickers.csv | data
	python src/fetch_portfolio_dist.py 'tickers.csv'

data/prices.csv: src/fetch_prices.py src/core.py tickers.csv | data
	python src/fetch_prices.py 'tickers.csv'

data/returns.csv: src/compute_returns.py src/core.py data/prices.csv
	python src/compute_returns.py 'data/prices.csv'

data/stats.csv data/covariance_matrix.csv &: src/compute_statistics.py src/core.py data/returns.csv
	python src/compute_statistics.py 'data/returns.csv'

data/simulations.csv: src/simulate_portfolio.py src/core.py data/stats.csv data/covariance_matrix.csv data/weights.csv
	python src/simulate_portfolio.py 'data/covariance_matrix.csv' 'data/stats.csv' --weights-path 'data/weights.csv'

data/risk_contribution.csv: src/compute_risk.py src/core.py data/covariance_matrix.csv data/weights.csv
	python src/compute_risk.py 'data/covariance_matrix.csv' 'data/weights.csv'

data/simulation_paths.csv data/simulation_summary.csv data/mdd_distribution.csv &: src/visualize_results.py src/core.py data/simulations.csv
	python src/visualize_results.py 'data/simulations.csv'

data/convergence.csv: src/analyze_convergence.py src/core.py data/covariance_matrix.csv data/stats.csv data/weights.csv
	python src/analyze_convergence.py 'data/covariance_matrix.csv' 'data/stats.csv' --weights-path 'data/weights.csv'

clean:
	-rm -f data/*.csv
