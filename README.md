# 🤖 Meeting-Ops-Agent

**AI-powered meeting operations system** — automates the full meeting lifecycle from pre-meeting preparation through post-meeting task tracking, follow-up, and risk alignment.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)

---

## ✨ What It Does

Meeting-Ops-Agent transforms meetings from "we talked about it" to "it's done." It uses a **multi-agent AI architecture** to:

| Phase | What happens |
|-------|-------------|
| **Pre-meeting** | Context Agent aggregates Jira/GitHub/Notion context → generates a one-page brief with goals, pending items, and agenda |
| **Post-meeting** | Note-taking Agent parses transcript → extracts decisions, action items, risks, and assumptions |
| **Task management** | Task Agent enriches items with owners, due dates, acceptance criteria → syncs to GitHub/Jira |
| **Follow-up** | Follow-up Agent sends Slack reminders and monitors task completion |
| **Risk tracking** | Risk & Alignment Agent detects blockers/overdue/scope drift → generates health scores and weekly reports |

---

## 🧠 Agent Architecture

```
┌─────────────────────────────────────────┐
│              Orchestrator               │  ← Central coordinator
│         (state machine + dispatch)      │
└──┬──────┬──────┬──────┬──────┬──────────┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
Context  Note   Task  Follow  Risk &
Agent   Taking  Agent  Up    Alignment
        Agent         Agent   Agent
```

1. **Orchestrator** — Manages meeting lifecycle state machine, dispatches to agents
2. **Context Agent** — Aggregates Notion/GitHub/Jira context, produces pre-meeting brief
3. **Note-taking Agent** — Processes transcripts → structured notes (decisions, actions, risks)
4. **Task Agent** — Enriches action items with owners/deadlines/criteria, syncs to task systems
5. **Follow-up Agent** — Sends reminders, monitors progress, generates weekly reports
6. **Risk & Alignment Agent** — Detects delays/blockers/drift, calculates health scores

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI |
| LLM / Agents | LangChain + OpenAI GPT-4o |
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Task Queue | Celery + Redis |
| Storage | SQLite (dev) / PostgreSQL (prod) |
| Audio transcription | OpenAI Whisper |
| Deployment | Docker + Docker Compose |

---

## 🚀 Quick Start

### Option 1: Docker Compose (recommended)

```bash
git clone https://github.com/LeiQQQin/Meeting-Ops-Agent.git
cd Meeting-Ops-Agent
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY
docker-compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual setup

```bash
# Setup
./scripts/setup.sh

# Configure
cp .env.example .env
# Edit .env

# Run
./scripts/run_local.sh
```

---

## 📁 Project Structure

```
Meeting-Ops-Agent/
├── src/
│   ├── backend/
│   │   ├── main.py                     # FastAPI app entry point
│   │   ├── config.py                   # Configuration (pydantic-settings)
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── agents/
│   │   │   ├── base.py                 # BaseAgent with shared LLM client
│   │   │   ├── orchestrator.py         # Central coordinator
│   │   │   ├── context_agent.py        # Pre-meeting context aggregation
│   │   │   ├── note_taking_agent.py    # Transcript → structured notes
│   │   │   ├── task_agent.py           # Action item enrichment & sync
│   │   │   ├── follow_up_agent.py      # Reminders & weekly reports
│   │   │   └── risk_alignment_agent.py # Risk detection & health scoring
│   │   ├── connectors/
│   │   │   ├── base.py                 # BaseConnector interface
│   │   │   ├── github_connector.py
│   │   │   ├── jira_connector.py
│   │   │   ├── slack_connector.py
│   │   │   └── notion_connector.py
│   │   ├── models/
│   │   │   ├── meeting.py              # Meeting, MeetingNotes, PreMeetingBrief
│   │   │   └── task.py                 # ActionItem, RiskItem, WeeklyReport
│   │   └── api/
│   │       ├── meetings.py             # Meeting CRUD + lifecycle endpoints
│   │       ├── tasks.py                # Action item & risk endpoints
│   │       └── agents.py              # Agent status & trigger endpoints
│   └── frontend/
│       ├── src/
│       │   ├── App.tsx
│       │   ├── api/client.ts           # Typed API client
│       │   ├── pages/                  # Dashboard, MeetingList, MeetingDetail, NewMeeting
│       │   └── components/             # ActionItemsPanel, RiskPanel, NotesPanel, …
│       └── Dockerfile
├── tests/
│   ├── test_agents.py                  # Agent unit tests (mocked LLM)
│   ├── test_connectors.py              # Connector unit tests
│   └── test_api.py                     # API integration tests
├── docs/
│   ├── architecture.md
│   ├── api-design.md
│   ├── deployment.md
│   └── agents/                         # Per-agent documentation
├── scripts/
│   ├── setup.sh
│   └── run_local.sh
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

## 🔌 Connectors

Connectors are pluggable and implement a unified `BaseConnector` interface.

| Connector | Purpose | Required credentials |
|-----------|---------|---------------------|
| GitHub | Create Issues, fetch context | `GITHUB_TOKEN`, `GITHUB_DEFAULT_REPO` |
| Jira | Create tickets, fetch context | `JIRA_SERVER_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN` |
| Slack | Send reminders, follow-ups | `SLACK_BOT_TOKEN` |
| Notion | Create DB entries, fetch pages | `NOTION_API_KEY`, `NOTION_DEFAULT_DATABASE_ID` |

Add a custom connector by implementing `BaseConnector` and registering it in `CONNECTOR_REGISTRY`.

---

## 🧪 Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## 📖 API Example

```bash
# Create meeting
curl -X POST http://localhost:8000/meetings \
  -H "Content-Type: application/json" \
  -d '{"title": "Sprint Review", "project_tags": ["sprint-12"], "connectors": ["github"]}'

# Generate pre-meeting brief
curl -X POST http://localhost:8000/meetings/{id}/prepare

# Upload transcript
curl -X POST "http://localhost:8000/meetings/{id}/transcript" \
  -d '{"transcript_text": "We decided to ship next week. Alice will update docs by Friday."}'

# View action items
curl http://localhost:8000/tasks/{id}

# Confirm and sync to GitHub
curl -X POST http://localhost:8000/meetings/{id}/confirm-tasks

# Send Slack follow-up
curl -X POST "http://localhost:8000/meetings/{id}/followup?channels=#engineering"
```

Full API docs: [docs/api-design.md](docs/api-design.md)

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Design](docs/api-design.md)
- [Deployment Guide](docs/deployment.md)
- [Agent Docs](docs/agents/)

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/my-feature`
3. Add tests for new functionality
4. Submit a pull request

---

## 📄 License

MIT — see [LICENSE](LICENSE)
