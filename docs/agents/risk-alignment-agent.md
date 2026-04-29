# Risk & Alignment Agent

## Purpose
Detects task delays, dependency blockers, and goal drift. Generates a risk register and project health score.

## Risk Detection

### Rule-based (deterministic)
| Condition | Severity | Category |
|-----------|----------|----------|
| Task overdue | HIGH | timeline |
| Deadline within 3 days, task not started | MEDIUM | timeline |
| No owner assigned | MEDIUM | resource |
| Task status = BLOCKED | HIGH | dependency |

### LLM-based (semantic)
Analyses action items against project goals and OKRs to identify:
- Scope drift
- Resource conflicts
- Dependency chains

## Health Score (0-100)
```
base_score = completion_rate (0-100)
- 20 per CRITICAL risk
- 10 per HIGH risk
- 5 per MEDIUM risk
min 0, max 100
```

## Output
```json
{
  "risks": [...],
  "health_score": 72,
  "health_summary": "Good progress overall. One critical blocker needs attention.",
  "completion_rate": 60.0
}
```
