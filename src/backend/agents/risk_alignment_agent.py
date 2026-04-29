"""
Risk & Alignment Agent — detects task delays, dependency blockers and
goal drift. Cross-references action items against OKRs / milestones and
produces a risk register with health indicators.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.backend.agents.base import BaseAgent
from src.backend.models.task import ActionItem, RiskItem, RiskSeverity, TaskStatus

logger = logging.getLogger(__name__)

RISK_ANALYSIS_PROMPT = """\
You are the Risk & Alignment Agent for the Meeting Ops system.

Analyse the following action items and project context for risks.
Identify:
1. Timeline risks (tasks with approaching or overdue deadlines).
2. Dependency blockers (tasks waiting on other tasks or people).
3. Resource risks (tasks with no owner or unclear ownership).
4. Scope drift (tasks that seem unrelated to the stated project goals).
5. Any other risks you observe.

Project goals / OKRs: {goals}
Action items:
{items}

Return a JSON array of risk objects:
[
  {{
    "title": "Risk title",
    "description": "Detailed description",
    "severity": "critical | high | medium | low",
    "category": "timeline | dependency | resource | scope | other",
    "affected_tasks": ["task title 1", "task title 2"],
    "mitigation": "Suggested mitigation step"
  }}
]

Return ONLY the JSON array, no markdown fences.
"""

HEALTH_SUMMARY_PROMPT = """\
You are the Risk & Alignment Agent. Given the following project health data,
write a 3-5 sentence executive health summary for the project manager.

Total tasks: {total}
Completed: {completed}
In progress: {in_progress}
Blocked / overdue: {blocked}
Open risks: {risk_count} (critical: {critical}, high: {high})
Completion rate: {completion_rate}%

Be honest about problems but constructive about next steps.
"""


class RiskAlignmentAgent(BaseAgent):
    name = "risk_alignment"
    description = (
        "Detects task delays, dependency blockers and goal drift; "
        "generates a risk register and project health report."
    )

    async def run(
        self,
        action_items: list[ActionItem],
        project_goals: Optional[list[str]] = None,
        existing_risks: Optional[list[RiskItem]] = None,
        meeting_id: str = "",
        **kwargs: Any,
    ) -> dict:
        """
        Analyse action items and return a risk register + health summary.

        Returns
        -------
        dict with keys:
            risks: list[RiskItem]
            health_score: int  (0-100)
            health_summary: str
            completion_rate: float
        """
        project_goals = project_goals or []
        existing_risks = existing_risks or []

        # 1. Rule-based risk detection
        rule_risks = self._detect_rule_based_risks(action_items, meeting_id)

        # 2. LLM-based risk analysis
        llm_risks = await self._analyse_with_llm(action_items, project_goals, meeting_id)

        # 3. Merge and de-duplicate
        all_risks = existing_risks + rule_risks + llm_risks

        # 4. Calculate health score
        health_score = self._calculate_health_score(action_items, all_risks)
        completion_rate = self._completion_rate(action_items)

        # 5. Generate health summary
        health_summary = await self._generate_health_summary(
            action_items, all_risks, health_score, completion_rate
        )

        return {
            "risks": all_risks,
            "health_score": health_score,
            "health_summary": health_summary,
            "completion_rate": completion_rate,
        }

    # ------------------------------------------------------------------
    # Rule-based detection
    # ------------------------------------------------------------------

    def _detect_rule_based_risks(
        self, items: list[ActionItem], meeting_id: str
    ) -> list[RiskItem]:
        risks: list[RiskItem] = []
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        warning_threshold = now + timedelta(days=3)

        for item in items:
            # Overdue
            if item.due_date and item.due_date < now and item.status != TaskStatus.DONE:
                risks.append(
                    RiskItem(
                        meeting_id=meeting_id,
                        title=f"Overdue: {item.title}",
                        description=f"Task '{item.title}' was due on "
                        f"{item.due_date.strftime('%Y-%m-%d')} and is not completed.",
                        severity=RiskSeverity.HIGH,
                        category="timeline",
                        affected_tasks=[item.title],
                        owner=item.owner,
                    )
                )
            # Approaching deadline
            elif (
                item.due_date
                and item.due_date < warning_threshold
                and item.status not in (TaskStatus.DONE, TaskStatus.IN_PROGRESS)
            ):
                risks.append(
                    RiskItem(
                        meeting_id=meeting_id,
                        title=f"Deadline approaching: {item.title}",
                        description=f"Task '{item.title}' is due in less than 3 days "
                        f"and has not started.",
                        severity=RiskSeverity.MEDIUM,
                        category="timeline",
                        affected_tasks=[item.title],
                        owner=item.owner,
                    )
                )
            # No owner
            if not item.owner:
                risks.append(
                    RiskItem(
                        meeting_id=meeting_id,
                        title=f"No owner: {item.title}",
                        description=f"Task '{item.title}' has no assigned owner.",
                        severity=RiskSeverity.MEDIUM,
                        category="resource",
                        affected_tasks=[item.title],
                        mitigation="Assign an owner in the next meeting or via the task system.",
                    )
                )
            # Blocked
            if item.status == TaskStatus.BLOCKED:
                risks.append(
                    RiskItem(
                        meeting_id=meeting_id,
                        title=f"Blocked: {item.title}",
                        description=f"Task '{item.title}' is blocked.",
                        severity=RiskSeverity.HIGH,
                        category="dependency",
                        affected_tasks=[item.title],
                        owner=item.owner,
                    )
                )

        return risks

    # ------------------------------------------------------------------
    # LLM-based analysis
    # ------------------------------------------------------------------

    async def _analyse_with_llm(
        self,
        items: list[ActionItem],
        goals: list[str],
        meeting_id: str,
    ) -> list[RiskItem]:
        if not items:
            return []

        items_text = "\n".join(
            f"- [{item.status.value}] {item.title} | Owner: {item.owner or 'None'} "
            f"| Due: {item.due_date or 'None'}"
            for item in items
        )
        goals_text = "\n".join(f"- {g}" for g in goals) or "Not specified"

        prompt = RISK_ANALYSIS_PROMPT.format(goals=goals_text, items=items_text)
        raw = await self._call_llm(prompt)
        data = self._parse_json_array(raw)

        risks = []
        for r in data:
            try:
                risks.append(
                    RiskItem(
                        meeting_id=meeting_id,
                        title=r.get("title", "Unnamed risk"),
                        description=r.get("description", ""),
                        severity=RiskSeverity(r.get("severity", "medium")),
                        category=r.get("category", "other"),
                        affected_tasks=r.get("affected_tasks", []),
                        mitigation=r.get("mitigation"),
                    )
                )
            except Exception as exc:
                logger.warning("Could not parse risk item: %s — %s", r, exc)

        return risks

    # ------------------------------------------------------------------
    # Health scoring
    # ------------------------------------------------------------------

    def _calculate_health_score(
        self, items: list[ActionItem], risks: list[RiskItem]
    ) -> int:
        if not items:
            return 100

        score = 100
        completion = self._completion_rate(items)
        score = int(completion)

        critical = sum(1 for r in risks if r.severity == RiskSeverity.CRITICAL)
        high = sum(1 for r in risks if r.severity == RiskSeverity.HIGH)
        medium = sum(1 for r in risks if r.severity == RiskSeverity.MEDIUM)

        score -= critical * 20
        score -= high * 10
        score -= medium * 5

        return max(0, min(100, score))

    def _completion_rate(self, items: list[ActionItem]) -> float:
        if not items:
            return 100.0
        done = sum(1 for i in items if i.status == TaskStatus.DONE)
        return round(done / len(items) * 100, 1)

    async def _generate_health_summary(
        self,
        items: list[ActionItem],
        risks: list[RiskItem],
        health_score: int,
        completion_rate: float,
    ) -> str:
        total = len(items)
        completed = sum(1 for i in items if i.status == TaskStatus.DONE)
        in_progress = sum(1 for i in items if i.status == TaskStatus.IN_PROGRESS)
        blocked = sum(
            1
            for i in items
            if i.status in (TaskStatus.BLOCKED, TaskStatus.OVERDUE)
        )
        critical = sum(1 for r in risks if r.severity == RiskSeverity.CRITICAL)
        high = sum(1 for r in risks if r.severity == RiskSeverity.HIGH)

        prompt = HEALTH_SUMMARY_PROMPT.format(
            total=total,
            completed=completed,
            in_progress=in_progress,
            blocked=blocked,
            risk_count=len(risks),
            critical=critical,
            high=high,
            completion_rate=completion_rate,
        )
        return await self._call_llm(prompt)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_json_array(self, raw: str) -> list:
        try:
            result = json.loads(raw)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                    return result if isinstance(result, list) else []
                except json.JSONDecodeError:
                    pass
        return []
