# riskguard/db/models.py
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint

Base = declarative_base()

class Symbol(Base):
    __tablename__ = "symbols"
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String, default="")
    prices = relationship("Price", back_populates="symbol", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="symbol", cascade="all, delete-orphan")

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    dt = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    # adj_close is added via ensure_schema() if missing
    symbol = relationship("Symbol", back_populates="prices")
    __table_args__ = (UniqueConstraint("symbol_id", "dt", name="_symbol_dt_uc"),)

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    cost_basis = Column(Float, nullable=False)
    symbol = relationship("Symbol", back_populates="positions")
