"""
SQLAlchemy ORM models for LLMantis database.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Float, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Organization(Base):
    """A customer organization."""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    targets = relationship("Target", back_populates="organization", cascade="all, delete-orphan")
    ownership_verifications = relationship("OwnershipVerification", back_populates="organization", cascade="all, delete-orphan")
    scans = relationship("Scan", back_populates="organization", cascade="all, delete-orphan")


class Target(Base):
    """A chatbot to be tested."""
    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=False)
    canary = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="targets")
    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan")


class OwnershipVerification(Base):
    """Proof that organization owns a domain."""
    __tablename__ = "ownership_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="ownership_verifications")


class Scan(Base):
    """A penetration test scan."""
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    duration_s = Column(Float, nullable=False)
    grade = Column(String(1), nullable=True)
    score = Column(Integer, nullable=True)
    error_rate = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    target = relationship("Target", back_populates="scans")
    organization = relationship("Organization", back_populates="scans")
    results = relationship("Result", back_populates="scan", cascade="all, delete-orphan")


class Result(Base):
    """One attack result from a scan."""
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    attack_id = Column(String(255), nullable=False)
    verdict = Column(String(50), nullable=False)
    confidence = Column(String(50), nullable=False, default="likely")
    evidence = Column(Text, nullable=True)
    method = Column(String(50), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="results")
