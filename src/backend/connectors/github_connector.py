"""
GitHub connector — creates Issues, fetches PRs/Issues as context.
Requires: GITHUB_TOKEN, GITHUB_DEFAULT_REPO
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from src.backend.connectors.base import BaseConnector
from src.backend.config import get_settings

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    name = "github"

    def __init__(self) -> None:
        self._client = None
        self._repo = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        settings = get_settings()
        try:
            from github import Github  # type: ignore

            self._client = Github(settings.github_token)
            if settings.github_default_repo:
                self._repo = self._client.get_repo(settings.github_default_repo)
            logger.info("GitHub connector connected to %s", settings.github_default_repo)
        except Exception as exc:
            logger.warning("GitHub connector unavailable: %s", exc)

    # ------------------------------------------------------------------
    # Task management (Issues)
    # ------------------------------------------------------------------

    async def create_task(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        due_date: Optional[str] = None,
        labels: Optional[list[str]] = None,
        repo: Optional[str] = None,
        **kwargs: Any,
    ) -> dict:
        if self._client is None:
            raise RuntimeError("GitHub connector not connected")

        target_repo = self._repo
        if repo:
            target_repo = self._client.get_repo(repo)
        if target_repo is None:
            raise RuntimeError("No GitHub repo configured")

        body = description
        if owner:
            body += f"\n\n**Owner:** {owner}"
        if due_date:
            body += f"\n**Due date:** {due_date}"

        issue_labels = labels or []
        issue = target_repo.create_issue(
            title=title,
            body=body,
            labels=issue_labels,
            assignees=[owner] if owner else [],
        )

        return {"id": str(issue.number), "url": issue.html_url, "title": issue.title}

    async def update_task(self, task_id: str, **kwargs: Any) -> dict:
        if self._repo is None:
            raise RuntimeError("GitHub connector not connected")
        issue = self._repo.get_issue(int(task_id))
        issue.edit(**kwargs)
        return {"id": task_id, "url": issue.html_url, "state": issue.state}

    async def get_task(self, task_id: str) -> dict:
        if self._repo is None:
            raise RuntimeError("GitHub connector not connected")
        issue = self._repo.get_issue(int(task_id))
        return {
            "id": str(issue.number),
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "url": issue.html_url,
            "assignees": [a.login for a in issue.assignees],
        }

    async def list_tasks(self, state: str = "open", **filters: Any) -> list[dict]:
        if self._repo is None:
            return []
        issues = self._repo.get_issues(state=state)
        return [
            {
                "id": str(i.number),
                "title": i.title,
                "state": i.state,
                "url": i.html_url,
                "assignees": [a.login for a in i.assignees],
                "updated_at": i.updated_at.isoformat() if i.updated_at else None,
            }
            for i in issues
        ]

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    async def fetch_context(self, query: str, limit: int = 10) -> list[dict]:
        if self._repo is None:
            return []
        try:
            issues = self._repo.get_issues(state="all")
            results = []
            query_lower = query.lower()
            for issue in issues:
                if query_lower in (issue.title or "").lower() or query_lower in (
                    issue.body or ""
                ).lower():
                    results.append(
                        {
                            "title": issue.title,
                            "url": issue.html_url,
                            "body": (issue.body or "")[:500],
                            "updated_at": (
                                issue.updated_at.isoformat() if issue.updated_at else None
                            ),
                        }
                    )
                    if len(results) >= limit:
                        break
            return results
        except Exception as exc:
            logger.warning("GitHub context fetch failed: %s", exc)
            return []
