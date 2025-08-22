# riskguard/data/normalize.py
import numpy as np
import pandas as pd

def normalize_price_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    # Flatten MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [str(c[-1]) if isinstance(c, tuple) else str(c) for c in df.columns]
    else:
        df.columns = [str(c) for c in df.columns]

    # Standardize names
    rename_map = {
        "adj close":"AdjClose","adjclose":"AdjClose","adj_close":"AdjClose",
        "open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"
    }
    df.columns = [rename_map.get(c.strip().lower(), c.strip()) for c in df.columns]

    out = pd.DataFrame(index=pd.to_datetime(df.index, errors="coerce"))
    for col in ["Open","High","Low","Close","Volume"]:
        out[col] = pd.to_numeric(df.get(col, df.get("Close")), errors="coerce")
    out["AdjClose"] = pd.to_numeric(df.get("AdjClose", out["Close"]), errors="coerce")

    out.index = out.index.tz_localize(None)
    out = out[~out.index.duplicated(keep="last")].sort_index()
    out = out.dropna(subset=["Close"])
    out["Volume"] = out["Volume"].fillna(0.0)
    return out[["Open","High","Low","Close","AdjClose","Volume"]]

def ohlcv_by_day(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    g = df.copy()
    g.index = pd.to_datetime(g.index).tz_localize(None).normalize()
    agg = {"Open":"first","High":"max","Low":"min","Close":"last","AdjClose":"last","Volume":"sum"}
    agg = {k:v for k,v in agg.items() if k in g.columns}
    out = g.groupby(g.index).agg(agg)
    return out.sort_index().dropna(subset=["Close"])
