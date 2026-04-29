"""
Jira connector — creates Jira issues, fetches issues as context.
Requires: JIRA_SERVER_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.connectors.base import BaseConnector
from src.backend.config import get_settings

logger = logging.getLogger(__name__)


class JiraConnector(BaseConnector):
    name = "jira"

    def __init__(self) -> None:
        self._client = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        settings = get_settings()
        try:
            from jira import JIRA  # type: ignore

            self._client = JIRA(
                server=settings.jira_server_url,
                basic_auth=(settings.jira_user_email, settings.jira_api_token),
            )
            logger.info("Jira connector connected to %s", settings.jira_server_url)
        except Exception as exc:
            logger.warning("Jira connector unavailable: %s", exc)

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    async def create_task(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        due_date: Optional[str] = None,
        labels: Optional[list[str]] = None,
        project_key: Optional[str] = None,
        issue_type: str = "Task",
        **kwargs: Any,
    ) -> dict:
        if self._client is None:
            raise RuntimeError("Jira connector not connected")

        settings = get_settings()
        fields: dict[str, Any] = {
            "project": {"key": project_key or settings.jira_default_project_key},
            "summary": title,
            "description": description,
            "issuetype": {"name": issue_type},
        }
        if labels:
            fields["labels"] = labels
        if due_date:
            fields["duedate"] = due_date
        if owner:
            fields["assignee"] = {"name": owner}

        issue = self._client.create_issue(fields=fields)
        return {
            "id": issue.key,
            "url": f"{get_settings().jira_server_url}/browse/{issue.key}",
            "title": title,
        }

    async def update_task(self, task_id: str, **kwargs: Any) -> dict:
        if self._client is None:
            raise RuntimeError("Jira connector not connected")
        issue = self._client.issue(task_id)
        issue.update(fields=kwargs)
        return {"id": task_id, "url": f"{get_settings().jira_server_url}/browse/{task_id}"}

    async def get_task(self, task_id: str) -> dict:
        if self._client is None:
            raise RuntimeError("Jira connector not connected")
        issue = self._client.issue(task_id)
        return {
            "id": issue.key,
            "title": issue.fields.summary,
            "description": issue.fields.description,
            "status": issue.fields.status.name,
            "assignee": getattr(issue.fields.assignee, "displayName", None),
            "url": f"{get_settings().jira_server_url}/browse/{issue.key}",
        }

    async def list_tasks(self, project_key: Optional[str] = None, **filters: Any) -> list[dict]:
        if self._client is None:
            return []
        settings = get_settings()
        pk = project_key or settings.jira_default_project_key
        jql = f"project = {pk} ORDER BY updated DESC"
        issues = self._client.search_issues(jql, maxResults=50)
        return [
            {
                "id": i.key,
                "title": i.fields.summary,
                "status": i.fields.status.name,
                "assignee": getattr(i.fields.assignee, "displayName", None),
                "url": f"{settings.jira_server_url}/browse/{i.key}",
            }
            for i in issues
        ]

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    async def fetch_context(self, query: str, limit: int = 10) -> list[dict]:
        if self._client is None:
            return []
        try:
            jql = f'text ~ "{query}" ORDER BY updated DESC'
            issues = self._client.search_issues(jql, maxResults=limit)
            settings = get_settings()
            return [
                {
                    "title": i.fields.summary,
                    "url": f"{settings.jira_server_url}/browse/{i.key}",
                    "body": (i.fields.description or "")[:500],
                    "updated_at": str(i.fields.updated),
                }
                for i in issues
            ]
        except Exception as exc:
            logger.warning("Jira context fetch failed: %s", exc)
            return []
