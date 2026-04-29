"""Connector package — pluggable integrations with third-party tools."""
from src.backend.connectors.base import BaseConnector
from src.backend.connectors.github_connector import GitHubConnector
from src.backend.connectors.jira_connector import JiraConnector
from src.backend.connectors.slack_connector import SlackConnector
from src.backend.connectors.notion_connector import NotionConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "github": GitHubConnector,
    "jira": JiraConnector,
    "slack": SlackConnector,
    "notion": NotionConnector,
}

__all__ = [
    "BaseConnector",
    "GitHubConnector",
    "JiraConnector",
    "SlackConnector",
    "NotionConnector",
    "CONNECTOR_REGISTRY",
]
