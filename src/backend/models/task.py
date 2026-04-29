"""
Task and risk domain models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    OVERDUE = "overdue"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_id: str
    title: str
    description: Optional[str] = None
    owner: Optional[str] = None
    owner_email: Optional[str] = None
    due_date: Optional[datetime] = None
    acceptance_criteria: Optional[str] = None
    priority: str = "medium"
    status: TaskStatus = TaskStatus.TODO
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    connector: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class ActionItemUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    due_date: Optional[datetime] = None
    acceptance_criteria: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[str] = None


class RiskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_id: str
    title: str
    description: Optional[str] = None
    severity: RiskSeverity = RiskSeverity.MEDIUM
    category: str = "general"
    affected_tasks: list[str] = Field(default_factory=list)
    mitigation: Optional[str] = None
    owner: Optional[str] = None
    is_resolved: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class WeeklyReport(BaseModel):
    period_start: datetime
    period_end: datetime
    completed_tasks: list[ActionItem] = Field(default_factory=list)
    in_progress_tasks: list[ActionItem] = Field(default_factory=list)
    overdue_tasks: list[ActionItem] = Field(default_factory=list)
    active_risks: list[RiskItem] = Field(default_factory=list)
    summary: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
