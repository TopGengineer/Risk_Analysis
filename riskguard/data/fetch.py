# riskguard/data/fetch.py
import logging
from datetime import datetime
import numpy as np
import pandas as pd

try:
    import yfinance as yf
    HAVE_YF = True
except Exception:
    HAVE_YF = False

from .normalize import normalize_price_frame

log = logging.getLogger("riskguard.data.fetch")

def fetch_history_real(ticker: str, period="5y", interval="1d") -> pd.DataFrame:
    if not HAVE_YF:
        return pd.DataFrame()
    try:
        raw = yf.download(ticker, period=period, interval=interval,
                          auto_adjust=False, progress=False, threads=False)
        if isinstance(raw, pd.DataFrame) and not raw.empty:
            return normalize_price_frame(raw)
    except Exception as e:
        log.info("yfinance fetch failed %s: %s", ticker, e)
    return pd.DataFrame()

def fetch_history(ticker: str, period="5y", interval="1d") -> pd.DataFrame:
    df = fetch_history_real(ticker, period, interval)
    if not df.empty:
        return df

    # Fallback simulation
    idx = pd.date_range(end=datetime.now(), periods=int(252*3), freq="B")
    dt = 1/252; drift, vol = 0.08, 0.25
    z = np.random.standard_normal(len(idx))
    rets = (drift - 0.5*vol**2)*dt + vol*np.sqrt(dt)*z
    close = 100*np.exp(np.cumsum(rets))
    sim = pd.DataFrame(index=idx)
    sim["Close"] = close
    sim["Open"] = sim["Close"].shift(1).fillna(sim["Close"])
    sim["High"] = sim[["Open","Close"]].max(axis=1)*(1+np.random.rand(len(sim))*0.01)
    sim["Low"]  = sim[["Open","Close"]].min(axis=1)*(1-np.random.rand(len(sim))*0.01)
    sim["AdjClose"] = sim["Close"]
    sim["Volume"] = np.random.randint(1e5, 1e6, size=len(sim))
    return normalize_price_frame(sim)
