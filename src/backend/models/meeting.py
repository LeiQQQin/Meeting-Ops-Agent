"""
Meeting domain models.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"


class Participant(BaseModel):
    name: str
    email: Optional[str] = None
    role: Optional[str] = None


class MeetingCreateRequest(BaseModel):
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    participants: List[Participant] = Field(default_factory=list)
    project_tags: List[str] = Field(default_factory=list)
    connectors: List[str] = Field(
        default_factory=list,
        description="Enabled connectors e.g. ['github', 'jira', 'slack']",
    )


class MeetingNotes(BaseModel):
    decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    action_items: List[dict] = Field(
        default_factory=list,
        description="Action items with owner, due_date, acceptance_criteria",
    )
    risks: List[dict] = Field(
        default_factory=list,
        description="Identified risks and blockers",
    )
    discussion_points: List[str] = Field(
        default_factory=list, description="Key discussion points"
    )
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    summary: Optional[str] = None


class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: MeetingStatus = MeetingStatus.SCHEDULED
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    participants: List[Participant] = Field(default_factory=list)
    project_tags: List[str] = Field(default_factory=list)
    connectors: List[str] = Field(default_factory=list)
    transcript: Optional[str] = None
    notes: Optional[MeetingNotes] = None
    pre_meeting_brief: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class TranscriptUploadResponse(BaseModel):
    meeting_id: str
    message: str
    transcript_length: int


class PreMeetingBrief(BaseModel):
    meeting_id: str
    goals: List[str] = Field(default_factory=list)
    pending_items: List[str] = Field(default_factory=list)
    decision_questions: List[str] = Field(default_factory=list)
    suggested_agenda: List[dict] = Field(default_factory=list)
    context_summary: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
