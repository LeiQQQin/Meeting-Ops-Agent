# Task Agent

## Purpose
Enriches raw action items extracted from meeting notes with owners, due dates, and acceptance criteria. Optionally syncs them to configured third-party task systems.

## Inputs
- `action_items`: Raw action item dicts from NoteTakingAgent
- `meeting_title`: Context for enrichment
- `participants`: For owner inference
- `connectors`: Connected task-system connectors
- `require_confirmation`: Whether to sync immediately or wait for user approval

## Enrichment
For each action item, the agent:
1. Writes a clear, specific title
2. Infers the owner from participant context
3. Suggests a due date based on mentioned timelines
4. Writes measurable acceptance criteria
5. Assigns priority (high/medium/low)

## Sync Flow
```
require_confirmation=True (default):
  ActionItem created locally → user reviews → POST /confirm-tasks → connector.create_task()

require_confirmation=False:
  ActionItem created locally → connector.create_task() immediately
```

## Clarifications
If critical fields (owner, due date) are missing, the agent can generate clarification questions via `generate_clarifications()`.

## Supported Connectors
- GitHub Issues
- Jira
- Notion Database
- Slack (posts reminder message)
