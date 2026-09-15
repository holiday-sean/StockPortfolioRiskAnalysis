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
`Data (yfinance) → Python -> GARCH Model → Risk Metrics → Power BI Dashboard`

### Running the Project
If you want to collect risk metrics for your own portfolio, in your terminal running the following:

`git clone https://github.com/holiday-sean/StockPortfolioRiskAnalysis.git`

Then upload your portfolio (in  a `.csv` format) and name it `tickers.csv`.

#### Docker (Recommended):
1. `docker-compose up`

The data will be populated into the `data` folder (Note: If this step does not work, create an empy data folder)

2. `docker-compose down`

Running this command will close the docker environment but retain your data files. (Note: run `docker-compose up --build` if you <b>change</b> your portfolio data or starting portfolio value)

#### Conda & Makefile

1. `conda create --file environment.yaml`

2. `conda activate portfolio-analysis`

3. `make all`

### Project Structure

In progress....

### Dependencies

In progress....
