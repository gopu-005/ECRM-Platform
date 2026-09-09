"""
Pydantic schemas for request/response validation
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.models.models import (
    UserRole, LeadStatus, LeadSource, DealStage,
    TaskStatus, TaskPriority, ActivityType, MeetingStatus,
)

T = TypeVar("T")


# ─────────────────────────────────────────────────────────────────────────────
# Base / Pagination
# ─────────────────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Organization Schemas
# ─────────────────────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    domain: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    logo_url: Optional[str]
    is_active: bool
    subscription_plan: str
    max_users: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Auth Schemas
# ─────────────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    # Organization
    org_name: str
    org_slug: str
    # User
    email: EmailStr
    password: str
    first_name: str
    last_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ─────────────────────────────────────────────────────────────────────────────
# User Schemas
# ─────────────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.SALES_REP
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    phone: Optional[str]
    timezone: str
    last_login_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Lead Schemas
# ─────────────────────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW
    source: Optional[LeadSource] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to_id: Optional[str] = None


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None
    score: Optional[int] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to_id: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    organization_id: str
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    title: Optional[str]
    status: LeadStatus
    source: Optional[LeadSource]
    score: int
    annual_revenue: Optional[float]
    employee_count: Optional[int]
    industry: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    assigned_to_id: Optional[str]
    assigned_to: Optional[UserResponse]
    converted_at: Optional[datetime]
    last_contacted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Contact Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    account_id: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None
    linkedin_url: Optional[str] = None


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    account_id: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None


class ContactResponse(BaseModel):
    id: str
    organization_id: str
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    title: Optional[str]
    department: Optional[str]
    account_id: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    owner_id: Optional[str]
    lead_id: Optional[str]
    linkedin_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Account Schemas
# ─────────────────────────────────────────────────────────────────────────────

class AccountCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    domain: Optional[str]
    industry: Optional[str]
    size: Optional[str]
    annual_revenue: Optional[float]
    employee_count: Optional[int]
    phone: Optional[str]
    website: Optional[str]
    city: Optional[str]
    country: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    owner_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Deal Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DealCreate(BaseModel):
    name: str
    stage: DealStage = DealStage.PROSPECTING
    value: float = 0.0
    currency: str = "USD"
    probability: int = 10
    expected_close_date: Optional[datetime] = None
    contact_id: Optional[str] = None
    account_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class DealUpdate(BaseModel):
    name: Optional[str] = None
    stage: Optional[DealStage] = None
    value: Optional[float] = None
    probability: Optional[int] = None
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    contact_id: Optional[str] = None
    account_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    lost_reason: Optional[str] = None


class DealStageUpdate(BaseModel):
    stage: DealStage
    lost_reason: Optional[str] = None


class DealResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    stage: DealStage
    value: float
    currency: str
    probability: int
    weighted_value: float
    expected_close_date: Optional[datetime]
    actual_close_date: Optional[datetime]
    contact_id: Optional[str]
    account_id: Optional[str]
    assigned_to_id: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    lost_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Task Schemas
# ─────────────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[str] = None
    deal_id: Optional[str] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    assigned_to_id: Optional[str]
    created_by_id: str
    deal_id: Optional[str]
    contact_id: Optional[str]
    lead_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Meeting Schemas
# ─────────────────────────────────────────────────────────────────────────────

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    deal_id: Optional[str] = None
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    attendees: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_times(self) -> "MeetingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    meeting_url: Optional[str] = None
    status: Optional[MeetingStatus] = None
    notes: Optional[str] = None


class MeetingResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    description: Optional[str]
    status: MeetingStatus
    start_time: datetime
    end_time: datetime
    location: Optional[str]
    meeting_url: Optional[str]
    organizer_id: str
    deal_id: Optional[str]
    contact_id: Optional[str]
    lead_id: Optional[str]
    attendees: Optional[List[str]]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Activity / Notification Schemas
# ─────────────────────────────────────────────────────────────────────────────

class ActivityResponse(BaseModel):
    id: str
    organization_id: str
    user_id: Optional[str]
    type: ActivityType
    title: str
    description: Optional[str]
    lead_id: Optional[str]
    contact_id: Optional[str]
    deal_id: Optional[str]
    account_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    read_at: Optional[datetime]
    link: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Analytics Schemas
# ─────────────────────────────────────────────────────────────────────────────

class KPICard(BaseModel):
    label: str
    value: Any
    change_percent: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "flat"
    unit: Optional[str] = None


class DashboardAnalytics(BaseModel):
    total_leads: KPICard
    lead_conversion_rate: KPICard
    total_contacts: KPICard
    total_accounts: KPICard
    total_deals: KPICard
    pipeline_value: KPICard
    weighted_pipeline: KPICard
    win_rate: KPICard
    avg_deal_size: KPICard
    open_tasks: KPICard
    upcoming_meetings: KPICard
    activities_this_week: KPICard
    recent_activities: List[ActivityResponse]
    top_deals: List[DealResponse]
    lead_by_status: List[dict]
    deal_by_stage: List[dict]
    revenue_trend: List[dict]
