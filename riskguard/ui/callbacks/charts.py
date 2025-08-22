# riskguard/ui/callbacks/charts.py
from dash import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from ...db.base import SessionLocal
from ...db.repo import ensure_history, get_price_df
from ...data.series import daily_price_series
from ...data.normalize import ohlcv_by_day
from ...data.updates import update_latest_prices
from ...utils.dates import parse_lookback_df, parse_lookback_series
from ...config import DEFAULT_TICKERS

def register_charts_callbacks(app):
    @app.callback(
        Output("price-graph","figure"),
        Input("tick","n_intervals"),
        Input("chart-type","value"),
        Input("chart-tickers","value"),
        Input("chart-lookback","value"),
    )
    def update_chart(_n, ctype, tickers, lb):
        tickers = (tickers or DEFAULT_TICKERS)[:]
        with SessionLocal() as s:
            ensure_history(s, tickers)
            try:
                update_latest_prices(s, tickers)
            except Exception:
                pass

            if ctype == "line":
                fig = go.Figure()
                for t in tickers:
                    sers = daily_price_series(s, t)
                    sers = parse_lookback_series(lb, sers)
                    if sers is None or sers.empty:
                        continue
                    fig.add_trace(go.Scatter(x=sers.index, y=sers.values, mode="lines", name=t))
                fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=520, hovermode="x unified")
                fig.update_xaxes(rangeslider_visible=False)
                return fig

            # Candlestick
            t = tickers[0]
            df = get_price_df(s, t)
            df = parse_lookback_df(lb, df)
            df_daily = ohlcv_by_day(df)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75,0.25], vertical_spacing=0.05)
            if not df_daily.empty:
                fig.add_trace(go.Candlestick(
                    x=df_daily.index, open=df_daily["Open"], high=df_daily["High"],
                    low=df_daily["Low"], close=df_daily["Close"], name=t
                ), row=1, col=1)
                vol = df_daily.get("Volume", pd.Series(index=df_daily.index, dtype=float))
                fig.add_trace(go.Bar(x=df_daily.index, y=vol, name="Volume"), row=2, col=1)
            fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=620)
            fig.update_xaxes(rangeslider_visible=False)
            return fig
