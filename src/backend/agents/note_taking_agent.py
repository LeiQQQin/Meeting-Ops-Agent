"""
Note-taking Agent — receives meeting transcript text and extracts
structured meeting notes: decisions, action items, risks, discussion
points, and assumptions.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from src.backend.agents.base import BaseAgent
from src.backend.models.meeting import MeetingNotes

logger = logging.getLogger(__name__)

NOTE_TAKING_PROMPT = """\
You are the Note-taking Agent for the Meeting Ops system.

Analyse the following meeting transcript and extract structured notes.
Return a JSON object with EXACTLY the following keys:

{{
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {{
      "title": "Short action title",
      "description": "Detailed description of what needs to be done",
      "owner": "Person's name or null if unclear",
      "due_date": "YYYY-MM-DD or null if not mentioned",
      "acceptance_criteria": "How to verify completion, or null if not mentioned",
      "priority": "high | medium | low"
    }}
  ],
  "risks": [
    {{
      "title": "Risk title",
      "description": "Risk description",
      "severity": "critical | high | medium | low",
      "category": "technical | resource | timeline | dependency | other",
      "mitigation": "Suggested mitigation or null"
    }}
  ],
  "discussion_points": ["Key discussion point 1", "Key discussion point 2"],
  "assumptions": ["Assumption 1", "Assumption 2"],
  "summary": "2-4 sentence meeting summary"
}}

Rules:
- Extract ALL action items — do not miss any commitment made.
- Mark blockers and dependencies as risks.
- Return ONLY valid JSON, no markdown fences.

Transcript:
---
{transcript}
---
"""


class NoteTakingAgent(BaseAgent):
    name = "note_taking"
    description = (
        "Processes meeting transcripts and extracts structured notes: "
        "decisions, action items, risks, discussion points, and assumptions."
    )

    async def run(self, transcript: str, **kwargs: Any) -> MeetingNotes:
        """
        Parse a meeting transcript and return structured MeetingNotes.

        Parameters
        ----------
        transcript:
            Raw meeting transcript text (from ASR or manual upload).
        """
        if not transcript or not transcript.strip():
            return MeetingNotes(summary="No transcript provided.")

        prompt = NOTE_TAKING_PROMPT.format(transcript=transcript[:12000])
        raw = await self._call_llm(prompt)
        data = self._parse_json(raw)

        return MeetingNotes(
            decisions=data.get("decisions", []),
            action_items=data.get("action_items", []),
            risks=data.get("risks", []),
            discussion_points=data.get("discussion_points", []),
            assumptions=data.get("assumptions", []),
            summary=data.get("summary"),
        )

    # ------------------------------------------------------------------
    # Audio transcription helper
    # ------------------------------------------------------------------

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe an audio file to text using OpenAI Whisper.
        Returns the transcript string.
        """
        try:
            import whisper  # type: ignore

            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            return result["text"]
        except ImportError:
            logger.warning("whisper not installed; using OpenAI API transcription")
            return await self._transcribe_via_api(audio_path)
        except Exception as exc:
            logger.error("Audio transcription failed: %s", exc)
            raise

    async def _transcribe_via_api(self, audio_path: str) -> str:
        """Fallback: use OpenAI Audio API for transcription."""
        from openai import AsyncOpenAI

        from src.backend.config import get_settings

        client = AsyncOpenAI(api_key=get_settings().openai_api_key)
        with open(audio_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model="whisper-1", file=f
            )
        return response.text

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
        logger.warning("NoteTakingAgent: could not parse LLM JSON output")
        return {}
