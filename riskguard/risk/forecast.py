# riskguard/risk/forecast.py
import numpy as np
import pandas as pd

try:
    from sklearn.ensemble import GradientBoostingRegressor
    HAVE_SKLEARN = True
except Exception:
    HAVE_SKLEARN = False

try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAVE_SM = True
except Exception:
    HAVE_SM = False

def _build_ts_features(series: pd.Series, max_lag=30):
    s = series.dropna().astype(float)
    df = pd.DataFrame({"y": s})
    for k in range(1, max_lag+1):
        df[f"lag_{k}"] = s.shift(k)
    for w in [5,10,20]:
        if len(df) > w + max_lag:
            df[f"roll_mean_{w}"] = s.rolling(w).mean()
            df[f"roll_std_{w}"]  = s.rolling(w).std()
    df["dow"] = s.index.dayofweek; df["dom"] = s.index.day; df["month"] = s.index.month
    df = df.dropna()
    return df.drop(columns=["y"]), df["y"]

def _next_feature_row(last_row: pd.Series, new_y: float, max_lag=30):
    r = last_row.copy()
    for k in range(max_lag, 1, -1):
        lk, lkm1 = f"lag_{k}", f"lag_{k-1}"
        if lk in r and lkm1 in r: r[lk] = r[lkm1]
    if "lag_1" in r: r["lag_1"] = new_y
    return r

def forecast_series(series: pd.Series, steps=30, alpha=0.95):
    s = series.dropna().astype(float)
    if not len(s): return pd.Series(dtype=float), None, None, "No data"
    freq = pd.infer_freq(s.index) or "B"
    future_index = pd.date_range(start=s.index[-1], periods=steps+1, freq=freq)[1:]
    if HAVE_SKLEARN:
        max_lag = min(30, max(5, len(s)//4))
        X, y = _build_ts_features(s, max_lag=max_lag)
        if not X.empty:
            gb_point = GradientBoostingRegressor(loss="squared_error", random_state=42)
            gb_point.fit(X, y)
            q_lo = (1 - alpha) / 2.0; q_hi = 1.0 - q_lo
            gb_lo = GradientBoostingRegressor(loss="quantile", alpha=q_lo, random_state=42)
            gb_hi = GradientBoostingRegressor(loss="quantile", alpha=q_hi, random_state=42)
            gb_lo.fit(X, y); gb_hi.fit(X, y)
            preds, lo, hi = [], [], []
            cur = X.iloc[-1].copy()
            for _ in range(steps):
                p  = float(gb_point.predict(cur.to_frame().T)[0])
                pl = float(gb_lo.predict(cur.to_frame().T)[0])
                ph = float(gb_hi.predict(cur.to_frame().T)[0])
                preds.append(p); lo.append(pl); hi.append(ph)
                cur = _next_feature_row(cur, p, max_lag=max_lag)
            fc = pd.Series(preds, index=future_index)
            return fc, pd.Series(lo, future_index), pd.Series(hi, future_index), f"GBM Quantile ({int(alpha*100)}%)"
    if HAVE_SM:
        try:
            m = SARIMAX(s, order=(1,1,1), enforce_stationarity=False, enforce_invertibility=False)
            res = m.fit(disp=False)
            pred = res.get_forecast(steps=steps)
            fc = pred.predicted_mean; fc.index = future_index
            ci = pred.conf_int(); ci.index = future_index
            return fc, ci.iloc[:,0], ci.iloc[:,1], "SARIMAX(1,1,1)"
        except Exception:
            pass
    if len(s) > 1:
        drift = (s.iloc[-1] - s.iloc[0]) / len(s)
        vals = [s.iloc[-1] + drift*i for i in range(1, steps+1)]
    else:
        vals = [s.iloc[-1]]*steps
    fc = pd.Series(vals, index=future_index)
    return fc, None, None, "Drift"
