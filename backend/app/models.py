from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_date: Mapped[datetime] = mapped_column(Date, index=True)
    merchant: Mapped[str] = mapped_column(String(255), index=True)
    normalized_merchant: Mapped[str] = mapped_column(String(255), index=True)
    amount: Mapped[float] = mapped_column(Float)
    source_file: Mapped[str] = mapped_column(String(255))


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant: Mapped[str] = mapped_column(String(255), unique=True)
    normalized_merchant: Mapped[str] = mapped_column(String(255), unique=True)
    average_amount: Mapped[float] = mapped_column(Float)
    cadence_days: Mapped[int] = mapped_column(Integer)
    transaction_count: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float)
    classification: Mapped[str] = mapped_column(String(30), default="likely_subscription")
    status: Mapped[str] = mapped_column(String(30), default="pending")
    value_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_score: Mapped[float] = mapped_column(Float, default=50)
    renewal_risk: Mapped[float] = mapped_column(Float, default=50)
    recommendation: Mapped[str] = mapped_column(String(500), default="Review this charge.")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
