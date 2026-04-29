"""
Slack connector — sends messages and DMs for follow-up and notifications.
Requires: SLACK_BOT_TOKEN
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.connectors.base import BaseConnector
from src.backend.config import get_settings

logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector):
    name = "slack"

    def __init__(self) -> None:
        self._client = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        settings = get_settings()
        try:
            from slack_sdk.web.async_client import AsyncWebClient  # type: ignore

            self._client = AsyncWebClient(token=settings.slack_bot_token)
            logger.info("Slack connector ready")
        except Exception as exc:
            logger.warning("Slack connector unavailable: %s", exc)

    # ------------------------------------------------------------------
    # Task management (Slack doesn't have native tasks — no-ops)
    # ------------------------------------------------------------------

    async def create_task(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        due_date: Optional[str] = None,
        labels: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict:
        # Slack doesn't manage tasks; just post a reminder message
        channel = kwargs.get("channel", get_settings().slack_default_channel)
        msg = f"*New action item:* {title}\n{description}"
        if owner:
            msg += f"\n*Owner:* {owner}"
        if due_date:
            msg += f"\n*Due:* {due_date}"
        await self.send_message(channel, msg)
        return {"id": "slack-message", "url": "", "title": title}

    async def update_task(self, task_id: str, **kwargs: Any) -> dict:
        return {"id": task_id}

    async def get_task(self, task_id: str) -> dict:
        return {"id": task_id}

    async def list_tasks(self, **filters: Any) -> list[dict]:
        return []

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def send_message(
        self, channel: str, message: str, **kwargs: Any
    ) -> bool:
        if self._client is None:
            logger.warning("Slack client not initialised")
            return False
        try:
            await self._client.chat_postMessage(channel=channel, text=message, **kwargs)
            return True
        except Exception as exc:
            logger.error("Slack send_message failed: %s", exc)
            return False

    async def send_followup(
        self,
        channel: str,
        action_items: list[dict],
        mention_users: Optional[list[str]] = None,
    ) -> bool:
        lines = ["*📋 Meeting Follow-up — Action Items*"]
        for item in action_items:
            owner = item.get("owner", "TBD")
            due = item.get("due_date", "TBD")
            lines.append(f"• *{item['title']}*  |  Owner: {owner}  |  Due: {due}")
        if mention_users:
            lines.append(" ".join(f"<@{u}>" for u in mention_users))
        return await self.send_message(channel, "\n".join(lines))
