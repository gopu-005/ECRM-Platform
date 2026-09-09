"""
SQLAlchemy ORM Models for ECRM Platform
All models include organization_id for multi-tenant isolation
"""

from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime, ForeignKey,
    Enum as SAEnum, JSON, BigInteger, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from app.core.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    SALES_MANAGER = "sales_manager"
    SALES_REP = "sales_rep"
    VIEWER = "viewer"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    COLD_CALL = "cold_call"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    ADVERTISEMENT = "advertisement"
    TRADE_SHOW = "trade_show"
    OTHER = "other"


class DealStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ActivityType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    DEAL_STAGE_CHANGE = "deal_stage_change"
    LEAD_CONVERTED = "lead_converted"
    SYSTEM = "system"


class MeetingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ImportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─────────────────────────────────────────────────────────────────────────────
# Mixin
# ─────────────────────────────────────────────────────────────────────────────

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class SoftDeleteMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ─────────────────────────────────────────────────────────────────────────────
# Organization (Tenant Root)
# ─────────────────────────────────────────────────────────────────────────────

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "1-10", "11-50", etc.
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    subscription_plan: Mapped[str] = mapped_column(String(50), default="starter", nullable=False)
    max_users: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="organization", lazy="select")
    leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="organization", lazy="select")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="organization", lazy="select")
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="organization", lazy="select")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="organization", lazy="select")


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────

class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.SALES_REP, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    assigned_leads: Mapped[List["Lead"]] = relationship("Lead", back_populates="assigned_to", foreign_keys="Lead.assigned_to_id")
    assigned_deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="assigned_to", foreign_keys="Deal.assigned_to_id")
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="user", foreign_keys="Activity.user_id")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="assigned_to", foreign_keys="Task.assigned_to_id")

    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_user_org_email"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Account (Company)
# ─────────────────────────────────────────────────────────────────────────────

class Account(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="accounts")
    contacts: Mapped[List["Contact"]] = relationship("Contact", back_populates="account")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="account")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        Index("ix_accounts_org_name", "organization_id", "name"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Contact
# ─────────────────────────────────────────────────────────────────────────────

class Contact(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="contacts")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="contacts")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="contact")
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="contact")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Lead
# ─────────────────────────────────────────────────────────────────────────────

class Lead(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(SAEnum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True)
    source: Mapped[Optional[LeadSource]] = mapped_column(SAEnum(LeadSource), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annual_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    employee_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="leads")
    assigned_to: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to_id])
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="lead", uselist=False)
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="lead")

    __table_args__ = (
        Index("ix_leads_org_status", "organization_id", "status"),
        Index("ix_leads_org_score", "organization_id", "score"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Deal / Opportunity
# ─────────────────────────────────────────────────────────────────────────────

class Deal(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[DealStage] = mapped_column(SAEnum(DealStage), default=DealStage.PROSPECTING, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=10, nullable=False)  # 0-100
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    lost_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="deals")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="deals")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="deals")
    assigned_to: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_deals", foreign_keys=[assigned_to_id])
    activities: Mapped[List["Activity"]] = relationship("Activity", back_populates="deal")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="deal")

    __table_args__ = (
        Index("ix_deals_org_stage", "organization_id", "stage"),
        Index("ix_deals_org_value", "organization_id", "value"),
    )

    @property
    def weighted_value(self) -> float:
        return self.value * (self.probability / 100)


# ─────────────────────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────────────────────

class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True)
    priority: Mapped[TaskPriority] = mapped_column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    deal_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("deals.id"), nullable=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)

    # Relationships
    assigned_to: Mapped[Optional["User"]] = relationship("User", back_populates="tasks", foreign_keys=[assigned_to_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="tasks")


# ─────────────────────────────────────────────────────────────────────────────
# Meeting
# ─────────────────────────────────────────────────────────────────────────────

class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MeetingStatus] = mapped_column(SAEnum(MeetingStatus), default=MeetingStatus.SCHEDULED, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    organizer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    deal_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("deals.id"), nullable=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)
    attendees: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # list of user_ids
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organizer: Mapped["User"] = relationship("User", foreign_keys=[organizer_id])


# ─────────────────────────────────────────────────────────────────────────────
# Activity
# ─────────────────────────────────────────────────────────────────────────────

class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lead_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("leads.id"), nullable=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("contacts.id"), nullable=True)
    deal_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("deals.id"), nullable=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="activities", foreign_keys=[user_id])
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="activities")
    deal: Mapped[Optional["Deal"]] = relationship("Deal", back_populates="activities")

    __table_args__ = (
        Index("ix_activities_org_created", "organization_id", "created_at"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────────────────────────────────────

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


# ─────────────────────────────────────────────────────────────────────────────
# Audit Log
# ─────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_org_created", "organization_id", "created_at"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Import Job
# ─────────────────────────────────────────────────────────────────────────────

class ImportJob(Base, TimestampMixin):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(SAEnum(ImportStatus), default=ImportStatus.PENDING, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "lead", "contact", etc.
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
