"""
Tests for individual agents (no LLM calls — mocked).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.backend.agents.note_taking_agent import NoteTakingAgent
from src.backend.agents.task_agent import TaskAgent
from src.backend.agents.follow_up_agent import FollowUpAgent
from src.backend.agents.risk_alignment_agent import RiskAlignmentAgent
from src.backend.models.meeting import Meeting, Participant, MeetingNotes
from src.backend.models.task import ActionItem, RiskItem, TaskStatus, RiskSeverity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_action_item(**kwargs) -> ActionItem:
    defaults = dict(
        meeting_id="m1",
        title="Write unit tests",
        owner="Alice",
        status=TaskStatus.TODO,
    )
    defaults.update(kwargs)
    return ActionItem(**defaults)


# ---------------------------------------------------------------------------
# NoteTakingAgent
# ---------------------------------------------------------------------------


class TestNoteTakingAgent:
    def setup_method(self):
        with patch("src.backend.agents.base.ChatOpenAI"):
            self.agent = NoteTakingAgent()

    @pytest.mark.asyncio
    async def test_empty_transcript_returns_notes(self):
        notes = await self.agent.run(transcript="")
        assert notes.summary == "No transcript provided."

    @pytest.mark.asyncio
    async def test_parses_valid_llm_response(self):
        response = json.dumps(
            {
                "decisions": ["Use Python 3.11"],
                "action_items": [
                    {
                        "title": "Setup CI",
                        "owner": "Bob",
                        "due_date": "2024-06-01",
                        "acceptance_criteria": "All tests pass on PR",
                        "priority": "high",
                    }
                ],
                "risks": [{"title": "Vendor dependency", "severity": "medium", "category": "dependency"}],
                "discussion_points": ["Discussed tech stack"],
                "assumptions": ["Budget is approved"],
                "summary": "Team aligned on tech stack.",
            }
        )
        self.agent._call_llm = AsyncMock(return_value=response)
        notes = await self.agent.run(transcript="We decided to use Python 3.11.")
        assert "Use Python 3.11" in notes.decisions
        assert len(notes.action_items) == 1
        assert notes.action_items[0]["title"] == "Setup CI"
        assert len(notes.risks) == 1
        assert notes.summary == "Team aligned on tech stack."

    @pytest.mark.asyncio
    async def test_handles_malformed_llm_response(self):
        self.agent._call_llm = AsyncMock(return_value="not json at all")
        notes = await self.agent.run(transcript="Some meeting content")
        # Should not crash — returns empty notes
        assert isinstance(notes, MeetingNotes)


# ---------------------------------------------------------------------------
# TaskAgent
# ---------------------------------------------------------------------------


class TestTaskAgent:
    def setup_method(self):
        with patch("src.backend.agents.base.ChatOpenAI"):
            self.agent = TaskAgent()

    @pytest.mark.asyncio
    async def test_enriches_action_items(self):
        enriched_json = json.dumps(
            {
                "title": "Set up automated testing pipeline",
                "description": "Configure CI/CD with GitHub Actions",
                "owner": "Alice",
                "due_date": "2024-06-15",
                "acceptance_criteria": "All tests pass; coverage > 80%",
                "priority": "high",
            }
        )
        self.agent._call_llm = AsyncMock(return_value=enriched_json)

        raw_items = [{"title": "Setup CI", "owner": None}]
        items = await self.agent.run(
            meeting_id="m1",
            action_items=raw_items,
            meeting_title="Sprint Review",
        )
        assert len(items) == 1
        assert items[0].title == "Set up automated testing pipeline"
        assert items[0].owner == "Alice"
        assert items[0].priority == "high"

    @pytest.mark.asyncio
    async def test_sync_calls_connector(self):
        connector = AsyncMock()
        connector.name = "github"
        connector.create_task = AsyncMock(
            return_value={"id": "42", "url": "https://github.com/org/repo/issues/42"}
        )
        item = make_action_item()
        result = await self.agent.sync_confirmed([item], [connector])
        connector.create_task.assert_called_once()
        assert result[0].external_id == "42"
        assert "github.com" in result[0].external_url

    @pytest.mark.asyncio
    async def test_date_parsing(self):
        item = make_action_item()
        assert self.agent._parse_date("2024-06-15") is not None
        assert self.agent._parse_date("") is None
        assert self.agent._parse_date(None) is None

    @pytest.mark.asyncio
    async def test_generate_clarifications(self):
        self.agent._call_llm = AsyncMock(
            return_value='["Who is responsible?", "What is the deadline?"]'
        )
        questions = await self.agent.generate_clarifications(
            action_item={"title": "Unclear task"},
            missing_fields=["owner", "due_date"],
        )
        assert len(questions) == 2
        assert "Who is responsible?" in questions


# ---------------------------------------------------------------------------
# FollowUpAgent
# ---------------------------------------------------------------------------


class TestFollowUpAgent:
    def setup_method(self):
        with patch("src.backend.agents.base.ChatOpenAI"):
            self.agent = FollowUpAgent()

    @pytest.mark.asyncio
    async def test_run_with_no_items_returns_no_sent(self):
        result = await self.agent.run(action_items=[], meeting_title="Test")
        assert result["sent"] is False

    @pytest.mark.asyncio
    async def test_check_overdue_marks_items(self):
        past_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2)
        item = make_action_item(due_date=past_date, status=TaskStatus.TODO)
        overdue = await self.agent.check_overdue([item])
        assert len(overdue) == 1
        assert overdue[0].status == TaskStatus.OVERDUE

    @pytest.mark.asyncio
    async def test_check_overdue_ignores_done(self):
        past_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=2)
        item = make_action_item(due_date=past_date, status=TaskStatus.DONE)
        overdue = await self.agent.check_overdue([item])
        assert len(overdue) == 0

    @pytest.mark.asyncio
    async def test_send_followup_calls_connector(self):
        connector = AsyncMock()
        connector.send_message = AsyncMock(return_value=True)
        self.agent._call_llm = AsyncMock(return_value="Follow up on these tasks please.")

        item = make_action_item()
        result = await self.agent.run(
            action_items=[item],
            meeting_title="Sprint",
            messaging_connectors=[connector],
            channels=["#general"],
        )
        connector.send_message.assert_called_once()
        assert result["sent"] is True

    @pytest.mark.asyncio
    async def test_generate_weekly_report(self):
        self.agent._call_llm = AsyncMock(return_value="Good week overall with one blocker.")
        done_item = make_action_item(status=TaskStatus.DONE)
        todo_item = make_action_item(title="Pending task", status=TaskStatus.TODO)
        report = await self.agent.generate_weekly_report(
            action_items=[done_item, todo_item]
        )
        assert len(report.completed_tasks) == 1
        assert len(report.in_progress_tasks) == 1
        assert report.summary == "Good week overall with one blocker."


# ---------------------------------------------------------------------------
# RiskAlignmentAgent
# ---------------------------------------------------------------------------


class TestRiskAlignmentAgent:
    def setup_method(self):
        with patch("src.backend.agents.base.ChatOpenAI"):
            self.agent = RiskAlignmentAgent()

    @pytest.mark.asyncio
    async def test_detects_overdue_task(self):
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
        item = make_action_item(due_date=past, status=TaskStatus.TODO)
        risks = self.agent._detect_rule_based_risks([item], "m1")
        titles = [r.title for r in risks]
        assert any("Overdue" in t for t in titles)

    @pytest.mark.asyncio
    async def test_detects_no_owner(self):
        item = make_action_item(owner=None)
        risks = self.agent._detect_rule_based_risks([item], "m1")
        assert any(r.category == "resource" for r in risks)

    @pytest.mark.asyncio
    async def test_detects_blocked_task(self):
        item = make_action_item(status=TaskStatus.BLOCKED)
        risks = self.agent._detect_rule_based_risks([item], "m1")
        assert any(r.category == "dependency" for r in risks)

    @pytest.mark.asyncio
    async def test_health_score_full_completion(self):
        items = [make_action_item(status=TaskStatus.DONE) for _ in range(5)]
        score = self.agent._calculate_health_score(items, [])
        assert score == 100

    @pytest.mark.asyncio
    async def test_health_score_decreases_with_risks(self):
        items = [make_action_item(status=TaskStatus.DONE) for _ in range(5)]
        critical_risk = RiskItem(
            meeting_id="m1", title="Critical issue", severity=RiskSeverity.CRITICAL
        )
        score = self.agent._calculate_health_score(items, [critical_risk])
        assert score < 100

    @pytest.mark.asyncio
    async def test_run_returns_expected_keys(self):
        self.agent._call_llm = AsyncMock(return_value="[]")
        item = make_action_item(status=TaskStatus.DONE)
        result = await self.agent.run(action_items=[item], meeting_id="m1")
        assert "risks" in result
        assert "health_score" in result
        assert "health_summary" in result
        assert "completion_rate" in result
