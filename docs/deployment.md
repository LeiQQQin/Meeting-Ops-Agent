# Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional but recommended)
- OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/LeiQQQin/Meeting-Ops-Agent.git
cd Meeting-Ops-Agent
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and any connector credentials
```

### 3. Run with Docker Compose (recommended)

```bash
docker-compose up --build
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 4. Or run manually

**Backend:**
```bash
cd src/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd src/frontend
npm install
npm start
```

---

## Production Deployment

### Environment Variables

Set all required variables in `.env` (see `.env.example`).

Key variables for production:
```
APP_ENV=production
APP_SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://user:password@host:5432/meeting_ops
OPENAI_API_KEY=<your-key>
```

### Database Migration

For production, switch from SQLite to PostgreSQL by updating `DATABASE_URL`.

### Scaling

The backend is stateless (Orchestrator can be backed by Redis/DB).
Scale horizontally with:
```bash
docker-compose up --scale backend=3
```

---

## Connector Setup

### GitHub
1. Create a [Personal Access Token](https://github.com/settings/tokens) with `repo` scope.
2. Set `GITHUB_TOKEN` and `GITHUB_DEFAULT_REPO` in `.env`.

### Jira
1. Create an [API Token](https://id.atlassian.com/manage-profile/security/api-tokens).
2. Set `JIRA_SERVER_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN`, `JIRA_DEFAULT_PROJECT_KEY`.

### Slack
1. Create a [Slack App](https://api.slack.com/apps) with `chat:write` bot scope.
2. Install to workspace and copy Bot User OAuth Token.
3. Set `SLACK_BOT_TOKEN` and `SLACK_DEFAULT_CHANNEL`.

### Notion
1. Create a [Notion Integration](https://www.notion.so/my-integrations).
2. Share your target database with the integration.
3. Set `NOTION_API_KEY` and `NOTION_DEFAULT_DATABASE_ID`.

---

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "connectors": ["github", "slack"],
  "meetings": 0
}
```
