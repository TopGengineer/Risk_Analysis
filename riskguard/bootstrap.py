# riskguard/bootstrap.py
import logging
from .db.base import init_db, ensure_schema, repair_adjclose_column, SessionLocal
from .db.repo import ensure_history, upsert_symbol
from .db.models import Position
from .config import DEFAULT_TICKERS, BENCHMARK

log = logging.getLogger("riskguard.bootstrap")

def bootstrap():
    init_db()
    ensure_schema()
    repair_adjclose_column()
    with SessionLocal() as s:
        ensure_history(s, DEFAULT_TICKERS + [BENCHMARK])
        if s.query(Position).count() == 0:
            # Seed a simple portfolio
            for t, q, c in [("AAPL",10,150.0), ("MSFT",8,300.0), ("SPY",5,430.0)]:
                sym = upsert_symbol(s, t)
                s.add(Position(symbol_id=sym.id, quantity=q, cost_basis=c))
            s.commit()
