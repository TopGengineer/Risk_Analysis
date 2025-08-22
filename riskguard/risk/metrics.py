# riskguard/risk/metrics.py
import numpy as np
import pandas as pd

try:
    from scipy.stats import norm
    HAVE_SCIPY = True
except Exception:
    HAVE_SCIPY = False

def parametric_var_es(ret: pd.Series, alpha: float = 0.95):
    if ret is None or ret.empty: return float("nan"), float("nan")
    mu = float(ret.mean()); sd = float(ret.std(ddof=1))
    if not np.isfinite(sd) or sd == 0.0: return float("nan"), float("nan")
    q = 1.0 - alpha
    if HAVE_SCIPY:
        z = norm.ppf(q)
        var = -(mu + sd * z)
        es  = -(mu - sd * norm.pdf(z) / q)
    else:
        z_map = {0.90:-1.2816, 0.95:-1.6449, 0.99:-2.3263}
        z = z_map.get(round(alpha,2), -1.6449)
        var = -(mu + sd*z); es = 1.25*var
    return float(max(var,0.0)), float(max(es,0.0))

def historical_var_es(ret: pd.Series, alpha: float = 0.95):
    if ret is None or ret.empty: return float("nan"), float("nan")
    q = ret.quantile(1.0 - alpha)
    tail = ret[ret <= q]
    es = tail.mean() if not tail.empty else float("nan")
    return float(abs(q)), float(abs(es))

def buy_hold_metrics(port_ret: pd.Series):
    if port_ret.empty: return {}
    equity = (1 + port_ret).cumprod()
    cagr = equity.iloc[-1] ** (252/len(port_ret)) - 1
    vol  = port_ret.std(ddof=1) * np.sqrt(252)
    sharpe = (port_ret.mean() / port_ret.std(ddof=1)) * np.sqrt(252) if port_ret.std(ddof=1) else np.nan
    mdd = float((equity / equity.cummax() - 1).min())
    return {"CAGR": float(cagr), "AnnVol": float(vol), "Sharpe": float(sharpe), "MaxDD": mdd}
