"""
Context Agent — aggregates historical meeting notes and related project
context (GitHub Issues, Jira tickets, Notion pages) and produces a
concise pre-meeting brief with a suggested agenda.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.agents.base import BaseAgent
from src.backend.models.meeting import Meeting, PreMeetingBrief

logger = logging.getLogger(__name__)

CONTEXT_PROMPT = """\
You are the Context Agent for the Meeting Ops system.

Given the following information about an upcoming meeting:
- Title: {title}
- Description: {description}
- Participants: {participants}
- Project tags: {tags}

And these relevant items from connected systems:
{context_items}

And recent meeting notes from similar meetings:
{recent_notes}

Please produce a pre-meeting brief in the following JSON format:
{{
  "goals": ["goal 1", "goal 2"],
  "pending_items": ["pending item 1", "pending item 2"],
  "decision_questions": ["question 1", "question 2"],
  "suggested_agenda": [
    {{"topic": "Topic 1", "duration_minutes": 10, "owner": "Person"}},
    {{"topic": "Topic 2", "duration_minutes": 15, "owner": "Person"}}
  ],
  "context_summary": "A 2-3 sentence summary of the relevant context."
}}

Return ONLY the JSON, no markdown fences.
"""


class ContextAgent(BaseAgent):
    name = "context"
    description = (
        "Aggregates historical meeting notes and project context, "
        "then outputs a pre-meeting brief and suggested agenda."
    )

    async def run(
        self,
        meeting: Meeting,
        connectors: Optional[list] = None,
        recent_meetings: Optional[list[Meeting]] = None,
        **kwargs: Any,
    ) -> PreMeetingBrief:
        """
        Build a pre-meeting brief for the given meeting.

        Parameters
        ----------
        meeting:
            The upcoming meeting to prepare for.
        connectors:
            Instantiated and connected BaseConnector objects to query.
        recent_meetings:
            Up to the last N meetings with similar tags to use as history.
        """
        connectors = connectors or []
        recent_meetings = recent_meetings or []

        # 1. Gather context from connectors
        context_items = await self._gather_context(meeting, connectors)

        # 2. Summarise recent meeting notes
        recent_notes = self._format_recent_notes(recent_meetings)

        # 3. Build prompt and call LLM
        participants_str = ", ".join(
            p.name for p in meeting.participants
        ) or "Unknown"
        tags_str = ", ".join(meeting.project_tags) or "None"
        context_str = self._format_context_items(context_items)

        prompt = CONTEXT_PROMPT.format(
            title=meeting.title,
            description=meeting.description or "No description provided.",
            participants=participants_str,
            tags=tags_str,
            context_items=context_str or "No context items found.",
            recent_notes=recent_notes or "No recent meeting notes available.",
        )

        raw = await self._call_llm(prompt)

        # 4. Parse JSON output
        brief_data = self._parse_json(raw)

        return PreMeetingBrief(
            meeting_id=meeting.id,
            goals=brief_data.get("goals", []),
            pending_items=brief_data.get("pending_items", []),
            decision_questions=brief_data.get("decision_questions", []),
            suggested_agenda=brief_data.get("suggested_agenda", []),
            context_summary=brief_data.get("context_summary"),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _gather_context(self, meeting: Meeting, connectors: list) -> list[dict]:
        query = meeting.title
        if meeting.project_tags:
            query += " " + " ".join(meeting.project_tags)

        all_items: list[dict] = []
        for connector in connectors:
            try:
                items = await connector.fetch_context(query, limit=5)
                for item in items:
                    item["source"] = connector.name
                all_items.extend(items)
            except Exception as exc:
                logger.warning(
                    "Context fetch failed for connector %s: %s", connector.name, exc
                )
        return all_items

    def _format_context_items(self, items: list[dict]) -> str:
        if not items:
            return ""
        lines = []
        for item in items:
            source = item.get("source", "unknown")
            title = item.get("title", "Untitled")
            body = (item.get("body") or "")[:300]
            url = item.get("url", "")
            lines.append(f"[{source}] {title}\n  {body}\n  URL: {url}")
        return "\n\n".join(lines)

    def _format_recent_notes(self, meetings: list[Meeting]) -> str:
        if not meetings:
            return ""
        lines = []
        for m in meetings[-3:]:  # limit to 3 most recent
            if m.notes:
                decisions = "; ".join(m.notes.decisions[:3])
                actions = len(m.notes.action_items)
                lines.append(
                    f"[{m.title}] Decisions: {decisions or 'None'}. "
                    f"Action items: {actions}."
                )
        return "\n".join(lines)

    def _parse_json(self, raw: str) -> dict:
        import json
        import re

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        logger.warning("ContextAgent: could not parse LLM JSON output")
        return {}
