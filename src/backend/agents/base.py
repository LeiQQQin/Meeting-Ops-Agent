"""
Abstract base class for all Meeting-Ops-Agent agents.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import ChatOpenAI

from src.backend.config import get_settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Every specialised agent inherits from this class.
    It provides a shared LLM client and a common ``run`` interface.
    """

    name: str = "base"
    description: str = ""

    def __init__(self) -> None:
        settings = get_settings()
        self._llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Execute the agent's primary task and return a result."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _call_llm(self, prompt: str) -> str:
        """
        Send a single user prompt to the LLM and return the text response.
        Wraps errors so callers get a graceful message instead of a crash.
        """
        try:
            from langchain_core.messages import HumanMessage

            response = await self._llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", self.name, exc)
            return f"[LLM error: {exc}]"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
