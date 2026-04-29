"""
Task and risk management API endpoints.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.backend.models.task import ActionItem, ActionItemUpdateRequest, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_orchestrator():
    from src.backend.main import orchestrator
    return orchestrator


# --------------------------------------------------------------------------
# Action items
# --------------------------------------------------------------------------


@router.get("/{meeting_id}", response_model=list[ActionItem])
async def list_tasks(meeting_id: str, orch=Depends(get_orchestrator)):
    """Return all action items for a meeting."""
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return orch.get_action_items(meeting_id)


@router.patch("/{meeting_id}/{task_id}", response_model=ActionItem)
async def update_task(
    meeting_id: str,
    task_id: str,
    payload: ActionItemUpdateRequest,
    orch=Depends(get_orchestrator),
):
    """Update a specific action item (local + optional external sync)."""
    items = orch.get_action_items(meeting_id)
    task = next((t for t in items if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Action item not found")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.owner is not None:
        task.owner = payload.owner
    if payload.due_date is not None:
        task.due_date = payload.due_date
    if payload.acceptance_criteria is not None:
        task.acceptance_criteria = payload.acceptance_criteria
    if payload.status is not None:
        task.status = payload.status
    if payload.priority is not None:
        task.priority = payload.priority

    return task


# --------------------------------------------------------------------------
# Risks
# --------------------------------------------------------------------------


@router.get("/{meeting_id}/risks", response_model=list[dict])
async def list_risks(meeting_id: str, orch=Depends(get_orchestrator)):
    """Return all identified risks for a meeting."""
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return [r.model_dump() for r in orch.get_risks(meeting_id)]


# --------------------------------------------------------------------------
# Weekly report
# --------------------------------------------------------------------------


@router.get("/weekly-report", response_model=dict)
async def weekly_report(
    meeting_ids: Optional[str] = None,
    orch=Depends(get_orchestrator),
):
    """
    Generate a weekly report.
    `meeting_ids` is an optional comma-separated list of meeting IDs.
    If omitted, all meetings are included.
    """
    ids = [m.strip() for m in meeting_ids.split(",")] if meeting_ids else None
    return await orch.get_weekly_report(meeting_ids=ids)
