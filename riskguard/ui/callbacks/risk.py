# riskguard/ui/callbacks/risk.py
from dash import Input, Output, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from ...db.base import SessionLocal
from .positions import build_positions_view
from ...data.series import daily_price_series
from ...risk.portfolio import portfolio_returns_dynamic
from ...risk.metrics import parametric_var_es, historical_var_es
from ...utils.dates import parse_lookback_series  # not used here but handy

def register_risk_callbacks(app):
    @app.callback(
        Output("risk-cards","children"),
        Output("rolling-vol-graph","figure"),
        Output("corr-heat","figure"),
        Input("tick","n_intervals"),
        Input("risk-alpha","value"),
        Input("risk-method","value"),
    )
    def risk_views(_n, alpha, method):
        with SessionLocal() as s:
            view = build_positions_view(s)
            if view is None or view.empty:
                cards = dbc.Row([dbc.Col(dbc.Alert("No positions in portfolio.", color="info"))])
                return cards, go.Figure(), go.Figure()

            total_value = float(pd.to_numeric(view["Market Value"], errors="coerce").sum())
            if not np.isfinite(total_value) or total_value <= 0:
                cards = dbc.Row([dbc.Col(dbc.Alert("Portfolio value is zero.", color="warning"))])
                return cards, go.Figure(), go.Figure()

            weights = (view.set_index("Ticker")["Market Value"] / total_value).to_dict()
            frames = {}
            for t in view["Ticker"]:
                ser = daily_price_series(s, t)
                if len(ser):
                    frames[t] = ser

        if not frames:
            cards = dbc.Row([dbc.Col(dbc.Alert("No price history available.", color="warning"))])
            return cards, go.Figure(), go.Figure()

        port_ret = portfolio_returns_dynamic(frames, weights, min_coverage=0.7)

        prices = pd.concat(frames.values(), axis=1).sort_index()
        asset_rets = prices.pct_change().loc[port_ret.index].dropna(how="all")

        ann_vol = float(port_ret.std(ddof=1) * np.sqrt(252)) if len(port_ret) else float("nan")
        sharpe  = float((port_ret.mean() / port_ret.std(ddof=1)) * np.sqrt(252)) if port_ret.std(ddof=1) > 0 else float("nan")
        equity  = (1 + port_ret).cumprod()
        mdd     = float((equity / equity.cummax() - 1).min()) if len(equity) else float("nan")

        if method == "param":
            var_val, es_val = parametric_var_es(port_ret, alpha)
            v_label, e_label = f"VaR {int(alpha*100)}% (Param)", f"ES {int(alpha*100)}% (Param)"
        else:
            var_val, es_val = historical_var_es(port_ret, alpha)
            v_label, e_label = f"VaR {int(alpha*100)}% (Hist)", f"ES {int(alpha*100)}% (Hist)"

        cards = dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Ann. Volatility"), html.H4(f"{ann_vol:.2%}" if np.isfinite(ann_vol) else "n/a")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Sharpe Ratio"),  html.H4(f"{sharpe:.2f}" if np.isfinite(sharpe) else "n/a")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div("Max Drawdown"),  html.H4(f"{mdd:.2%}" if np.isfinite(mdd) else "n/a")])), md=2),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div(v_label),         html.H4(f"{var_val:.2%}" if np.isfinite(var_val) else "n/a")])), md=3),
            dbc.Col(dbc.Card(dbc.CardBody([html.Div(e_label),         html.H4(f"{es_val:.2%}" if np.isfinite(es_val) else "n/a")])), md=3),
        ], className="gy-2")

        rv = port_ret.rolling(21).std(ddof=1) * np.sqrt(252)
        vol_fig = go.Figure()
        if len(rv):
            vol_fig.add_trace(go.Scatter(x=rv.index, y=rv, mode="lines", name="21d Rolling Vol"))
        vol_fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=280)

        corr_fig = go.Figure()
        if not asset_rets.empty:
            cm = asset_rets.corr()
            corr_fig.add_trace(go.Heatmap(z=cm.values, x=cm.columns, y=cm.index, zmin=-1, zmax=1, colorscale="RdBu"))
            corr_fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=320)

        return cards, vol_fig, corr_fig
