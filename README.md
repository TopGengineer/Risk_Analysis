# RiskGuard Core v5.2 — Daily-Stable, Spike-Proof Portfolio Risk

RiskGuard is a Dash/Plotly app that turns **daily market data** into a clean portfolio dashboard: line/candle charts, rolling volatility, correlation, **VaR/ES**, stress tests, buy-&-hold backtests, and simple forecasts — all built on a spike-resistant **daily adjusted-close** series stored in SQLite (with `yfinance` as source and a simulated fallback).

---

## Features
- **Daily-only writes** (1d bars) with **15% jump guard** to skip bad ticks.
- **Continuous adjusted close** via `(AdjClose/Close)` factor (ffill/bfill; hard fallback to Close).
- **Isolated spike patching** (>18% daily jump + robust z-score) to avoid “Gibbs-like” artifacts.
- One consistent, aligned **daily grid** for charts, risk, correlation, and backtest.
- Portfolio table shows **Current Price / Market Value / P&L / P&L %**.
- Risk cards: **Ann. Vol**, **Sharpe**, **Max Drawdown**, **VaR/ES (Parametric or Historical)**.
- Plots: **Rolling 21-day volatility** and **correlation heatmap**.
- **Stress tests** (−5% / −10% / −20%) and **worst 20-day window**.
- **Backtest** (buy-&-hold) vs `SPY` with CAGR/Vol/Sharpe/MaxDD.
- **Forecasts**: Gradient-Boosting Quantile (with CI) → SARIMAX → drift fallback.

---

## Requirements
Create `requirements.txt` (Python 3.10+):
    dash==2.17.1
    dash-bootstrap-components==1.6.0
    plotly==5.23.0
    pandas>=2.0,<3.0
    numpy>=1.24,<2.0
    yfinance>=0.2.40
    SQLAlchemy>=2.0
    requests>=2.31
    scikit-learn>=1.3
    statsmodels>=0.14
    scipy>=1.11

---

## Install & Run
    git clone <YOUR-REPO-URL>
    cd <YOUR-REPO-DIR>

    python -m venv .venv
    # Windows
    .\.venv\Scripts\Activate.ps1
    # macOS/Linux
    source .venv/bin/activate

    pip install -r requirements.txt
    python app.py

- First run creates `riskguard_core.db`, **repairs `adj_close`** if missing, seeds sample positions (AAPL/MSFT/SPY), fetches 1d bars, and opens `http://127.0.0.1:8050`.
- **Reset DB** anytime by deleting `riskguard_core.db` and running again.

---

## How To Use
- **Portfolio (left panel)**: pick a ticker, enter **Qty** and **Cost**, click **Save/Update** (or **Delete**). The table fills **Current Price / MV / P&L / P&L %** automatically.
- **Charts**: choose **Line** (clean adjusted close; patched spikes) or **Candlestick** (true daily OHLC + volume). Lookback: **3M / 6M / 1Y / 3Y / MAX**.
- **Risk**: choose **Parametric** or **Historical** and confidence (90/95/99%). Cards show Ann. Vol, Sharpe, MaxDD, VaR, ES. Plots: **rolling 21d vol** + **correlation heatmap**.
- **Stress Test**: click −5%/−10%/−20% to see instant P/L estimate and the **worst 20-day window**.
- **Backtest**: pick start date; runs buy-&-hold using current MV weights vs **SPY**. Outputs metrics + indexed equity curves.
- **Forecast**: select ticker & horizon (e.g., 30). Uses GB Quantile (with CI) → SARIMAX → drift.

---

## Configuration (edit `config.py` or the constants at the top of `app.py`)
- `DATABASE_URL = "sqlite:///riskguard_core.db"`
- `DEFAULT_TICKERS = ["AAPL", "MSFT", "SPY"]`
- `BENCHMARK = "SPY"`
- `UPDATE_MS = 15000` (UI refresh)
- Outlier guards: updater skip `> 15%` DoD jump; line patch `> 18%` jump **and** high robust z-score.

---

## Project Structure (recommended)
    riskguard/
      app.py                      # Dash entrypoint (layout + callbacks + server)
      bootstrap.py                # Schema/repair (adj_close), initial seeding
      config.py                   # Constants: DB URL, tickers, thresholds

      db/
        base.py                   # SQLAlchemy Base + engine/session factory
        models.py                 # ORM models: Symbol, Price, Position
        repo.py                   # CRUD helpers (upserts, queries, ensure_history)

      data/
        fetch.py                  # yfinance fetch + simulated fallback
        normalize.py              # normalize_price_frame, OHLCV aggregation
        series.py                 # adjusted-close builder, outlier patching, lookbacks
        updates.py                # daily-only updater with 15% jump guard

      risk/
        portfolio.py              # dynamic portfolio returns (coverage-aware)
        metrics.py                # VaR/ES, rolling vol, drawdown, backtest stats
        forecast.py               # GB Quantile / SARIMAX / drift

      ui/
        layout.py                 # components & layout
        callbacks/
          positions.py            # CRUD + table refresh
          charts.py               # line/candle
          risk.py                 # cards + rolling vol + correlation heatmap
          stress.py               # stress test + worst window
          backtest.py             # buy-&-hold vs benchmark
          forecast.py             # forecast graph

You can run monolith `app.py` first, then migrate into this structure — behavior stays the same.

---

## Troubleshooting
- **Portfolio P&L fields empty**: ensure Qty/Cost are numeric. The updater writes **daily** bars only; give it a moment. If offline, simulated prices still compute P&L.
- **Weird single-day spike/double peak**: updater skips >15% DoD; line series patches **isolated** glitches (>18% + robust z). True splits/dividends stabilize after next daily bar.
- **Backtest “no overlap”**: pick a later start date or remove assets with sparse history.
- **Old DB missing `adj_close`**: auto-repair runs at startup (backfills from `close`).

---

## Notes & Safety
- For research/education only — **not** investment advice.
- Yahoo Finance can lag/revise; verify before decisions. Respect data provider ToS.

---

## License
Add a `LICENSE` file (e.g., MIT) suitable for your use.

---

## Acknowledgments
Data: `yfinance` • UI: Dash + dash-bootstrap-components • Charts: Plotly • Forecasts: scikit-learn, statsmodels • Stats: scipy
