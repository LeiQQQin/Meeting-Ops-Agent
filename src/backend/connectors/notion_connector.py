"""
Notion connector — creates database entries and fetches pages as context.
Requires: NOTION_API_KEY, NOTION_DEFAULT_DATABASE_ID
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.connectors.base import BaseConnector
from src.backend.config import get_settings

logger = logging.getLogger(__name__)


class NotionConnector(BaseConnector):
    name = "notion"

    def __init__(self) -> None:
        self._client = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        settings = get_settings()
        try:
            from notion_client import AsyncClient  # type: ignore

            self._client = AsyncClient(auth=settings.notion_api_key)
            logger.info("Notion connector ready")
        except Exception as exc:
            logger.warning("Notion connector unavailable: %s", exc)

    # ------------------------------------------------------------------
    # Task management (Notion database rows)
    # ------------------------------------------------------------------

    async def create_task(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        due_date: Optional[str] = None,
        labels: Optional[list[str]] = None,
        database_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        if self._client is None:
            raise RuntimeError("Notion connector not connected")

        settings = get_settings()
        db_id = database_id or settings.notion_default_database_id

        properties: dict[str, Any] = {
            "Name": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": [{"text": {"content": description[:2000]}}]},
        }
        if owner:
            properties["Owner"] = {"rich_text": [{"text": {"content": owner}}]}
        if due_date:
            properties["Due Date"] = {"date": {"start": due_date}}
        if labels:
            properties["Tags"] = {"multi_select": [{"name": l} for l in labels]}

        page = await self._client.pages.create(
            parent={"database_id": db_id},
            properties=properties,
        )
        return {
            "id": page["id"],
            "url": page.get("url", ""),
            "title": title,
        }

    async def update_task(self, task_id: str, **kwargs: Any) -> dict:
        if self._client is None:
            raise RuntimeError("Notion connector not connected")
        await self._client.pages.update(page_id=task_id, properties=kwargs)
        return {"id": task_id}

    async def get_task(self, task_id: str) -> dict:
        if self._client is None:
            raise RuntimeError("Notion connector not connected")
        page = await self._client.pages.retrieve(page_id=task_id)
        props = page.get("properties", {})
        title = ""
        if "Name" in props:
            title_list = props["Name"].get("title", [])
            title = title_list[0]["text"]["content"] if title_list else ""
        return {"id": page["id"], "title": title, "url": page.get("url", "")}

    async def list_tasks(self, database_id: Optional[str] = None, **filters: Any) -> list[dict]:
        if self._client is None:
            return []
        settings = get_settings()
        db_id = database_id or settings.notion_default_database_id
        response = await self._client.databases.query(database_id=db_id)
        results = []
        for page in response.get("results", []):
            props = page.get("properties", {})
            title = ""
            if "Name" in props:
                title_list = props["Name"].get("title", [])
                title = title_list[0]["text"]["content"] if title_list else ""
            results.append({"id": page["id"], "title": title, "url": page.get("url", "")})
        return results

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    async def fetch_context(self, query: str, limit: int = 10) -> list[dict]:
        if self._client is None:
            return []
        try:
            results = await self._client.search(
                query=query,
                filter={"value": "page", "property": "object"},
                page_size=limit,
            )
            items = []
            for page in results.get("results", []):
                props = page.get("properties", {})
                title = page.get("url", "Untitled")
                if "title" in props:
                    tl = props["title"].get("title", [])
                    title = tl[0]["text"]["content"] if tl else title
                items.append(
                    {
                        "title": title,
                        "url": page.get("url", ""),
                        "body": "",
                        "updated_at": page.get("last_edited_time", ""),
                    }
                )
            return items
        except Exception as exc:
            logger.warning("Notion context fetch failed: %s", exc)
            return []
