"""
Task Agent — enriches action items extracted from meeting notes and
synchronises them to configured third-party task systems (GitHub, Jira,
Notion, …).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from src.backend.agents.base import BaseAgent
from src.backend.models.task import ActionItem, TaskStatus

logger = logging.getLogger(__name__)

ENRICH_PROMPT = """\
You are the Task Agent for the Meeting Ops system.

Below is a raw action item extracted from a meeting. Enrich it by:
1. Writing a clear, one-sentence title (if the existing one is vague).
2. Filling in a missing owner based on context clues (or leave null).
3. Suggesting a due date if the meeting mentioned a timeline (YYYY-MM-DD or null).
4. Writing specific, measurable acceptance criteria (1-3 bullet points).
5. Assigning a priority: "high", "medium", or "low".

Meeting title: {meeting_title}
Participants: {participants}

Raw action item:
{action_item}

Return ONLY JSON with these fields:
{{
  "title": "...",
  "description": "...",
  "owner": "... or null",
  "due_date": "YYYY-MM-DD or null",
  "acceptance_criteria": "...",
  "priority": "high|medium|low"
}}
"""

CLARIFICATION_PROMPT = """\
You are the Task Agent. An action item is missing critical information.
Generate 1-3 concise clarification questions to send to the meeting host.

Action item: {action_item}
Missing fields: {missing_fields}

Return a JSON array of question strings:
["Question 1?", "Question 2?"]
"""


class TaskAgent(BaseAgent):
    name = "task"
    description = (
        "Enriches raw action items (owner, due date, acceptance criteria) "
        "and syncs them to configured task systems."
    )

    async def run(
        self,
        meeting_id: str,
        action_items: list[dict],
        meeting_title: str = "",
        participants: Optional[list] = None,
        connectors: Optional[list] = None,
        require_confirmation: bool = True,
        **kwargs: Any,
    ) -> list[ActionItem]:
        """
        Enrich and optionally sync action items.

        Parameters
        ----------
        meeting_id:
            ID of the source meeting.
        action_items:
            Raw action item dicts from NoteTakingAgent.
        meeting_title:
            Used as LLM context for enrichment.
        participants:
            Meeting participants for owner inference.
        connectors:
            Connected task-system connectors to push tasks into.
        require_confirmation:
            If True, tasks are enriched but NOT synced to external systems
            until confirmed by the user. Set False for automatic sync.
        """
        participants = participants or []
        connectors = connectors or []
        participants_str = ", ".join(
            getattr(p, "name", str(p)) for p in participants
        )

        enriched: list[ActionItem] = []
        for raw_item in action_items:
            item = await self._enrich_item(raw_item, meeting_title, participants_str)
            item.meeting_id = meeting_id
            enriched.append(item)

        if not require_confirmation and connectors:
            enriched = await self._sync_to_connectors(enriched, connectors)

        return enriched

    async def sync_confirmed(
        self, action_items: list[ActionItem], connectors: list
    ) -> list[ActionItem]:
        """
        Called after user confirms. Pushes action items to external systems.
        """
        return await self._sync_to_connectors(action_items, connectors)

    async def generate_clarifications(
        self, action_item: dict, missing_fields: list[str]
    ) -> list[str]:
        """Generate clarification questions for incomplete action items."""
        prompt = CLARIFICATION_PROMPT.format(
            action_item=json.dumps(action_item),
            missing_fields=", ".join(missing_fields),
        )
        raw = await self._call_llm(prompt)
        try:
            questions = json.loads(raw)
            if isinstance(questions, list):
                return [str(q) for q in questions]
        except json.JSONDecodeError:
            pass
        return [raw]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _enrich_item(
        self, raw: dict, meeting_title: str, participants_str: str
    ) -> ActionItem:
        prompt = ENRICH_PROMPT.format(
            meeting_title=meeting_title or "Unknown meeting",
            participants=participants_str or "Unknown",
            action_item=json.dumps(raw, ensure_ascii=False),
        )
        response = await self._call_llm(prompt)
        enriched_data = self._parse_json(response)

        return ActionItem(
            meeting_id="",  # set by caller
            title=enriched_data.get("title") or raw.get("title", "Untitled action"),
            description=enriched_data.get("description") or raw.get("description", ""),
            owner=enriched_data.get("owner") or raw.get("owner"),
            due_date=self._parse_date(
                enriched_data.get("due_date") or raw.get("due_date")
            ),
            acceptance_criteria=enriched_data.get("acceptance_criteria")
            or raw.get("acceptance_criteria"),
            priority=enriched_data.get("priority") or raw.get("priority", "medium"),
            status=TaskStatus.TODO,
        )

    async def _sync_to_connectors(
        self, items: list[ActionItem], connectors: list
    ) -> list[ActionItem]:
        for connector in connectors:
            for item in items:
                try:
                    result = await connector.create_task(
                        title=item.title,
                        description=item.description or "",
                        owner=item.owner,
                        due_date=(
                            item.due_date.strftime("%Y-%m-%d") if item.due_date else None
                        ),
                        labels=["meeting-action-item"],
                    )
                    item.external_id = result.get("id")
                    item.external_url = result.get("url")
                    item.connector = connector.name
                    logger.info(
                        "Task synced to %s: %s → %s",
                        connector.name,
                        item.title,
                        result.get("url"),
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to sync task to %s: %s", connector.name, exc
                    )
        return items

    def _parse_json(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return {}

    def _parse_date(self, value: Any):
        if not value:
            return None
        if isinstance(value, str):
            from datetime import datetime

            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None
