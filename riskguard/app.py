# riskguard/app.py
import logging, threading, webbrowser, os
from dash import Dash
from .config import APP_VERSION, THEME
from .bootstrap import bootstrap
from .ui.layout import build_layout
from .ui.callbacks.positions import register_positions_callbacks
from .ui.callbacks.charts import register_charts_callbacks
from .ui.callbacks.risk import register_risk_callbacks
from .ui.callbacks.stress import register_stress_callbacks
from .ui.callbacks.backtest import register_backtest_callbacks
from .ui.callbacks.forecast import register_forecast_callbacks

logging.basicConfig(level=logging.INFO)

def create_app():
    app = Dash(__name__, external_stylesheets=[THEME], suppress_callback_exceptions=True)
    app.title = f"RiskGuard Core v{APP_VERSION}"
    app.layout = build_layout()
    # Register callbacks
    register_positions_callbacks(app)
    register_charts_callbacks(app)
    register_risk_callbacks(app)
    register_stress_callbacks(app)
    register_backtest_callbacks(app)
    register_forecast_callbacks(app)
    return app

def main():
    bootstrap()
    app = create_app()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8050")).start()
    app.run(host="127.0.0.1", port=int(os.getenv("PORT","8050")), debug=True, use_reloader=False)

if __name__ == "__main__":
    main()
