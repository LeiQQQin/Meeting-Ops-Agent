"""
Tests for connector stubs (no real API calls).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.backend.connectors.base import BaseConnector
from src.backend.connectors.github_connector import GitHubConnector
from src.backend.connectors.jira_connector import JiraConnector
from src.backend.connectors.slack_connector import SlackConnector
from src.backend.connectors.notion_connector import NotionConnector
from src.backend.connectors import CONNECTOR_REGISTRY


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestConnectorRegistry:
    def test_all_connectors_registered(self):
        assert "github" in CONNECTOR_REGISTRY
        assert "jira" in CONNECTOR_REGISTRY
        assert "slack" in CONNECTOR_REGISTRY
        assert "notion" in CONNECTOR_REGISTRY

    def test_registry_returns_correct_types(self):
        assert CONNECTOR_REGISTRY["github"] is GitHubConnector
        assert CONNECTOR_REGISTRY["slack"] is SlackConnector


# ---------------------------------------------------------------------------
# GitHub connector
# ---------------------------------------------------------------------------


class TestGitHubConnector:
    def _make_connector(self):
        connector = GitHubConnector()
        # Mock the GitHub client
        mock_repo = MagicMock()
        connector._client = MagicMock()
        connector._repo = mock_repo
        return connector, mock_repo

    @pytest.mark.asyncio
    async def test_create_task_calls_create_issue(self):
        connector, mock_repo = self._make_connector()
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_issue.html_url = "https://github.com/org/repo/issues/42"
        mock_issue.title = "Test task"
        mock_repo.create_issue.return_value = mock_issue

        result = await connector.create_task(
            title="Test task",
            description="Do the thing",
            owner="alice",
            labels=["bug"],
        )
        mock_repo.create_issue.assert_called_once()
        assert result["id"] == "42"
        assert "github.com" in result["url"]

    @pytest.mark.asyncio
    async def test_create_task_raises_when_no_client(self):
        connector = GitHubConnector()
        with pytest.raises(RuntimeError, match="not connected"):
            await connector.create_task("title", "desc")

    @pytest.mark.asyncio
    async def test_list_tasks_returns_empty_without_repo(self):
        connector = GitHubConnector()
        result = await connector.list_tasks()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_context_returns_empty_without_repo(self):
        connector = GitHubConnector()
        result = await connector.fetch_context("test query")
        assert result == []


# ---------------------------------------------------------------------------
# Slack connector
# ---------------------------------------------------------------------------


class TestSlackConnector:
    def _make_connected(self):
        connector = SlackConnector()
        mock_client = AsyncMock()
        connector._client = mock_client
        return connector, mock_client

    @pytest.mark.asyncio
    async def test_send_message_calls_chat_post(self):
        connector, mock_client = self._make_connected()
        mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
        result = await connector.send_message("#general", "Hello team!")
        mock_client.chat_postMessage.assert_called_once()
        assert result is True

    @pytest.mark.asyncio
    async def test_send_message_returns_false_without_client(self):
        connector = SlackConnector()
        result = await connector.send_message("#general", "Hello")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_followup_formats_items(self):
        connector, mock_client = self._make_connected()
        mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
        items = [
            {"title": "Write tests", "owner": "Alice", "due_date": "2024-06-01"},
            {"title": "Deploy", "owner": "Bob", "due_date": "2024-06-05"},
        ]
        result = await connector.send_followup("#general", items)
        assert result is True
        called_text = mock_client.chat_postMessage.call_args.kwargs.get("text", "")
        assert "Write tests" in called_text

    @pytest.mark.asyncio
    async def test_create_task_sends_message(self):
        connector, mock_client = self._make_connected()
        mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
        result = await connector.create_task(
            title="Setup pipeline",
            description="Configure CI",
            owner="Charlie",
        )
        assert result["title"] == "Setup pipeline"
        mock_client.chat_postMessage.assert_called_once()


# ---------------------------------------------------------------------------
# Base connector
# ---------------------------------------------------------------------------


class TestBaseConnector:
    def test_base_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            BaseConnector()

    def test_repr(self):
        c = SlackConnector()
        assert "SlackConnector" in repr(c)
        assert "slack" in repr(c)
