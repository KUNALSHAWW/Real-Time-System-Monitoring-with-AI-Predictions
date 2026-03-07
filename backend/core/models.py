"""
SQLAlchemy ORM models for the multi-tenant SaaS monitoring platform.

Tables:
  - users          : registered platform users
  - agents         : machines (sensors) registered by each user
  - metric_records : time-series metric rows sent by agents
  - anomaly_events : anomaly / alert records tied to specific agents
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    BigInteger,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(256), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True,
                     default=lambda: f"smk_{uuid.uuid4().hex}")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agents = relationship("Agent", back_populates="owner", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Agents (machines / sensors)
# ---------------------------------------------------------------------------

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(128), nullable=False, index=True)  # human-friendly name
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_agents_user_agent", "user_id", "agent_id", unique=True),
    )

    # Relationships
    owner = relationship("User", back_populates="agents")
    metrics = relationship("MetricRecord", back_populates="agent", cascade="all, delete-orphan")
    anomaly_events = relationship("AnomalyEvent", back_populates="agent", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Metric Records (time-series)
# ---------------------------------------------------------------------------

class MetricRecord(Base):
    __tablename__ = "metric_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_pk = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(128), nullable=False, index=True)  # denormalised for fast queries
    timestamp = Column(DateTime, nullable=False, index=True)

    # CPU
    cpu_percent = Column(Float, nullable=False)
    cpu_freq_mhz = Column(Float, nullable=True)

    # Memory
    memory_percent = Column(Float, nullable=False)
    memory_used_bytes = Column(BigInteger, nullable=True)
    memory_total_bytes = Column(BigInteger, nullable=True)

    # Disk
    disk_percent = Column(Float, nullable=False)
    disk_used_bytes = Column(BigInteger, nullable=True)
    disk_total_bytes = Column(BigInteger, nullable=True)

    # Disk I/O deltas (ransomware detection preparation)
    disk_read_bytes_delta = Column(BigInteger, default=0)
    disk_write_bytes_delta = Column(BigInteger, default=0)
    disk_read_count_delta = Column(Integer, default=0)
    disk_write_count_delta = Column(Integer, default=0)

    # Network deltas
    network_sent_bytes_delta = Column(BigInteger, default=0)
    network_recv_bytes_delta = Column(BigInteger, default=0)
    network_sent_bytes_total = Column(BigInteger, default=0)
    network_recv_bytes_total = Column(BigInteger, default=0)

    __table_args__ = (
        Index("ix_metrics_agent_ts", "agent_id", "timestamp"),
        Index("ix_metrics_user_ts", "user_id", "timestamp"),
    )

    # Relationships
    agent = relationship("Agent", back_populates="metrics")


# ---------------------------------------------------------------------------
# Anomaly / Alert Events
# ---------------------------------------------------------------------------

class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_pk = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(128), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    metric_name = Column(String(64), nullable=False)        # e.g. "cpu_percent"
    value = Column(Float, nullable=False)
    z_score = Column(Float, nullable=True)
    severity = Column(String(16), nullable=False)            # low / medium / high / critical
    message = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_anomaly_agent_ts", "agent_id", "timestamp"),
    )

    # Relationships
    agent = relationship("Agent", back_populates="anomaly_events")


# ---------------------------------------------------------------------------
# Remediation Events (self-healing audit trail)
# ---------------------------------------------------------------------------

class RemediationEvent(Base):
    __tablename__ = "remediation_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_pk = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String(128), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    event_type = Column(String(64), nullable=False)          # e.g. "process_kill", "container_restart"
    target_name = Column(String(256), nullable=False)
    target_pid = Column(Integer, nullable=True)
    reason = Column(Text, nullable=False)
    dry_run = Column(Boolean, nullable=False, default=True)
    success = Column(Boolean, nullable=False, default=False)
    rollback_available = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)              # JSON blob for extra context

    __table_args__ = (
        Index("ix_remediation_agent_ts", "agent_id", "timestamp"),
    )

    # Relationships
    agent = relationship("Agent")
