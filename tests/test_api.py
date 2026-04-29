"""
Tests for the FastAPI REST API layer.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.backend.models.meeting import Meeting, MeetingNotes, MeetingStatus
from src.backend.models.task import ActionItem, RiskItem, TaskStatus


@pytest.fixture
def client():
    """Create a test client with a mocked Orchestrator."""
    with patch("src.backend.agents.base.ChatOpenAI"), \
         patch("src.backend.main.orchestrator") as mock_orch:

        from src.backend.main import app

        mock_orch.list_meetings.return_value = []
        mock_orch.get_meeting.return_value = None
        mock_orch._connectors = {}
        mock_orch._meetings = {}

        yield TestClient(app), mock_orch


# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------


class TestSystemEndpoints:
    def test_health(self, client):
        tc, mock_orch = client
        mock_orch._connectors = {}
        mock_orch._meetings = {}
        response = tc.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root(self, client):
        tc, _ = client
        response = tc.get("/")
        assert response.status_code == 200
        assert response.json()["service"] == "Meeting-Ops-Agent"


# ---------------------------------------------------------------------------
# Meeting endpoints
# ---------------------------------------------------------------------------


class TestMeetingEndpoints:
    def test_list_meetings_empty(self, client):
        tc, mock_orch = client
        mock_orch.list_meetings.return_value = []
        response = tc.get("/meetings")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_meeting(self, client):
        tc, mock_orch = client
        meeting = Meeting(title="Sprint Review", project_tags=["sprint"])
        mock_orch.on_meeting_created = AsyncMock(return_value=meeting)

        response = tc.post(
            "/meetings",
            json={"title": "Sprint Review", "project_tags": ["sprint"]},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Sprint Review"

    def test_get_meeting_not_found(self, client):
        tc, mock_orch = client
        mock_orch.get_meeting.return_value = None
        response = tc.get("/meetings/nonexistent-id")
        assert response.status_code == 404

    def test_get_meeting_found(self, client):
        tc, mock_orch = client
        meeting = Meeting(id="abc", title="Test Meeting")
        mock_orch.get_meeting.return_value = meeting
        response = tc.get("/meetings/abc")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Meeting"

    def test_prepare_meeting(self, client):
        tc, mock_orch = client
        from src.backend.models.meeting import PreMeetingBrief
        meeting = Meeting(id="abc", title="Test Meeting")
        mock_orch.get_meeting.return_value = meeting
        brief = PreMeetingBrief(
            meeting_id="abc",
            goals=["Align on Q3 goals"],
            context_summary="Previous meeting discussed timeline.",
        )
        mock_orch.prepare_meeting = AsyncMock(return_value=brief)
        response = tc.post("/meetings/abc/prepare")
        assert response.status_code == 200
        data = response.json()
        assert data["goals"] == ["Align on Q3 goals"]

    def test_upload_transcript(self, client):
        tc, mock_orch = client
        meeting = Meeting(id="abc", title="Test")
        mock_orch.get_meeting.return_value = meeting
        mock_orch.process_transcript = AsyncMock(
            return_value={
                "meeting": meeting,
                "notes": MeetingNotes(summary="Short summary"),
                "action_items": [],
                "risks": [],
                "health_score": 100,
                "health_summary": "All good",
            }
        )
        response = tc.post(
            "/meetings/abc/transcript",
            params={"transcript_text": "We decided to ship next week."},
        )
        assert response.status_code == 200
        assert response.json()["meeting_id"] == "abc"

    def test_upload_transcript_missing_content(self, client):
        tc, mock_orch = client
        meeting = Meeting(id="abc", title="Test")
        mock_orch.get_meeting.return_value = meeting
        response = tc.post("/meetings/abc/transcript")
        assert response.status_code == 400

    def test_get_notes_no_notes(self, client):
        tc, mock_orch = client
        meeting = Meeting(id="abc", title="Test", notes=None)
        mock_orch.get_meeting.return_value = meeting
        response = tc.get("/meetings/abc/notes")
        assert response.status_code == 404

    def test_get_notes_with_notes(self, client):
        tc, mock_orch = client
        meeting = Meeting(
            id="abc",
            title="Test",
            notes=MeetingNotes(decisions=["Ship it"], summary="Good meeting"),
        )
        mock_orch.get_meeting.return_value = meeting
        response = tc.get("/meetings/abc/notes")
        assert response.status_code == 200
        assert "Ship it" in response.json()["decisions"]


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------


class TestTaskEndpoints:
    def test_list_tasks(self, client):
        tc, mock_orch = client
        meeting = Meeting(id="abc", title="Test")
        mock_orch.get_meeting.return_value = meeting
        item = ActionItem(meeting_id="abc", title="Write docs")
        mock_orch.get_action_items.return_value = [item]
        response = tc.get("/tasks/abc")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_tasks_meeting_not_found(self, client):
        tc, mock_orch = client
        mock_orch.get_meeting.return_value = None
        response = tc.get("/tasks/nonexistent")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


class TestAgentEndpoints:
    def test_list_agents(self, client):
        tc, mock_orch = client
        from src.backend.agents.note_taking_agent import NoteTakingAgent
        from src.backend.agents.context_agent import ContextAgent

        with patch("src.backend.agents.base.ChatOpenAI"):
            mock_orch.context_agent = ContextAgent()
            mock_orch.note_taking_agent = NoteTakingAgent()
            mock_orch.task_agent = MagicMock(name="task", description="Task agent")
            mock_orch.follow_up_agent = MagicMock(name="follow_up", description="Follow-up")
            mock_orch.risk_agent = MagicMock(name="risk_alignment", description="Risk")

        response = tc.get("/agents")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
