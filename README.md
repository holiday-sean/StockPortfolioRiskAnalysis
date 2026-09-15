# Portfolio Risk Analysis

### Introduction

#### Problem
Despite the continuous technological advances that have been made in conjunction with the finance industry, <b>there is no model</b> that has accurately captured the dynamic and unpredictable movements of the stock market. The features in order to predict the market are too multi-modal and complex in nature to capture and process. Furthermore, the trajectory of the market depends on future events that are unforseable. There is no definitive model, and there will probably never be one.

To the average investor that is interested in saving long-term, if there is no perfect model, how can one safely grow their portfolio? One way to approach this issue is to <b> account for risk.</b> If an investor can quantify risk, he/she/they can optimize their portfolio that withstand loss. But how do we even quantify risk in the first place? 

#### Solution (Monte Carlo Simulation)
One popular solution, to quantify risk as an objective metric, is to see all the potential portfolio values after `N` days using the <b>Monte Carlo Algorithm</b>.

The [Monte Carlo Algorithm](https://en.wikipedia.org/wiki/Monte_Carlo_method) is a mathematical technique that entails utilizing random sampling to estimate the potential outcomes of an uncertain system (in this case, our portfolio value after fluctuations in the stock market).

How do we apply this technique to our portfolio? We randomly sample the movements (events) in the stock market and combine it with out portfolio value. This process requires:
- Compiling share prices over a period of `N` days
- Calculating the variance, mean returns, and the degrees of freedom of each share
- Computing a covariance matrix that captures the relationship between different shares in one portfolio
  - E.g. if NVDA's share price decreases, how will AMZN's share price behave?
- Using linear algebra (matrix multiplication) to simulate how one's portfolio turns out everyday until `N` days is reached
- Do the previous step again many times (e.g. 1000 times) to create a distribution of potential portfolio earnings like a normal distribution or student's t-distribution
- Present the portfolio distribution along with key risk indicators captured such as value at risk (VaR), conditional value at risk (CVaR), and maximum dropdown (MDD) in a dashboard for an investor to decide whether the risk associated with their portfolio is acceptable.

### Pipeline Architecture
`Data (yfinance) → Python (Monte Carlo + Cholesky) → Risk Metrics → Power BI Dashboard`

### Running the Project

If you want to collect risk metrics for your own portfolio, clone the repo:

```bash
git clone https://github.com/holiday-sean/StockPortfolioRiskAnalysis.git
cd StockPortfolioRiskAnalysis
```

Then add your portfolio as `tickers.csv` in the repo root, with two columns — ticker symbol and number of shares you hold:

```csv
tickers,num_shares
AAPL,10
NVDA,5
```

#### Docker (Recommended)

Docker is the recommended path, especially on Windows, since `make` isn't natively available there — the Dockerfile installs it inside the container instead.

1. **Build and run the pipeline:**
   ```bash
   docker-compose up
   ```
   This builds the image (if needed) and runs the full pipeline (`make all`) inside the container. Outputs are written to `data/` in your local repo — the `docker-compose.yml` volume mapping means you'll see the CSVs on your host machine, not just inside the container. (If this step doesn't work, try creating an empty `data/` folder first and re-running.)

2. **Shut down the container:**
   ```bash
   docker-compose down
   ```
   This closes the Docker environment but keeps your generated data files intact.

3. **Re-run after changing your portfolio or starting value:**
   ```bash
   docker-compose up --build
   ```
   Any change to `tickers.csv` or the pipeline scripts requires a rebuild, since the code is copied into the image at build time rather than mounted live.

4. **Start fresh:**
   On Windows (no native `make`), the equivalent of `make clean` is manually deleting everything inside `data/`, then re-running `docker-compose up --build`.

#### Conda & Makefile (Linux/macOS)

If you're on Linux or macOS and already have `make` installed, you can skip Docker entirely:

1. **Create and activate the environment:**
   ```bash
   conda env create -f environment.yml
   conda activate portfolio-analysis
   ```

2. **Run the pipeline:**
   ```bash
   make all
   ```

3. **Start fresh:**
   ```bash
   make clean
   make all
   ```

#### Viewing your results

Once the pipeline finishes, `data/` will contain the simulation outputs (paths, summary risk stats, convergence sweep, etc. — see [Project Structure](#project-structure) below). Open the Power BI `.pbix` dashboard in Power BI Desktop; on first open, set the `DataFolder` parameter to the absolute path of your local `data/` folder so the dashboard points at your own results rather than needing any code changes.

### Project Structure

```
.
├── Dockerfile                 # Pipeline environment: Python 3.12-slim + make + pinned deps
├── docker-compose.yml         # Maps local data/ into the container; runs `make all` on `up`
├── Makefile                   # Orchestrates pipeline stages and their file dependencies
├── environment.yml            # Pinned conda dependencies for a non-Docker local run
├── tickers.csv                # Your input: ticker symbols + number of shares held
├── src/
│   ├── fetch_portfolio_dist.py   # tickers.csv → data/weights.csv (per-ticker portfolio weight)
│   ├── fetch_prices.py           # tickers.csv → data/prices.csv (5y daily Close, via yfinance)
│   ├── compute_returns.py        # data/prices.csv → data/returns.csv (daily log returns)
│   ├── compute_statistics.py     # data/returns.csv → data/stats.csv, data/covariance_matrix.csv
│   │                              #   (mean return, variance, t-distribution deg. of freedom per asset)
│   ├── simulate_portfolio.py     # Runs the Monte Carlo simulation → data/simulations.csv
│   │                              #   (correlated t-distributed draws via Cholesky decomposition,
│   │                              #    antithetic variates for variance reduction)
│   ├── visualize_results.py      # data/simulations.csv → data/simulation_paths.csv,
│   │                              #   data/simulation_summary.csv, data/mdd_distribution.csv
│   │                              #   (VaR, CVaR, probability of loss, max drawdown)
│   ├── analyze_convergence.py    # Sweeps n_simulations → data/convergence.csv
│   │                              #   (checks whether risk metrics have stabilized)
│   └── compute_risk.py           # covariance_matrix.csv + weights.csv → data/risk_contribution.csv
│                                  #   (variance-based risk decomposition per asset)
├── data/                      # Pipeline outputs — gitignored, regenerated on every run
└── <dashboard>.pbix           # Power BI dashboard: fan chart, MDD histogram,
                                #   covariance heatmap, VaR/CVaR/MDD summary cards
```

#### Pipeline flow

```
tickers.csv
   ├──► fetch_portfolio_dist.py ──► weights.csv ──────────────────┐
   └──► fetch_prices.py ──► prices.csv                            │
              │                                                   │
              ▼                                                   │
     compute_returns.py ──► returns.csv                           │
              │                                                   │
              ▼                                                   │
  compute_statistics.py ──► stats.csv, covariance_matrix.csv ─┐   │
              │                                                │   │
              │                                                ▼   ▼
              │                                    simulate_portfolio.py
              │                                                │
              │                                                ▼
              │                                          simulations.csv
              │                                          │         │
              │                                          ▼         ▼
              │                              visualize_results.py   analyze_convergence.py
              │                                          │         │
              │                                          ▼         ▼
              │                           simulation_paths.csv,   convergence.csv
              │                           simulation_summary.csv,
              │                           mdd_distribution.csv
              │
              └──► compute_risk.py (+ weights.csv) ──► risk_contribution.csv
```

### Dependencies

Pipeline dependencies are pinned in `environment.yml`:

| Package | Version | Purpose |
|---|---|---|
| `numpy` | 2.5.1 | Linear algebra (Cholesky decomposition), random number generation |
| `pandas` | 3.0.5 | Data wrangling, CSV I/O |
| `yfinance` | 1.5.2 | Historical price data from Yahoo Finance |
| `scipy` | 1.18.0 | Student's t-distribution fitting (`scipy.stats.t.fit`) |

Install locally with conda:

```bash
conda env create -f environment.yml
conda activate portfolio-analysis
```

If you're using Docker, you don't need to do this — the image installs the same pinned versions via `pip` automatically.

**Power BI dashboard:** the covariance heatmap is rendered as a Python visual inside Power BI Desktop, which relies on Power BI's own separately-configured Python environment (Power BI Options → Python scripting), not the conda environment above. That environment needs `pandas`, `numpy`, `matplotlib`, and `seaborn` available.

**Orchestration:**
- `make` — installed via `apt-get` inside the Docker image; not required on the host if you're using Docker Compose
- Docker / Docker Compose — to build and run the pipeline environment without setting up conda locally
