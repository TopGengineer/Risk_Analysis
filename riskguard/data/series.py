# riskguard/data/series.py
import numpy as np
import pandas as pd
from ..config import OUTLIER_JUMP_DAILY
from ..db.repo import get_price_df
from .normalize import ohlcv_by_day

def _consistent_adj_close_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    g = df.copy()
    g.index = pd.to_datetime(g.index).tz_localize(None)
    c = pd.to_numeric(g["Close"], errors="coerce")
    ac = pd.to_numeric(g.get("AdjClose", pd.Series(index=g.index, dtype=float)), errors="coerce")
    factor = (ac / c).replace([np.inf, -np.inf], np.nan).ffill().bfill().fillna(1.0)
    adj = c * factor
    return adj.dropna()

def daily_close_series_from_raw(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    s = _consistent_adj_close_series(df)
    if s.empty:
        s = pd.to_numeric(df["Close"], errors="coerce")
        s.index = pd.to_datetime(df.index).tz_localize(None)
    s.index = s.index.normalize()
    return s.groupby(s.index).last().sort_index().astype(float)

def patch_outliers_series(s: pd.Series, max_jump: float = OUTLIER_JUMP_DAILY) -> pd.Series:
    if s is None or len(s) < 5:
        return s if s is not None else pd.Series(dtype=float)
    r = s.pct_change()
    med = r.rolling(21, center=True, min_periods=8).median()
    mad = (r - med).abs().rolling(21, center=True, min_periods=8).median()
    z = (r - med) / mad.replace(0.0, np.nan)
    big_abs = r.abs() > max_jump
    big_z   = z.abs() > 8
    big = big_abs & big_z
    iso = big & (~big.shift(1).fillna(False)) & (~big.shift(-1).fillna(False))
    if not iso.any():
        return s
    s2 = s.copy()
    idx = np.where(iso)[0]
    for i in idx:
        if 0 < i < len(s2)-1:
            s2.iloc[i] = 0.5 * (s2.iloc[i-1] + s2.iloc[i+1])
        else:
            s2.iloc[i] = s2.iloc[i-1] if i > 0 else s2.iloc[i+1]
    return s2

def daily_price_series(session, ticker: str) -> pd.Series:
    df = get_price_df(session, ticker)
    if df is None or df.empty:
        return pd.Series(dtype=float, name=ticker)
    s = daily_close_series_from_raw(df)
    s = patch_outliers_series(s)
    s.name = ticker
    return s
