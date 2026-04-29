"""
Meeting management API endpoints.
"""
from __future__ import annotations

import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src.backend.config import Settings, get_settings
from src.backend.models.meeting import (
    Meeting,
    MeetingCreateRequest,
    MeetingStatus,
    TranscriptUploadResponse,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])

# --------------------------------------------------------------------------
# Dependency: application-level Orchestrator singleton
# --------------------------------------------------------------------------


def get_orchestrator():
    from src.backend.main import orchestrator
    return orchestrator


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.post("", response_model=Meeting, status_code=201)
async def create_meeting(
    payload: MeetingCreateRequest,
    orch=Depends(get_orchestrator),
):
    """Create a new meeting and register it with the Orchestrator."""
    meeting = Meeting(
        title=payload.title,
        description=payload.description,
        scheduled_at=payload.scheduled_at,
        participants=payload.participants,
        project_tags=payload.project_tags,
        connectors=payload.connectors,
    )
    await orch.on_meeting_created(meeting)
    return meeting


@router.get("", response_model=list[Meeting])
async def list_meetings(orch=Depends(get_orchestrator)):
    """Return all registered meetings."""
    return orch.list_meetings()


@router.get("/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str, orch=Depends(get_orchestrator)):
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@router.post("/{meeting_id}/prepare")
async def prepare_meeting(meeting_id: str, orch=Depends(get_orchestrator)):
    """
    Trigger the Context Agent to build a pre-meeting brief.
    Returns the generated brief.
    """
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    brief = await orch.prepare_meeting(meeting)
    return brief.model_dump()


@router.post("/{meeting_id}/transcript", response_model=TranscriptUploadResponse)
async def upload_transcript(
    meeting_id: str,
    transcript_text: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    require_confirmation: bool = True,
    orch=Depends(get_orchestrator),
    settings: Settings = Depends(get_settings),
):
    """
    Upload a meeting transcript (text or audio file).
    - If `transcript_text` is provided, it is used directly.
    - If an audio file is uploaded, it is transcribed via Whisper.

    Set `require_confirmation=false` to auto-sync tasks without a human check.
    """
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    transcript = transcript_text or ""

    # Handle audio file upload
    if file and not transcript:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in {".mp3", ".mp4", ".wav", ".m4a", ".webm", ".ogg"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {ext}",
            )
        upload_path = os.path.join(settings.upload_dir, f"{uuid.uuid4()}{ext}")
        os.makedirs(settings.upload_dir, exist_ok=True)
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        try:
            transcript = await orch.note_taking_agent.transcribe_audio(upload_path)
        finally:
            os.remove(upload_path)

    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript or audio file provided")

    result = await orch.process_transcript(
        meeting=meeting,
        transcript=transcript,
        require_task_confirmation=require_confirmation,
    )

    return TranscriptUploadResponse(
        meeting_id=meeting_id,
        message="Transcript processed successfully",
        transcript_length=len(transcript),
    )


@router.post("/{meeting_id}/confirm-tasks")
async def confirm_tasks(meeting_id: str, orch=Depends(get_orchestrator)):
    """
    Confirm and sync the enriched action items to external connectors
    (called after the user reviews and approves the action items).
    """
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    synced = await orch.confirm_and_sync_tasks(meeting_id)
    return {"synced_count": len(synced), "tasks": [t.model_dump() for t in synced]}


@router.post("/{meeting_id}/followup")
async def send_followup(
    meeting_id: str,
    channels: Optional[list[str]] = None,
    connector: str = "slack",
    orch=Depends(get_orchestrator),
):
    """Send post-meeting follow-up messages via the configured connector."""
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = await orch.send_followup(
        meeting_id=meeting_id,
        channels=channels,
        messaging_connector_name=connector,
    )
    return result


@router.get("/{meeting_id}/notes")
async def get_notes(meeting_id: str, orch=Depends(get_orchestrator)):
    """Return the structured meeting notes."""
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not meeting.notes:
        raise HTTPException(status_code=404, detail="Notes not yet generated")
    return meeting.notes.model_dump()
