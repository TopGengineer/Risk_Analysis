# riskguard/ui/callbacks/stress.py
from dash import Input, Output
import dash
from ...db.base import SessionLocal
from .positions import build_positions_view
from ...data.series import daily_price_series
from ...risk.portfolio import portfolio_returns_dynamic, worst_window_stats
import pandas as pd

def register_stress_callbacks(app):
    @app.callback(
        Output("stress-out","children"),
        Output("worst-window-out","children"),
        Input("stress-5","n_clicks"),
        Input("stress-10","n_clicks"),
        Input("stress-20","n_clicks"),
        prevent_initial_call=True
    )
    def run_stress(n5, n10, n20):
        clicks = [(n5 or 0), (n10 or 0), (n20 or 0)]
        if max(clicks) == 0:
            return dash.no_update, dash.no_update
        shock = [-0.05, -0.10, -0.20][clicks.index(max(clicks))]

        frames, weights, total_value = {}, {}, 0.0
        with SessionLocal() as s:
            view = build_positions_view(s)
            if view is None or view.empty:
                return "Add positions to run a stress test.", ""
            total_value = float(pd.to_numeric(view["Market Value"], errors="coerce").sum())
            for t in view["Ticker"]:
                ser = daily_price_series(s, t)
                if len(ser):
                    frames[t] = ser
            if not frames:
                return "No price history available.", ""
            weights = (view.set_index("Ticker")["Market Value"] / total_value).to_dict()

        port_ret = portfolio_returns_dynamic(frames, weights)
        if port_ret.empty:
            return "Insufficient history for stress test.", ""

        pnl_pct = shock; pnl_usd = total_value * pnl_pct
        stress_msg = f"Shock {int(shock*100)}% ⇒ Estimated P/L: {pnl_pct:.2%} (~${pnl_usd:,.0f})"
        ww = worst_window_stats(port_ret, window=20)
        ww_msg = f"Worst 20d window: {ww['start']} → {ww['end']} : {ww['ret']:.2%}" if ww else "Not enough data for 20-day window."
        return stress_msg, ww_msg
