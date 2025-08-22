# riskguard/db/repo.py
import numpy as np
import pandas as pd
from sqlalchemy import text
from .base import SessionLocal
from .models import Symbol, Price, Position
from ..data.fetch import fetch_history, fetch_history_real
from ..data.normalize import normalize_price_frame

def upsert_symbol(session, ticker: str) -> Symbol:
    t = ticker.upper().strip()
    sym = session.query(Symbol).filter(Symbol.ticker == t).one_or_none()
    if not sym:
        sym = Symbol(ticker=t, name=t)
        session.add(sym); session.commit()
    return sym

def bulk_upsert_prices(session, ticker: str, df: pd.DataFrame, adj_col_exists: bool = True):
    df = normalize_price_frame(df)
    if df is None or df.empty:
        return
    sym = upsert_symbol(session, ticker)

    if adj_col_exists:
        sql = """
        INSERT INTO prices (symbol_id, dt, open, high, low, close, volume, adj_close)
        VALUES (:sid, :dt, :open, :high, :low, :close, :volume, :adj_close)
        ON CONFLICT(symbol_id, dt) DO UPDATE SET
            open = excluded.open, high = excluded.high, low  = excluded.low,
            close= excluded.close, volume = excluded.volume, adj_close = excluded.adj_close
        """
    else:
        sql = """
        INSERT INTO prices (symbol_id, dt, open, high, low, close, volume)
        VALUES (:sid, :dt, :open, :high, :low, :close, :volume)
        ON CONFLICT(symbol_id, dt) DO UPDATE SET
            open = excluded.open, high = excluded.high, low  = excluded.low,
            close= excluded.close, volume = excluded.volume
        """

    recs = []
    for dt_, o, h, l, c, adj, v in df[["Open","High","Low","Close","AdjClose","Volume"]].itertuples(index=True, name=None):
        recs.append({
            "sid": sym.id,
            "dt": pd.Timestamp(dt_).to_pydatetime().replace(tzinfo=None),
            "open": float(o) if pd.notna(o) else float(c),
            "high": float(h) if pd.notna(h) else float(c),
            "low":  float(l) if pd.notna(l) else float(c),
            "close": float(c),
            "volume": float(v) if pd.notna(v) else 0.0,
            "adj_close": float(adj) if pd.notna(adj) else float(c),
        })
    if recs:
        session.execute(text(sql), recs)
        session.commit()

def ensure_history(session, tickers):
    for t in tickers:
        df = fetch_history_real(t)
        if df is None or df.empty:
            sym = upsert_symbol(session, t)
            exists = session.query(Price.id).filter(Price.symbol_id == sym.id).limit(1).first()
            if exists:
                continue
            df = fetch_history(t)
        bulk_upsert_prices(session, t, df)

def get_price_df(session, ticker: str) -> pd.DataFrame:
    sym = session.query(Symbol).filter(Symbol.ticker == ticker.upper()).one_or_none()
    if not sym:
        return pd.DataFrame()
    rows = session.query(Price).filter(Price.symbol_id == sym.id).order_by(Price.dt.asc()).all()
    if not rows:
        return pd.DataFrame()
    data = []
    for r in rows:
        adj = getattr(r, "adj_close", None)
        data.append((r.dt, r.open, r.high, r.low, r.close, adj, r.volume))
    df = pd.DataFrame(data, columns=["Date","Open","High","Low","Close","AdjClose","Volume"]).set_index("Date")
    df.index = pd.to_datetime(df.index).tz_localize(None)
    return df

def positions_df(session) -> pd.DataFrame:
    rows = session.execute(text(
        "SELECT s.ticker, COALESCE(s.name, s.ticker) as name, p.quantity, p.cost_basis "
        "FROM positions p JOIN symbols s ON s.id=p.symbol_id ORDER BY s.ticker"
    )).fetchall()
    return pd.DataFrame(rows, columns=["Ticker","Name","Quantity","Cost Basis"])
