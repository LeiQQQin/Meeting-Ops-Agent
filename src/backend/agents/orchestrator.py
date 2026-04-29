"""
Orchestrator — the central coordinator for the Meeting Ops system.
It manages the meeting lifecycle state machine and dispatches work to
the appropriate specialised agents.

Meeting lifecycle states:
  SCHEDULED → IN_PROGRESS → COMPLETED → FOLLOW_UP → CLOSED
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.agents.base import BaseAgent
from src.backend.agents.context_agent import ContextAgent
from src.backend.agents.follow_up_agent import FollowUpAgent
from src.backend.agents.note_taking_agent import NoteTakingAgent
from src.backend.agents.risk_alignment_agent import RiskAlignmentAgent
from src.backend.agents.task_agent import TaskAgent
from src.backend.connectors import CONNECTOR_REGISTRY, BaseConnector
from src.backend.models.meeting import Meeting, MeetingStatus, PreMeetingBrief
from src.backend.models.task import ActionItem, RiskItem

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Top-level coordinator that dispatches work to specialised agents
    and manages the meeting lifecycle.

    Usage
    -----
    orchestrator = Orchestrator()
    await orchestrator.setup(connector_names=["github", "slack"])
    brief = await orchestrator.prepare_meeting(meeting)
    notes = await orchestrator.process_transcript(meeting, transcript)
    """

    def __init__(self) -> None:
        self.context_agent = ContextAgent()
        self.note_taking_agent = NoteTakingAgent()
        self.task_agent = TaskAgent()
        self.follow_up_agent = FollowUpAgent()
        self.risk_agent = RiskAlignmentAgent()

        self._connectors: dict[str, BaseConnector] = {}

        # In-memory store (replace with DB in production)
        self._meetings: dict[str, Meeting] = {}
        self._action_items: dict[str, list[ActionItem]] = {}
        self._risks: dict[str, list[RiskItem]] = {}

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    async def setup(self, connector_names: Optional[list[str]] = None) -> None:
        """Initialise and connect the requested connectors."""
        for name in (connector_names or []):
            cls = CONNECTOR_REGISTRY.get(name)
            if cls is None:
                logger.warning("Unknown connector: %s", name)
                continue
            connector = cls()
            try:
                await connector.connect()
                self._connectors[name] = connector
                logger.info("Connector ready: %s", name)
            except Exception as exc:
                logger.error("Connector setup failed for %s: %s", name, exc)

    # ------------------------------------------------------------------
    # Meeting lifecycle events
    # ------------------------------------------------------------------

    async def on_meeting_created(self, meeting: Meeting) -> Meeting:
        """Register a new meeting."""
        self._meetings[meeting.id] = meeting
        logger.info("[Orchestrator] Meeting created: %s (%s)", meeting.title, meeting.id)
        return meeting

    async def prepare_meeting(self, meeting: Meeting) -> PreMeetingBrief:
        """
        EVENT: meeting_scheduled
        Trigger the Context Agent to build a pre-meeting brief.
        """
        meeting = self._get_or_register(meeting)
        connectors = list(self._connectors.values())
        recent = self._recent_meetings(meeting, limit=3)

        brief = await self.context_agent.run(
            meeting=meeting,
            connectors=connectors,
            recent_meetings=recent,
        )
        meeting.pre_meeting_brief = brief.model_dump()
        meeting.status = MeetingStatus.SCHEDULED
        self._meetings[meeting.id] = meeting

        logger.info("[Orchestrator] Pre-meeting brief ready for: %s", meeting.title)
        return brief

    async def process_transcript(
        self,
        meeting: Meeting,
        transcript: str,
        require_task_confirmation: bool = True,
    ) -> dict:
        """
        EVENT: transcript_ready
        Run the Note-taking Agent, then the Task Agent and Risk Agent.
        Returns a dict with notes, action_items, risks.
        """
        meeting = self._get_or_register(meeting)
        meeting.transcript = transcript
        meeting.status = MeetingStatus.COMPLETED

        # 1. Extract structured notes
        notes = await self.note_taking_agent.run(transcript=transcript)
        meeting.notes = notes

        # 2. Enrich action items
        connectors = list(self._connectors.values())
        action_items = await self.task_agent.run(
            meeting_id=meeting.id,
            action_items=notes.action_items,
            meeting_title=meeting.title,
            participants=meeting.participants,
            connectors=[] if require_task_confirmation else connectors,
            require_confirmation=require_task_confirmation,
        )
        self._action_items[meeting.id] = action_items

        # 3. Risk analysis
        result = await self.risk_agent.run(
            action_items=action_items,
            project_goals=meeting.pre_meeting_brief.get("goals", [])
            if meeting.pre_meeting_brief
            else [],
            meeting_id=meeting.id,
        )
        risks: list[RiskItem] = result["risks"]
        self._risks[meeting.id] = risks

        # 4. Transition state
        meeting.status = MeetingStatus.FOLLOW_UP
        self._meetings[meeting.id] = meeting

        logger.info(
            "[Orchestrator] Transcript processed for %s: %d action items, %d risks",
            meeting.title,
            len(action_items),
            len(risks),
        )

        return {
            "meeting": meeting,
            "notes": notes,
            "action_items": action_items,
            "risks": risks,
            "health_score": result["health_score"],
            "health_summary": result["health_summary"],
        }

    async def confirm_and_sync_tasks(self, meeting_id: str) -> list[ActionItem]:
        """
        EVENT: user_confirmed
        Push the action items to external connectors after user approval.
        """
        items = self._action_items.get(meeting_id, [])
        connectors = list(self._connectors.values())

        if not connectors:
            logger.info("[Orchestrator] No connectors configured; skipping sync.")
            return items

        synced = await self.task_agent.sync_confirmed(items, connectors)
        self._action_items[meeting_id] = synced

        logger.info(
            "[Orchestrator] Synced %d tasks for meeting %s", len(synced), meeting_id
        )
        return synced

    async def send_followup(
        self,
        meeting_id: str,
        channels: Optional[list[str]] = None,
        messaging_connector_name: str = "slack",
    ) -> dict:
        """
        EVENT: user_triggered or scheduled
        Send follow-up messages via the messaging connector.
        """
        meeting = self._meetings.get(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")

        items = self._action_items.get(meeting_id, [])
        connector = self._connectors.get(messaging_connector_name)
        messaging_connectors = [connector] if connector else []

        result = await self.follow_up_agent.run(
            action_items=items,
            meeting_title=meeting.title,
            messaging_connectors=messaging_connectors,
            channels=channels or [],
        )

        meeting.status = MeetingStatus.FOLLOW_UP
        self._meetings[meeting_id] = meeting

        return result

    async def run_periodic_check(
        self,
        meeting_id: str,
        channels: Optional[list[str]] = None,
        messaging_connector_name: str = "slack",
    ) -> dict:
        """
        Periodic task: check overdue items and send reminders.
        """
        items = self._action_items.get(meeting_id, [])
        connector = self._connectors.get(messaging_connector_name)
        messaging_connectors = [connector] if connector else []

        overdue = await self.follow_up_agent.check_overdue(
            action_items=items,
            notify_connectors=messaging_connectors,
            channels=channels or [],
        )

        # Re-analyse risks with updated statuses
        meeting = self._meetings.get(meeting_id)
        risk_result = await self.risk_agent.run(
            action_items=items,
            existing_risks=self._risks.get(meeting_id, []),
            meeting_id=meeting_id,
        )
        self._risks[meeting_id] = risk_result["risks"]

        return {
            "overdue_items": overdue,
            "risks": risk_result["risks"],
            "health_score": risk_result["health_score"],
        }

    async def get_weekly_report(self, meeting_ids: Optional[list[str]] = None) -> dict:
        """Generate a weekly report across one or many meetings."""
        all_items: list[ActionItem] = []
        all_risks: list[RiskItem] = []

        ids = meeting_ids or list(self._meetings.keys())
        for mid in ids:
            all_items.extend(self._action_items.get(mid, []))
            all_risks.extend(self._risks.get(mid, []))

        report = await self.follow_up_agent.generate_weekly_report(
            action_items=all_items, risks=all_risks
        )
        return report.model_dump()

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        return self._meetings.get(meeting_id)

    def get_action_items(self, meeting_id: str) -> list[ActionItem]:
        return self._action_items.get(meeting_id, [])

    def get_risks(self, meeting_id: str) -> list[RiskItem]:
        return self._risks.get(meeting_id, [])

    def list_meetings(self) -> list[Meeting]:
        return list(self._meetings.values())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_register(self, meeting: Meeting) -> Meeting:
        if meeting.id not in self._meetings:
            self._meetings[meeting.id] = meeting
        return self._meetings[meeting.id]

    def _recent_meetings(self, current: Meeting, limit: int = 3) -> list[Meeting]:
        """Return the most recent meetings sharing at least one project tag."""
        if not current.project_tags:
            return []
        related = [
            m
            for m in self._meetings.values()
            if m.id != current.id
            and m.notes is not None
            and any(t in current.project_tags for t in m.project_tags)
        ]
        related.sort(key=lambda m: m.created_at, reverse=True)
        return related[:limit]
