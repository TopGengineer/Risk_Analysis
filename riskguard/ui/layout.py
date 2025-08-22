# riskguard/ui/layout.py
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from ..config import THEME, UPDATE_MS, DEFAULT_TICKERS

def build_layout():
    sidebar = dbc.Card(dbc.CardBody([
        html.H4("Control Panel"),
        html.Hr(),

        html.Div("Portfolio", className="text-muted small mb-1"),
        dcc.Dropdown(id="pos-ticker", placeholder="Search symbol…", searchable=True),
        dbc.Row([
            dbc.Col(dbc.Input(id="pos-qty",  type="number", placeholder="Qty"),  md=6),
            dbc.Col(dbc.Input(id="pos-cost", type="number", placeholder="Cost"), md=6),
        ], class_name="mt-2"),
        dbc.Row([
            dbc.Col(dbc.Button("Save/Update", id="pos-save", color="success", class_name="w-100"), md=6),
            dbc.Col(dbc.Button("Delete",      id="pos-del",  color="danger",  class_name="w-100"), md=6),
        ], class_name="mt-2"),
        html.Div(id="pos-msg", className="mt-2"),

        html.Hr(),

        html.Div("Forecast", className="text-muted small mb-1"),
        dcc.Dropdown(id="fc-ticker", placeholder="Search symbol…", searchable=True),
        dbc.Row([
            dbc.Col(dbc.Input(id="fc-horizon", type="number", value=30, min=5, max=252), md=8),
            dbc.Col(dbc.Button("Run Forecast", id="fc-run", color="primary", class_name="w-100"), md=4),
        ], class_name="mt-2"),

        html.Hr(),
        html.Div("Risk Settings", className="text-muted small mb-1"),
        dbc.Row([
            dbc.Col(dbc.Select(id="risk-alpha",
                options=[{"label":"90%","value":0.90},{"label":"95%","value":0.95},{"label":"99%","value":0.99}],
                value=0.95), md=6),
            dbc.Col(dbc.Select(id="risk-method",
                options=[{"label":"Parametric","value":"param"},{"label":"Historical","value":"hist"}],
                value="param"), md=6),
        ], class_name="mb-2"),

        html.Hr(),
        html.Small("Data source: yfinance (or simulation if offline)")
    ]), class_name="h-100")

    return dbc.Container([
        dcc.Interval(id="tick", interval=UPDATE_MS, n_intervals=0),
        dbc.Row([
            dbc.Col(sidebar, md=3),
            dbc.Col([
                html.H3("Portfolio Risk Dashboard"),
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        dash_table.DataTable(
                            id="positions-table",
                            page_size=10,
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            style_header={"fontWeight": "600"},
                            style_cell={"fontFamily": "monospace", "padding": "6px"},
                            style_cell_conditional=[
                                {"if": {"column_id": c}, "textAlign": "right"}
                                for c in ["Quantity","Cost Basis","Current Price","Market Value","P/L","P/L %"]
                            ],
                        )
                    ])), md=12),
                ], class_name="gy-3"),

                html.Hr(),
                html.H4("Charts"),
                dbc.Row([
                    dbc.Col(dbc.Select(id="chart-type",
                        options=[{"label":"Line","value":"line"},{"label":"Candlestick","value":"candle"}],
                        value="line"), md=2),
                    dbc.Col(dcc.Dropdown(id="chart-tickers", multi=True, searchable=True,
                        placeholder="Search symbols…", value=DEFAULT_TICKERS), md=7),
                    dbc.Col(dbc.Select(id="chart-lookback",
                        options=[{"label":x,"value":x} for x in ["3M","6M","1Y","3Y","MAX"]],
                        value="1Y"), md=3),
                ], className="g-2"),
                dbc.Card(dbc.CardBody([dcc.Graph(id="price-graph", style={"height":"520px"})])),

                html.Hr(),
                html.H4("Risk"),
                dbc.Row(id="risk-cards", className="gy-2"),
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="rolling-vol-graph", style={"height":"280px"})])), md=6),
                    dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="corr-heat", style={"height":"320px"})])), md=6),
                ], className="gy-3"),

                html.Hr(),
                html.H5("Stress Test"),
                dbc.Row([
                    dbc.Col(
                        dbc.ButtonGroup([
                            dbc.Button("Shock -5%",  id="stress-5",  color="warning", size="sm"),
                            dbc.Button("Shock -10%", id="stress-10", color="danger",  size="sm"),
                            dbc.Button("Shock -20%", id="stress-20", color="danger",  size="sm"),
                        ]),
                        md=6
                    ),
                    dbc.Col(html.Div(id="stress-out", className="small"), md=6, style={"alignSelf": "center"}),
                ], class_name="mb-2"),
                dbc.Row([dbc.Col(html.Div(id="worst-window-out", className="small text-muted"))]),

                html.Hr(),
                html.H4("Backtest (Buy & Hold)"),
                dbc.Row([
                    dbc.Col(dcc.DatePickerSingle(id="bt-start"), md=3),
                    dbc.Col(dbc.Button("Run Backtest", id="bt-run", color="primary"), md=2),
                    dbc.Col(html.Div("Uses your current portfolio positions & market-value weights.",
                                     className="text-muted small"), md=7),
                ], class_name="mb-2"),
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([dcc.Graph(id="bt-curve", style={"height":"320px"})])), md=8),
                    dbc.Col(dbc.Card(dbc.CardBody([html.Div(id="bt-metrics")])), md=4),
                ]),

                html.Hr(),
                html.H4("Forecast"),
                dbc.Card(dbc.CardBody([dcc.Graph(id="forecast-graph", style={"height":"420px"})])),
            ], md=9),
        ]),
    ], fluid=True)
