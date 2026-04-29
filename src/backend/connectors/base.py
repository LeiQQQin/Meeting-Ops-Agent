"""
Abstract base class for all connectors.
Each connector wraps a third-party system (GitHub, Jira, Slack, Notion …).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseConnector(ABC):
    """
    All connectors must implement this interface so the agent layer can
    interact with them in a uniform way.
    """

    name: str = "base"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def connect(self) -> None:
        """Initialise the underlying SDK client / verify credentials."""

    async def disconnect(self) -> None:
        """Optional teardown hook."""

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    @abstractmethod
    async def create_task(
        self,
        title: str,
        description: str,
        owner: Optional[str] = None,
        due_date: Optional[str] = None,
        labels: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> dict:
        """Create a task/issue and return a dict with at least {id, url}."""

    @abstractmethod
    async def update_task(self, task_id: str, **kwargs: Any) -> dict:
        """Update an existing task. Returns updated task data."""

    @abstractmethod
    async def get_task(self, task_id: str) -> dict:
        """Fetch task details by ID."""

    @abstractmethod
    async def list_tasks(self, **filters: Any) -> list[dict]:
        """List tasks matching optional filters."""

    # ------------------------------------------------------------------
    # Context retrieval (for Context Agent)
    # ------------------------------------------------------------------

    async def fetch_context(self, query: str, limit: int = 10) -> list[dict]:
        """
        Retrieve relevant context items from this system.
        Override in connectors that support search (Notion, Jira, GitHub).
        Returns a list of dicts: [{title, url, body, updated_at}, …]
        """
        return []

    # ------------------------------------------------------------------
    # Messaging (for Follow-up Agent)
    # ------------------------------------------------------------------

    async def send_message(
        self, channel: str, message: str, **kwargs: Any
    ) -> bool:
        """Send a message to a channel/user. Returns True on success."""
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
