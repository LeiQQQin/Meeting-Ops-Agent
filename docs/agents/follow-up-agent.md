# Follow-up Agent

## Purpose
Monitors action item progress and sends periodic reminders to responsible parties. Generates weekly status reports.

## Key Methods

### `run()` — Post-meeting follow-up
Sends a formatted follow-up message with all action items to specified channels.

### `check_overdue()` — Overdue detection
Scans action items for past-due dates and sends reminder messages.

### `generate_weekly_report()` — Weekly report
Generates a `WeeklyReport` with:
- Completed tasks
- In-progress tasks
- Overdue tasks
- Active risks
- Executive summary (LLM-generated)

## Scheduling
Use APScheduler or Celery to schedule periodic checks:
```python
# Every 24 hours
scheduler.add_job(
    orchestrator.run_periodic_check,
    "interval",
    hours=settings.followup_check_interval_hours
)
```

## Message Format (Slack)
```
📋 Meeting Follow-up — Action Items
• *Update API docs*  |  Owner: Alice  |  Due: 2024-06-15
• *Deploy to staging*  |  Owner: Bob  |  Due: 2024-06-17
@alice @bob
```
