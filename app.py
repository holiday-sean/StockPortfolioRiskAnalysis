"""
app.py

Streamlit front end for the Monte Carlo portfolio risk simulator.

Run locally:
    streamlit run app.py

All numerical work happens in src/core.py; this file only collects inputs,
validates them, and draws the results.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import core

# ---- limits that keep a small public server responsive -----------------
MAX_TICKERS = 10
MAX_DAYS = 756            # 3 trading years
MIN_HISTORY_DAYS = 250    # need about a year of overlapping prices
TRADING_DAYS = 252
TICKER_PATTERN = re.compile(r"^[A-Z0-9.\-^=]{1,12}$")

REPO_URL = "https://github.com/holiday-sean/StockPortfolioRiskAnalysis"

DEFAULT_HOLDINGS = pd.DataFrame({"Ticker": ["VTI", "BND"], "Weight (%)": [60.0, 40.0]})

BLUE = "#2a78d6"
BLUE_FILL = "rgba(42, 120, 214, {a})"
RED = "#d64545"
GREY = "#8a8f98"


st.set_page_config(page_title="Portfolio Risk Simulator", page_icon="📉", layout="wide")


# ------------------------------------------------------------ helpers

def money(v):
    return f"-${abs(v):,.0f}" if v < 0 else f"${v:,.0f}"


def pct(v, digits=1):
    return f"{v * 100:.{digits}f}%"


@st.cache_data(ttl=3600, show_spinner=False)
def load_prices(tickers, period):
    """Cached so repeat runs with the same tickers don't hit Yahoo again."""
    return core.get_prices(list(tickers), period=period)


def parse_holdings(holdings):
    """Validate the holdings table. Returns (tickers, weights Series)."""
    df = holdings.copy()
    df["Ticker"] = df["Ticker"].astype("string").str.strip().str.upper()
    df = df[df["Ticker"].notna() & (df["Ticker"] != "")]

    if df.empty:
        raise ValueError("Add at least one ticker.")
    if len(df) > MAX_TICKERS:
        raise ValueError(f"Please use at most {MAX_TICKERS} tickers.")
    if df["Ticker"].duplicated().any():
        dupes = ", ".join(df.loc[df["Ticker"].duplicated(), "Ticker"])
        raise ValueError(f"Each ticker can appear once (duplicate: {dupes}).")
    bad = [t for t in df["Ticker"] if not TICKER_PATTERN.match(t)]
    if bad:
        raise ValueError(f"These don't look like ticker symbols: {', '.join(bad)}.")

    weights = pd.to_numeric(df["Weight (%)"], errors="coerce")
    if weights.isna().any() or (weights <= 0).any():
        raise ValueError("Every ticker needs a weight greater than 0.")

    weights.index = df["Ticker"].tolist()
    return df["Ticker"].tolist(), weights.astype(float)


def run_analysis(holdings, period, start_value, years, n_trials, conf_level):
    tickers, weights = parse_holdings(holdings)
    n_days = int(round(years * TRADING_DAYS))
    if n_days > MAX_DAYS:
        raise ValueError("Horizon is too long for this demo.")

    prices = load_prices(tuple(tickers), period)
    if len(prices) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Only {len(prices)} days of overlapping price history were found for "
            f"{', '.join(tickers)}. At least {MIN_HISTORY_DAYS} are needed; one of the "
            "tickers may be a recent listing. Try removing it or choosing a longer history."
        )

    result = core.analyze_portfolio(prices, weights, n_trials, n_days,
                                    start_value, conf_level)
    result["settings"] = {
        "start_value": start_value, "n_days": n_days, "n_trials": result["paths"].shape[0],
        "conf_level": conf_level, "period": period,
        "first_date": prices.index.min(), "last_date": prices.index.max(),
        "n_history_days": len(prices),
    }
    return result


# ------------------------------------------------------------- charts

def fan_chart(paths, n_days):
    days = np.arange(n_days + 1)
    p5, p25, p50, p75, p95 = np.percentile(paths.values, [5, 25, 50, 75, 95], axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=p95, line=dict(width=0), showlegend=False,
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=days, y=p5, line=dict(width=0), fill="tonexty",
                             fillcolor=BLUE_FILL.format(a=0.15), name="5th–95th percentile",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=days, y=p75, line=dict(width=0), showlegend=False,
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=days, y=p25, line=dict(width=0), fill="tonexty",
                             fillcolor=BLUE_FILL.format(a=0.3), name="25th–75th percentile",
                             hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=days, y=p50, line=dict(color=BLUE, width=2.5), name="Median",
                             hovertemplate="Day %{x}<br>Median: $%{y:,.0f}<extra></extra>"))
    fig.add_hline(y=paths.iloc[0, 0], line=dict(color=GREY, dash="dash", width=1))
    fig.update_layout(
        title="Range of portfolio values over time",
        xaxis_title="Trading days", yaxis_title="Portfolio value ($)",
        yaxis_tickprefix="$", yaxis_tickformat=",.0f",
        legend=dict(orientation="h", y=-0.2), margin=dict(t=50, b=10), height=420,
    )
    return fig


def ending_value_chart(paths, var_value, conf_level):
    start = paths.iloc[0, 0]
    ending = paths.iloc[:, -1]
    fig = go.Figure(go.Histogram(x=ending, nbinsx=60, marker_color=BLUE,
                                 hovertemplate="$%{x:,.0f}<br>%{y} trials<extra></extra>"))
    fig.add_vline(x=start, line=dict(color=GREY, dash="dash"),
                  annotation_text="Start", annotation_position="top")
    fig.add_vline(x=start + var_value, line=dict(color=RED, dash="dash"),
                  annotation_text=f"VaR {conf_level:.0%}", annotation_position="top left")
    fig.update_layout(title="Ending portfolio value", xaxis_title="Value at the end ($)",
                      yaxis_title="Simulations", xaxis_tickprefix="$", xaxis_tickformat=",.0f",
                      showlegend=False, margin=dict(t=50, b=10), height=340)
    return fig


def drawdown_chart(mdd):
    fig = go.Figure(go.Histogram(x=mdd * 100, nbinsx=50, marker_color=BLUE,
                                 hovertemplate="%{x:.1f}%<br>%{y} trials<extra></extra>"))
    fig.add_vline(x=float(mdd.median() * 100), line=dict(color=GREY, dash="dash"),
                  annotation_text="Median", annotation_position="top")
    fig.update_layout(title="Worst peak-to-trough drop along each path",
                      xaxis_title="Maximum drawdown (%)", yaxis_title="Simulations",
                      showlegend=False, margin=dict(t=50, b=10), height=340)
    return fig


def risk_contribution_chart(contrib, weights):
    order = contrib.sort_values()
    fig = go.Figure(go.Bar(
        x=order.values, y=order.index, orientation="h", marker_color=BLUE,
        text=[f"{v:.1f}%" for v in order.values], textposition="outside",
        hovertemplate="%{y}: %{x:.1f}% of risk<extra></extra>",
    ))
    fig.update_layout(title="Share of portfolio risk by holding",
                      xaxis_title="Contribution to portfolio variance (%)",
                      xaxis=dict(range=[min(0, order.min() * 1.2), order.max() * 1.2 + 1]),
                      margin=dict(t=50, b=10), height=max(260, 60 * len(order) + 120))
    return fig


def correlation_chart(cov):
    sd = np.sqrt(np.diag(cov.values))
    corr = cov.values / np.outer(sd, sd)
    fig = go.Figure(go.Heatmap(
        z=corr, x=cov.columns, y=cov.index, zmin=-1, zmax=1, colorscale="RdBu_r",
        text=np.round(corr, 2), texttemplate="%{text}",
        hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(title="How the holdings move together (correlation)",
                      yaxis_autorange="reversed", margin=dict(t=50, b=10),
                      height=max(260, 60 * len(cov) + 120))
    return fig


# ------------------------------------------------------------- layout

def render_results(result):
    s = result["settings"]
    summary = result["summary"]
    paths = result["paths"]
    start = s["start_value"]
    conf = s["conf_level"]

    var_value = summary["VaR"] * start
    cvar_value = summary["CVaR"] * start
    median_end = float(paths.iloc[:, -1].median())

    st.caption(
        f"{s['n_trials']:,} simulated paths over {s['n_days']} trading days "
        f"(≈ {s['n_days'] / TRADING_DAYS:.1f} years), based on daily prices from "
        f"{s['first_date']:%b %d, %Y} to {s['last_date']:%b %d, %Y}."
    )

    cols = st.columns(6)
    cols[0].metric("Median ending value", money(median_end))
    cols[1].metric("Chance of a loss", pct(summary["prob_of_loss"], 0))
    cols[2].metric(f"VaR ({conf:.0%})", money(var_value))
    cols[3].metric(f"CVaR ({conf:.0%})", money(cvar_value) if np.isfinite(cvar_value) else "n/a")
    cols[4].metric("Median max drawdown", pct(summary["MDD_median"], 0))
    cols[5].metric("Bad-case drawdown", pct(summary["MDD_p5_worst_case"], 0),
                   help="5% of simulated paths had a deeper peak-to-trough drop than this.")

    st.info(
        f"**In plain terms:** in {pct(summary['prob_of_loss'], 0)} of simulations the portfolio "
        f"ended below its {money(start)} starting value. In the worst {1 - conf:.0%} of outcomes "
        f"it lost at least {money(abs(var_value))}"
        + (f", and the average loss within that worst slice was {money(abs(cvar_value))}."
           if np.isfinite(cvar_value) else ".")
    )

    st.plotly_chart(fan_chart(paths, s["n_days"]), width='stretch')

    left, right = st.columns(2)
    left.plotly_chart(ending_value_chart(paths, var_value, conf), width='stretch')
    right.plotly_chart(drawdown_chart(result["mdd"]), width='stretch')

    left, right = st.columns(2)
    left.plotly_chart(risk_contribution_chart(result["risk_contributions"], result["weights"]),
                      width='stretch')
    if len(result["cov"]) > 1:
        right.plotly_chart(correlation_chart(result["cov"]), width='stretch')
    else:
        right.info("Add a second holding to see how the holdings move together.")

    stats = result["stats"]
    table = pd.DataFrame({
        "Weight": (result["weights"] * 100).round(1).astype(str) + "%",
        "Avg annual return": (stats["mean_return"] * TRADING_DAYS * 100).round(1).astype(str) + "%",
        "Annual volatility": (np.sqrt(stats["variance"] * TRADING_DAYS) * 100).round(1).astype(str) + "%",
        "Tail heaviness (t d.o.f.)": stats["degree_of_freedom"].round(1),
    })
    table.index.name = "Ticker"
    st.subheader("Holdings, as measured from history")
    st.dataframe(table, width='stretch')

    summary_csv = pd.DataFrame([{**summary, "starting_value": start, "n_days": s["n_days"]}])
    st.download_button("Download summary as CSV", summary_csv.to_csv(index=False),
                       file_name="simulation_summary.csv", mime="text/csv")

    with st.expander("How to read this, and what it doesn't tell you"):
        st.markdown(
            f"""
- **VaR** is the loss that only {1 - conf:.0%} of simulated outcomes exceed. **CVaR** is the
  average loss *inside* that worst slice, so it is always at least as bad as VaR.
- **Max drawdown** is the biggest drop from a running peak along each path, which matters
  because a portfolio can recover by the end yet still hurt along the way.
- The simulation assumes the **historical average return and volatility** continue. If the
  history window included an unusual period (for example the 2022 rate hikes for bonds), the
  results will lean on it. It's a "what if the future resembles the last {s['period']}?"
  scenario, not a forecast.
- Daily returns are drawn from a **Student's t** distribution (fat tails) and correlated
  through the covariance matrix. This is a common approximation, not a full multivariate
  t model. There is no rebalancing, trading cost, tax, or contribution.
- Weights are percentages of your starting value; prices are assumed to be in USD.
            """
        )


def main():
    st.title("Portfolio Risk Simulator")
    st.markdown(
        "See the range of outcomes your portfolio could face, using a Monte Carlo simulation "
        "calibrated to real price history. "
        f"[Source code and methodology on GitHub]({REPO_URL})."
    )

    with st.sidebar:
        st.header("Your portfolio")
        holdings = st.data_editor(
            DEFAULT_HOLDINGS, num_rows="dynamic", hide_index=True, key="holdings",
            width='stretch',
            column_config={
                "Ticker": st.column_config.TextColumn(help="Yahoo Finance symbol, e.g. VTI, AAPL"),
                "Weight (%)": st.column_config.NumberColumn(min_value=0.0, max_value=100.0,
                                                           step=1.0, format="%.1f"),
            },
        )
        st.caption(f"Up to {MAX_TICKERS} holdings. Weights are rescaled to 100%.")

        st.header("Simulation")
        start_value = st.number_input("Starting value ($)", min_value=100.0, max_value=1e9,
                                      value=10000.0, step=1000.0)
        years = st.slider("Horizon (years)", 0.25, 3.0, 1.0, 0.25)
        n_trials = st.select_slider("Simulations", options=[500, 1000, 2000, 5000], value=2000)
        conf_level = st.select_slider("Confidence level", options=[0.90, 0.95, 0.99], value=0.95,
                                      format_func=lambda v: f"{v:.0%}")
        period = st.selectbox("Price history", ["3y", "5y", "10y"], index=1)
        run_clicked = st.button("Run simulation", type="primary", width='stretch')

    if run_clicked or "result" not in st.session_state:
        try:
            with st.spinner("Fetching prices and simulating..."):
                st.session_state["result"] = run_analysis(
                    holdings, period, start_value, years, n_trials, conf_level)
            st.session_state.pop("error", None)
        except ValueError as exc:
            st.session_state["result"], st.session_state["error"] = None, str(exc)
        except Exception:
            st.session_state["result"] = None
            st.session_state["error"] = (
                "Something went wrong while fetching data or running the simulation. "
                "Please check the tickers and try again."
            )

    if st.session_state.get("error"):
        st.error(st.session_state["error"])
    if st.session_state.get("result") is not None:
        render_results(st.session_state["result"])


main()
