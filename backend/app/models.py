from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from .database import Base

# Single-user for now; every table carries user_id so that adding
# real multi-user support later is just wiring up auth, not a
# schema rewrite.
DEFAULT_USER_ID = 1


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, default=DEFAULT_USER_ID)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'numeric' | 'boolean' | 'duration'
    unit = Column(String(20))
    group_name = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "type IN ('numeric','boolean','duration')", name="valid_metric_type"
        ),
    )


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, default=DEFAULT_USER_ID)
    metric_id = Column(
        Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False
    )
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    active_duration_seconds = Column(Integer)
    status = Column(String(20), nullable=False, default="running")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, default=DEFAULT_USER_ID)
    metric_id = Column(
        Integer, ForeignKey("metrics.id", ondelete="CASCADE"), nullable=False
    )
    value = Column(Numeric)
    duration_seconds = Column(Integer)
    logged_at = Column(DateTime(timezone=True), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, default=DEFAULT_USER_ID)
    title = Column(String(200), nullable=False)
    points = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pending")  # pending|done|late
    due_date = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())