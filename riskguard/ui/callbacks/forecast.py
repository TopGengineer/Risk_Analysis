# riskguard/ui/callbacks/forecast.py
from dash import Input, Output, State
import plotly.graph_objects as go
from ...db.base import SessionLocal
from ...db.repo import ensure_history
from ...data.series import daily_price_series
from ...risk.forecast import forecast_series

def register_forecast_callbacks(app):
    @app.callback(
        Output("forecast-graph","figure"),
        Input("fc-run","n_clicks"),
        State("fc-ticker","value"),
        State("fc-horizon","value"),
        State("risk-alpha","value"),
        prevent_initial_call=True
    )
    def run_forecast(_n, ticker, horizon, alpha):
        if not ticker:
            return go.Figure()
        horizon = int(horizon or 30); alpha = float(alpha or 0.95)
        ticker = ticker.upper().strip()
        with SessionLocal() as s:
            ensure_history(s, [ticker])
            close = daily_price_series(s, ticker)
            if close.empty:
                return go.Figure()
        fc, lo, hi, method = forecast_series(close, steps=horizon, alpha=alpha)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=close.index, y=close.values, mode="lines", name="History"))
        if len(fc):
            fig.add_trace(go.Scatter(x=fc.index, y=fc.values, mode="lines", name=f"Forecast • {method}"))
            if lo is not None and hi is not None:
                fig.add_trace(go.Scatter(x=fc.index, y=hi, line=dict(width=0), showlegend=False))
                fig.add_trace(go.Scatter(x=fc.index, y=lo, fill="tonexty", line=dict(width=0),
                                         name=f"{int(alpha*100)}% CI", opacity=0.2))
        fig.update_layout(title=f"{ticker} Forecast ({method})", margin=dict(l=10,r=10,t=30,b=10), height=420)
        fig.update_xaxes(rangeslider_visible=False)
        return fig
