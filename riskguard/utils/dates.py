# riskguard/utils/dates.py
import pandas as pd

def parse_lookback_df(lb: str, df):
    if df is None or df.empty:
        return df
    if lb == "MAX":
        return df
    end = df.index.max()
    if lb.endswith("M"):
        start = end - pd.DateOffset(months=int(lb[:-1]))
    elif lb.endswith("Y"):
        start = end - pd.DateOffset(years=int(lb[:-1]))
    else:
        start = end - pd.DateOffset(months=12)
    return df[df.index >= start]

def parse_lookback_series(lb: str, s):
    if s is None or s.empty:
        return s
    if lb == "MAX":
        return s
    end = s.index.max()
    if lb.endswith("M"):
        start = end - pd.DateOffset(months=int(lb[:-1]))
    elif lb.endswith("Y"):
        start = end - pd.DateOffset(years=int(lb[:-1]))
    else:
        start = end - pd.DateOffset(months=12)
    return s.loc[s.index >= start]
