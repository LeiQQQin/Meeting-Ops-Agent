"""
Agent-status and agent-trigger API endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/agents", tags=["agents"])


def get_orchestrator():
    from src.backend.main import orchestrator
    return orchestrator


@router.get("")
async def list_agents(orch=Depends(get_orchestrator)):
    """Return metadata about all registered agents."""
    return [
        {
            "name": agent.name,
            "description": agent.description,
        }
        for agent in [
            orch.context_agent,
            orch.note_taking_agent,
            orch.task_agent,
            orch.follow_up_agent,
            orch.risk_agent,
        ]
    ]


@router.post("/{meeting_id}/run-risk-check")
async def run_risk_check(
    meeting_id: str,
    orch=Depends(get_orchestrator),
):
    """
    Manually trigger a risk & alignment check for a meeting.
    """
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = await orch.run_periodic_check(meeting_id=meeting_id)
    return {
        "overdue_count": len(result["overdue_items"]),
        "risk_count": len(result["risks"]),
        "health_score": result["health_score"],
        "risks": [r.model_dump() for r in result["risks"]],
    }


@router.post("/{meeting_id}/run-followup-check")
async def run_followup_check(
    meeting_id: str,
    channels: list[str] | None = None,
    connector: str = "slack",
    orch=Depends(get_orchestrator),
):
    """
    Manually trigger a follow-up check and send reminders for a meeting.
    """
    meeting = orch.get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = await orch.send_followup(
        meeting_id=meeting_id,
        channels=channels,
        messaging_connector_name=connector,
    )
    return result
