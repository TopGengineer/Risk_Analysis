# riskguard/ui/callbacks/positions.py
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from ...db.base import SessionLocal
from ...db.repo import positions_df, upsert_symbol, bulk_upsert_prices, ensure_history
from ...utils.search import search_symbols
from ...data.fetch import fetch_history
from ...data.updates import update_latest_prices

def build_positions_view(session) -> pd.DataFrame:
    pos = positions_df(session)
    if pos.empty:
        return pos
    from ...data.series import daily_price_series
    last_prices = []
    for t in pos["Ticker"]:
        ser = daily_price_series(session, t)
        last_prices.append(float(ser.iloc[-1]) if len(ser) else np.nan)
    pos = pos.copy()
    pos["Current Price"] = pd.to_numeric(last_prices, errors="coerce")
    pos["Market Value"]  = pd.to_numeric(pos["Quantity"], errors="coerce") * pos["Current Price"]
    pos["P/L"]           = (pos["Current Price"] - pd.to_numeric(pos["Cost Basis"], errors="coerce")) * pd.to_numeric(pos["Quantity"], errors="coerce")
    denom = (pd.to_numeric(pos["Quantity"], errors="coerce") * pd.to_numeric(pos["Cost Basis"], errors="coerce"))
    pos["P/L %"]         = np.where(denom>0, (pos["P/L"]/denom)*100.0, np.nan)
    return pos

def register_positions_callbacks(app):
    @app.callback(Output("pos-ticker","options"), Input("pos-ticker","search_value"))
    def suggest_pos(q): return search_symbols(q)

    @app.callback(Output("fc-ticker","options"), Input("fc-ticker","search_value"))
    def suggest_fc(q): return search_symbols(q)

    @app.callback(Output("chart-tickers","options"),
                  Input("chart-tickers","search_value"),
                  State("chart-tickers","value"))
    def suggest_chart(q, selected):
        opts = search_symbols(q)
        selected = selected or []
        keep = [{"label": v, "value": v} for v in selected if v and v not in [o["value"] for o in opts]]
        return keep + opts

    @app.callback(
        Output("pos-msg","children"),
        Input("pos-save","n_clicks"),
        State("pos-ticker","value"),
        State("pos-qty","value"),
        State("pos-cost","value"),
        prevent_initial_call=True
    )
    def save_position(_n, ticker, qty, cost):
        if not ticker or qty is None or cost is None:
            return dbc.Alert("Fill symbol, quantity, and cost.", color="warning")
        ticker = ticker.strip().upper()
        with SessionLocal() as s:
            df = fetch_history(ticker)
            bulk_upsert_prices(s, ticker, df, adj_col_exists=True)
            sym = upsert_symbol(s, ticker)
            from ...db.models import Position
            pos = s.query(Position).filter(Position.symbol_id==sym.id).one_or_none()
            if pos:
                pos.quantity = float(qty); pos.cost_basis = float(cost)
            else:
                s.add(Position(symbol_id=sym.id, quantity=float(qty), cost_basis=float(cost)))
            s.commit()
        return dbc.Alert(f"Saved {ticker}.", color="success")

    @app.callback(
        Output("pos-msg","children", allow_duplicate=True),
        Input("pos-del","n_clicks"),
        State("pos-ticker","value"),
        prevent_initial_call=True
    )
    def delete_position_cb(_n, ticker):
        if not ticker:
            return dbc.Alert("Select a symbol to delete.", color="warning")
        ticker = ticker.strip().upper()
        with SessionLocal() as s:
            from ...db.models import Position, Symbol
            sym = s.query(Symbol).filter(Symbol.ticker==ticker).one_or_none()
            if not sym:
                return dbc.Alert(f"No such symbol: {ticker}.", color="danger")
            s.query(Position).filter(Position.symbol_id==sym.id).delete()
            s.commit()
        return dbc.Alert(f"Deleted {ticker}.", color="info")

    @app.callback(
        Output("positions-table","data"),
        Output("positions-table","columns"),
        Input("tick","n_intervals"),
        Input("pos-msg","children")
    )
    def refresh_positions(_n, _msg):
        with SessionLocal() as s:
            pos = positions_df(s)
            tickers = list(pos["Ticker"]) if not pos.empty else []
            if tickers:
                try:
                    ensure_history(s, tickers)
                    update_latest_prices(s, tickers)
                except Exception:
                    pass
            view = build_positions_view(s)
            full_cols = ["Ticker","Name","Quantity","Cost Basis","Current Price","Market Value","P/L","P/L %"]
            cols = [{"name":c,"id":c} for c in full_cols]
            if view.empty:
                return [], cols
            for c in full_cols:
                if c not in view.columns:
                    view[c] = np.nan
            view = view[full_cols]
            return view.round(4).replace([np.inf,-np.inf], np.nan).to_dict("records"), cols
