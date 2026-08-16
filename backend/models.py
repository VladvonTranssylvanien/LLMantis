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
    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")


class Target(Base):
    """A chatbot to be tested."""
    __tablename__ = "targets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=False)
    canary = Column(String(255), nullable=True)
    # PLAYBOOK decision #5: customer prompts are trade secrets.
    # "delete_after_scan" is the safe default — must be an explicit
    # opt-in to keep a target's prompt around longer than that.
    retention = Column(String(50), nullable=False, default="delete_after_scan")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="targets")
    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan")


class Membership(Base):
    """
    Links a user to an organization with a role.

    No separate `users` table yet — user_id is a bare UUID until real
    authentication exists. This table is the schema groundwork the
    implementation plan calls for on day one, so the agency/multi-user
    tier is a new row later, not a backend rewrite.
    """
    __tablename__ = "memberships"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), primary_key=True)
    role = Column(String(50), nullable=False)  # "owner" | "admin" | "member"
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="memberships")


class OwnershipVerification(Base):
    """Proof that organization owns a domain."""
    __tablename__ = "ownership_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    domain = Column(String(255), nullable=False)
    method = Column(String(50), nullable=False)
    token = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="ownership_verifications")


class Scan(Base):
    """A penetration test scan."""
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    target_id = Column(UUID(as_uuid=True), ForeignKey("targets.id"), nullable=False)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    library_version = Column(String(50), nullable=False, default="1.0")
    duration_s = Column(Float, nullable=False)
    # 'done' | 'incomplete' — PLAYBOOK §9: >10% errored attacks means no
    # grade at all. This must survive the trip to the database, not just
    # exist in the streamed response, or a later reader of this row has
    # no way to know the grade was deliberately withheld.
    status = Column(String(50), nullable=False, default="done")
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
    judge_reason = Column(Text, nullable=True)
    method = Column(String(50), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    scan = relationship("Scan", back_populates="results")


class ApiKey(Base):
    """
    A credential that lets an organization call the API programmatically
    (CI/CD pipelines, integrations) instead of through the browser.

    Only the SHA-256 hash is stored — the plaintext key is shown to the
    caller exactly once, at creation, and never again.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)
    key_prefix = Column(String(16), nullable=False)  # shown in listings to tell keys apart
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="api_keys")
