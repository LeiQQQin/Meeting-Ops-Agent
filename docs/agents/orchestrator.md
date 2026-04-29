# Orchestrator

## Overview

The Orchestrator is the central coordinator of the Meeting-Ops-Agent system. It:
- Manages the meeting lifecycle state machine
- Dispatches work to specialised agents
- Manages connector connections
- Maintains the meeting and task store

## Lifecycle States

```
SCHEDULED → IN_PROGRESS → COMPLETED → FOLLOW_UP → CLOSED
```

## Key Methods

| Method | Trigger | Description |
|--------|---------|-------------|
| `on_meeting_created(meeting)` | Meeting created | Registers meeting |
| `prepare_meeting(meeting)` | Pre-meeting | Triggers Context Agent |
| `process_transcript(meeting, transcript)` | Post-meeting | Note-taking + Task + Risk agents |
| `confirm_and_sync_tasks(meeting_id)` | User confirmation | Pushes tasks to connectors |
| `send_followup(meeting_id)` | Post-meeting | Triggers Follow-up Agent |
| `run_periodic_check(meeting_id)` | Scheduled | Overdue check + risk update |
| `get_weekly_report()` | Weekly | Generates weekly report |

## Configuration

The Orchestrator is initialised on application startup and auto-detects enabled connectors based on environment variables.
