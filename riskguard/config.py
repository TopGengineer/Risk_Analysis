# riskguard/config.py
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

APP_VERSION = "5.2"
DATABASE_URL = "sqlite:///riskguard_core.db"
THEME = dbc.themes.FLATLY
UPDATE_MS = 15_000

DEFAULT_TICKERS = ["AAPL", "MSFT", "SPY"]
BENCHMARK = "SPY"
DEFAULT_BT_START = (datetime.today() - timedelta(days=365)).date()

FALLBACK_SYMBOLS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA",
    "SPY","QQQ","DIA","IWM","VTI","GLD","TLT",
    "BTC-USD","ETH-USD","EURUSD=X","USDJPY=X","^GSPC","^IXIC","^DJI","^VIX"
]

# Outlier filter (daily close) & update guard
OUTLIER_JUMP_DAILY = 0.18   # used for line series patching
UPDATE_SKIP_JUMP   = 0.15   # skip if |new/old - 1| > 15%
