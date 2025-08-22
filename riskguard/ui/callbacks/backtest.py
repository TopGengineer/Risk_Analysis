# riskguard/ui/callbacks/backtest.py
from dash import Input, Output, State, html
import plotly.graph_objects as go
import pandas as pd
from ...config import BENCHMARK
from ...db.base import SessionLocal
from ...db.repo import ensure_history
from .positions import build_positions_view
from ...data.series import daily_price_series
from ...risk.portfolio import portfolio_returns_dynamic
from ...risk.metrics import buy_hold_metrics

def register_backtest_callbacks(app):
    @app.callback(
        Output("bt-curve","figure"),
        Output("bt-metrics","children"),
        Input("bt-run","n_clicks"),
        State("bt-start","date"),
        prevent_initial_call=True
    )
    def run_backtest(_n, start_date):
        with SessionLocal() as s:
            view = build_positions_view(s)
            if view is None or view.empty:
                return go.Figure(), html.Div("Add positions to run a backtest.")

            total_value = float(pd.to_numeric(view["Market Value"], errors="coerce").sum())
            if total_value <= 0:
                return go.Figure(), html.Div("Portfolio value is zero — cannot backtest.")

            tickers = list(view["Ticker"])
            ensure_history(s, tickers + [BENCHMARK])

            frames = {}
            for t in tickers:
                ser = daily_price_series(s, t)
                if len(ser):
                    frames[t] = ser
            if not frames:
                return go.Figure(), html.Div("No price history found for your positions.")

            weights = (view.set_index("Ticker")["Market Value"] / total_value).to_dict()
            port_ret = portfolio_returns_dynamic(frames, weights)

            bser = daily_price_series(s, BENCHMARK)
            if bser.empty:
                return go.Figure(), html.Div(f"No history for benchmark {BENCHMARK}.")
            bench = bser.pct_change().dropna()

        common_idx = port_ret.index.intersection(bench.index)
        if common_idx.empty:
            msg = ("No overlap between portfolio and benchmark dates. "
                   "Pick a later start date or remove assets with sparse history.")
            return go.Figure(), html.Div(msg)

        start_user = pd.to_datetime(start_date) if start_date else common_idx.min()
        start_eff  = max(start_user, common_idx.min())
        port_ret = port_ret.loc[(port_ret.index >= start_eff) & (port_ret.index.isin(common_idx))]
        bench    = bench.loc[(bench.index >= start_eff) & (bench.index.isin(common_idx))]

        if len(port_ret) < 5 or len(bench) < 5:
            msg = ("Not enough overlapping data after the selected start date. "
                   "Try a later date or remove assets with very short history.")
            return go.Figure(), html.Div(msg)

        met = buy_hold_metrics(port_ret)
        eq  = (1 + port_ret).cumprod() * 100
        spy = (1 + bench).cumprod() * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eq.index,  y=eq,  mode="lines", name="Portfolio (100 = start)"))
        fig.add_trace(go.Scatter(x=spy.index, y=spy, mode="lines", name=BENCHMARK))
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=320, hovermode="x unified",
                          title=f"Backtest from {start_eff.date()}")
        fig.update_xaxes(rangeslider_visible=False)

        note = ""
        if start_date and pd.to_datetime(start_date) < start_eff:
            note = f" (adjusted from {pd.to_datetime(start_date).date()} to earliest overlap {start_eff.date()})"

        metrics_div = html.Div([
            html.Ul([
                html.Li(f"CAGR: {met.get('CAGR', float('nan')):.2%}" if 'CAGR' in met else "CAGR: n/a"),
                html.Li(f"Ann. Vol: {met.get('AnnVol', float('nan')):.2%}" if 'AnnVol' in met else "Ann. Vol: n/a"),
                html.Li(f"Sharpe: {met.get('Sharpe', float('nan')):.2f}" if 'Sharpe' in met else "Sharpe: n/a"),
                html.Li(f"Max Drawdown: {met.get('MaxDD', float('nan')):.2%}" if 'MaxDD' in met else "Max DD: n/a"),
            ]),
            html.Small(f"Start date{note}")
        ])

        return fig, metrics_div
