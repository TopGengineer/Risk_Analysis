# riskguard/db/base.py
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base
from ..config import DATABASE_URL

log = logging.getLogger("riskguard.db")

engine = create_engine(
    DATABASE_URL, echo=False, pool_pre_ping=True, future=True,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_prices_symbol_dt ON prices(symbol_id, dt)")

def ensure_schema() -> bool:
    """Ensure 'adj_close' column exists on prices."""
    with engine.connect() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(prices)").fetchall()]
        if "adj_close" not in cols:
            conn.exec_driver_sql("ALTER TABLE prices ADD COLUMN adj_close FLOAT")
            log.info("Added prices.adj_close column.")
    return True

def repair_adjclose_column():
    """Backfill adj_close with close where missing/zero."""
    with engine.begin() as conn:
        conn.exec_driver_sql("""
            UPDATE prices
            SET adj_close = close
            WHERE adj_close IS NULL OR adj_close = 0
        """)
