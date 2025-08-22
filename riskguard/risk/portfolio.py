# riskguard/risk/portfolio.py
import numpy as np
import pandas as pd

def portfolio_returns_dynamic(price_map, weights, min_coverage: float = 0.7) -> pd.Series:
    if not price_map:
        return pd.Series(dtype=float)
    rets = {t: s.sort_index().pct_change() for t, s in price_map.items() if s is not None and len(s)>1}
    if not rets:
        return pd.Series(dtype=float)
    R = pd.concat(rets, axis=1).sort_index()
    W = pd.Series(weights).reindex(R.columns).fillna(0.0)
    tot = float(W.sum()) if float(W.sum()) != 0.0 else np.nan
    weighted_sum = R.mul(W, axis=1).sum(axis=1, skipna=True)
    weight_in_play = R.notna().mul(W, axis=1).sum(axis=1)
    port_ret = weighted_sum / weight_in_play.replace(0, np.nan)
    if np.isfinite(tot) and tot>0:
        coverage = weight_in_play / tot
        port_ret = port_ret.where(coverage >= min_coverage)
    return port_ret.dropna().sort_index()

def worst_window_stats(port_ret: pd.Series, window: int = 20):
    if len(port_ret) < window + 1:
        return {}
    roll = (1 + port_ret).rolling(window).apply(lambda x: x.prod() - 1, raw=False)
    idx = roll.idxmin()
    return {"window_days": window,
            "start": (idx - pd.tseries.offsets.BDay(window-1)).date(),
            "end": idx.date(), "ret": float(roll.loc[idx])}
