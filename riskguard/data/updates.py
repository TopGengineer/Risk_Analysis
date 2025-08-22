# riskguard/data/updates.py
import logging
import numpy as np
import pandas as pd

try:
    import yfinance as yf
    HAVE_YF = True
except Exception:
    HAVE_YF = False

from ..config import UPDATE_SKIP_JUMP
from .normalize import normalize_price_frame
from ..db.repo import get_price_df, bulk_upsert_prices

log = logging.getLogger("riskguard.data.updates")

def update_latest_prices(session, tickers):
    """Daily-only; upsert last day; skip suspicious jumps."""
    if not HAVE_YF:
        return
    for t in tickers:
        try:
            df = yf.download(t, period="12d", interval="1d",
                             auto_adjust=False, progress=False, threads=False)
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            df = normalize_price_frame(df).tail(1)
            hist = get_price_df(session, t)
            if not hist.empty:
                last_close = float(hist["Close"].iloc[-1])
                new_close  = float(df["Close"].iloc[-1])
                if np.isfinite(last_close) and last_close > 0:
                    jump = abs(new_close / last_close - 1.0)
                    if jump > UPDATE_SKIP_JUMP:
                        log.warning("Skipping suspicious bar %s: %.4f -> %.4f (%.1f%%)",
                                    t, last_close, new_close, 100*jump)
                        continue
            bulk_upsert_prices(session, t, df, adj_col_exists=True)
        except Exception as e:
            log.info("update_latest_prices failed %s: %s", t, e)
