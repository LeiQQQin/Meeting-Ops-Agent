# Architecture Overview

## System Architecture

Meeting-Ops-Agent uses a multi-agent architecture where an **Orchestrator** coordinates specialised agents across the full meeting lifecycle.

```
┌────────────────────────────────────────────────────────────────┐
│                        Web UI (React)                          │
│              Meetings · Notes · Tasks · Risks                  │
└───────────────────────────┬────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                              │
│  /meetings  /tasks  /agents  /health                           │
└───────────────────────────┬────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────┐
│                      Orchestrator                              │
│          State machine + event dispatcher                      │
└─┬──────┬──────┬──────┬──────┬───────────────────────────────--┘
  │      │      │      │      │
  ▼      ▼      ▼      ▼      ▼
Context  Note   Task  Follow  Risk &
Agent   Taking  Agent  up    Alignment
        Agent         Agent   Agent
  │      │      │      │      │
  └──────┴──────┴──────┴──────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
 GitHub         Jira        Slack
Connector    Connector   Connector
                               │
                           Notion
                          Connector
```

## Meeting Lifecycle State Machine

```
SCHEDULED ──► IN_PROGRESS ──► COMPLETED ──► FOLLOW_UP ──► CLOSED
    │                                            │
    └── prepare_meeting()                        └── run_periodic_check()
    └── context_agent.run()                      └── follow_up_agent.check_overdue()
                                                 └── risk_agent.run()
```

### Events

| Event | Trigger | Handler |
|-------|---------|---------|
| `meeting_created` | User creates a meeting | `Orchestrator.on_meeting_created()` |
| `meeting_scheduled` | Meeting is upcoming | `Orchestrator.prepare_meeting()` → Context Agent |
| `transcript_ready` | Transcript uploaded | `Orchestrator.process_transcript()` → Note-taking + Task + Risk |
| `user_confirmed` | User approves tasks | `Orchestrator.confirm_and_sync_tasks()` → Task Agent → Connectors |
| `followup_triggered` | Scheduled/manual | `Orchestrator.send_followup()` → Follow-up Agent |
| `periodic_check` | Cron schedule | `Orchestrator.run_periodic_check()` → Follow-up + Risk Agents |

## Component Responsibilities

### Orchestrator
- Central singleton, lives for the lifetime of the application
- Maintains in-memory meeting and action item stores (extend to DB in production)
- Manages connector lifecycle (connect/disconnect)
- Dispatches work to specialised agents

### Agents
Each agent is a stateless worker that:
1. Accepts typed inputs
2. Calls the shared LLM (`ChatOpenAI`) via `BaseAgent._call_llm()`
3. Returns typed Pydantic models

### Connectors
Each connector wraps a third-party SDK:
- Implements `BaseConnector` interface
- Can be swapped or extended without changing agent code
- Registered in `CONNECTOR_REGISTRY` for dynamic instantiation

## Data Flow: Transcript Processing

```
User → POST /meetings/{id}/transcript
         │
         ▼
   NoteTakingAgent.run(transcript)
         │
         ▼  JSON (decisions, action_items, risks, …)
   MeetingNotes
         │
         ├──► TaskAgent.run(action_items)
         │         │
         │         ▼ enriched ActionItem[]
         │    [if no require_confirmation]
         │         ▼
         │    Connector.create_task() → GitHub/Jira/Notion
         │
         └──► RiskAlignmentAgent.run(action_items)
                   │
                   ▼ RiskItem[], health_score, health_summary
```

## Technology Choices

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.11 + FastAPI | Type safety, async support, OpenAPI auto-docs |
| LLM | LangChain + OpenAI | Pluggable models, structured prompting |
| Frontend | React 18 + TypeScript + Tailwind | Fast, type-safe, utility-first CSS |
| Task Queue | Celery + Redis | Background jobs for scheduled checks |
| Storage | SQLite (dev) / PostgreSQL (prod) | Simple to get started, easy to scale |
| Audio | OpenAI Whisper | Local or API-based transcription |
| Deployment | Docker + docker-compose | Reproducible, easy to self-host |
