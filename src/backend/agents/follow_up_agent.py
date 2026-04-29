"""
Follow-up Agent — monitors action item progress and sends periodic
reminders to responsible parties via configured messaging connectors
(Slack, email, etc.). Also generates weekly status reports.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.backend.agents.base import BaseAgent
from src.backend.models.task import ActionItem, TaskStatus, WeeklyReport

logger = logging.getLogger(__name__)

FOLLOWUP_MESSAGE_PROMPT = """\
You are the Follow-up Agent for the Meeting Ops system.
Write a brief, friendly follow-up message for the following action items.
Keep it under 200 words. Be specific about what's expected and when.

Meeting: {meeting_title}
Action items:
{items}

Write the message in a direct, professional tone. Include @mentions like
@owner_name where appropriate. Do not use markdown headers.
"""

WEEKLY_REPORT_PROMPT = """\
You are the Follow-up Agent. Generate a concise weekly status report.

Period: {period_start} to {period_end}
Completed tasks ({completed_count}): {completed_titles}
In-progress tasks ({in_progress_count}): {in_progress_titles}
Overdue tasks ({overdue_count}): {overdue_titles}
Active risks: {risks}

Write a 3-5 sentence executive summary for this week.
Highlight completed wins, blockers, and top priorities for next week.
"""


class FollowUpAgent(BaseAgent):
    name = "follow_up"
    description = (
        "Monitors action item status, sends reminders to responsible parties, "
        "and generates weekly status reports."
    )

    async def run(
        self,
        action_items: list[ActionItem],
        meeting_title: str = "",
        messaging_connectors: Optional[list] = None,
        channels: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict:
        """
        Send post-meeting follow-up messages for action items.

        Parameters
        ----------
        action_items:
            The action items to follow up on.
        meeting_title:
            Used in the follow-up message context.
        messaging_connectors:
            Connectors that support send_message (e.g. Slack).
        channels:
            Target channel(s) for the follow-up message.
        """
        messaging_connectors = messaging_connectors or []
        channels = channels or []

        if not action_items:
            return {"sent": False, "reason": "No action items to follow up on."}

        # Generate follow-up message
        message = await self._generate_followup_message(action_items, meeting_title)

        sent_count = 0
        for connector in messaging_connectors:
            for channel in channels:
                try:
                    success = await connector.send_message(channel, message)
                    if success:
                        sent_count += 1
                except Exception as exc:
                    logger.error(
                        "Follow-up send failed on %s/%s: %s",
                        connector.name,
                        channel,
                        exc,
                    )

        return {
            "sent": sent_count > 0,
            "message": message,
            "channels_notified": sent_count,
        }

    async def check_overdue(
        self,
        action_items: list[ActionItem],
        notify_connectors: Optional[list] = None,
        channels: Optional[list[str]] = None,
    ) -> list[ActionItem]:
        """
        Check for overdue tasks and send reminders if needed.
        Returns the list of overdue action items.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        overdue = [
            item
            for item in action_items
            if item.due_date
            and item.due_date < now
            and item.status not in (TaskStatus.DONE,)
        ]

        for item in overdue:
            item.status = TaskStatus.OVERDUE

        if overdue and notify_connectors and channels:
            await self._send_overdue_reminders(overdue, notify_connectors, channels)

        return overdue

    async def generate_weekly_report(
        self,
        action_items: list[ActionItem],
        risks: Optional[list] = None,
        period_days: int = 7,
    ) -> WeeklyReport:
        """
        Generate a weekly status report from action item states.
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        period_start = now - timedelta(days=period_days)

        completed = [i for i in action_items if i.status == TaskStatus.DONE]
        in_progress = [
            i
            for i in action_items
            if i.status in (TaskStatus.IN_PROGRESS, TaskStatus.TODO)
        ]
        overdue = [i for i in action_items if i.status == TaskStatus.OVERDUE]

        def _titles(items: list[ActionItem]) -> str:
            return ", ".join(i.title for i in items[:5]) or "None"

        prompt = WEEKLY_REPORT_PROMPT.format(
            period_start=period_start.strftime("%Y-%m-%d"),
            period_end=now.strftime("%Y-%m-%d"),
            completed_count=len(completed),
            completed_titles=_titles(completed),
            in_progress_count=len(in_progress),
            in_progress_titles=_titles(in_progress),
            overdue_count=len(overdue),
            overdue_titles=_titles(overdue),
            risks=", ".join(str(r) for r in (risks or [])) or "None",
        )

        summary = await self._call_llm(prompt)

        return WeeklyReport(
            period_start=period_start,
            period_end=now,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            overdue_tasks=overdue,
            active_risks=risks or [],
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _generate_followup_message(
        self, items: list[ActionItem], meeting_title: str
    ) -> str:
        items_text = "\n".join(
            f"- {i.title} | Owner: {i.owner or 'TBD'} | Due: {i.due_date or 'TBD'}"
            for i in items
        )
        prompt = FOLLOWUP_MESSAGE_PROMPT.format(
            meeting_title=meeting_title or "Meeting",
            items=items_text,
        )
        return await self._call_llm(prompt)

    async def _send_overdue_reminders(
        self,
        overdue_items: list[ActionItem],
        connectors: list,
        channels: list[str],
    ) -> None:
        lines = ["⚠️ *Overdue Action Items — Immediate Attention Required*"]
        for item in overdue_items:
            due_str = item.due_date.strftime("%Y-%m-%d") if item.due_date else "No date"
            lines.append(
                f"• *{item.title}* — Owner: {item.owner or 'TBD'} — Was due: {due_str}"
            )
        message = "\n".join(lines)

        for connector in connectors:
            for channel in channels:
                try:
                    await connector.send_message(channel, message)
                except Exception as exc:
                    logger.error(
                        "Overdue reminder failed on %s/%s: %s",
                        connector.name,
                        channel,
                        exc,
                    )
