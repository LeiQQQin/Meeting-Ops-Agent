# API Design

## Base URL

```
http://localhost:8000
```

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Authentication

MVP uses no authentication. In production, add JWT middleware:
```
Authorization: Bearer <token>
```

---

## Endpoints

### System

#### `GET /health`
Returns service health and active connector list.

```json
{
  "status": "ok",
  "connectors": ["github", "slack"],
  "meetings": 3
}
```

---

### Meetings — `/meetings`

#### `POST /meetings` — Create a meeting
```json
// Request body
{
  "title": "Q3 Sprint Review",
  "description": "Review sprint 12 outcomes and plan sprint 13",
  "scheduled_at": "2024-06-14T10:00:00Z",
  "participants": [
    {"name": "Alice", "email": "alice@example.com", "role": "PM"},
    {"name": "Bob", "role": "Engineer"}
  ],
  "project_tags": ["sprint-12", "frontend"],
  "connectors": ["github", "slack"]
}
```
Response: `201 Meeting`

#### `GET /meetings` — List all meetings
Response: `200 Meeting[]`

#### `GET /meetings/{id}` — Get meeting detail
Response: `200 Meeting` or `404`

#### `POST /meetings/{id}/prepare` — Generate pre-meeting brief
Triggers the Context Agent.
Response: `200 PreMeetingBrief`

```json
{
  "meeting_id": "...",
  "goals": ["Align on Q3 roadmap", "Resolve sprint 12 blockers"],
  "pending_items": ["API rate limiting decision pending"],
  "decision_questions": ["Should we delay the mobile release?"],
  "suggested_agenda": [
    {"topic": "Sprint 12 retro", "duration_minutes": 20, "owner": "Alice"},
    {"topic": "Sprint 13 planning", "duration_minutes": 30, "owner": "Bob"}
  ],
  "context_summary": "Last sprint had 2 blockers. 85% completion rate."
}
```

#### `POST /meetings/{id}/transcript` — Upload transcript
Query params:
- `transcript_text` (string) — raw transcript text, OR
- `file` (multipart) — audio file (.mp3/.wav/.m4a/etc.)
- `require_confirmation` (bool, default `true`) — if true, tasks won't be pushed to external systems until confirmed

Response: `200 TranscriptUploadResponse`

#### `POST /meetings/{id}/confirm-tasks` — Confirm and sync tasks
After reviewing enriched action items, confirm to push them to external connectors.
Response:
```json
{
  "synced_count": 4,
  "tasks": [...]
}
```

#### `POST /meetings/{id}/followup` — Send follow-up messages
Sends via configured messaging connector (default: Slack).
Query params: `channels`, `connector`

#### `GET /meetings/{id}/notes` — Get structured meeting notes
Response: `200 MeetingNotes`

---

### Tasks — `/tasks`

#### `GET /tasks/{meeting_id}` — List action items for a meeting
Response: `200 ActionItem[]`

#### `PATCH /tasks/{meeting_id}/{task_id}` — Update an action item
```json
{
  "owner": "Charlie",
  "due_date": "2024-06-20T00:00:00Z",
  "status": "in_progress",
  "acceptance_criteria": "All tests pass with >80% coverage"
}
```

#### `GET /tasks/{meeting_id}/risks` — List identified risks
Response: `200 RiskItem[]`

#### `GET /tasks/weekly-report` — Generate weekly report
Query params: `meeting_ids` (optional, comma-separated)

---

### Agents — `/agents`

#### `GET /agents` — List all registered agents

#### `POST /agents/{meeting_id}/run-risk-check` — Manual risk check

#### `POST /agents/{meeting_id}/run-followup-check` — Manual follow-up check

---

## Data Models

### Meeting
```typescript
{
  id: string;
  title: string;
  description?: string;
  status: "scheduled" | "in_progress" | "completed" | "follow_up" | "closed";
  scheduled_at?: string;  // ISO 8601
  started_at?: string;
  ended_at?: string;
  participants: Participant[];
  project_tags: string[];
  connectors: string[];
  transcript?: string;
  notes?: MeetingNotes;
  pre_meeting_brief?: PreMeetingBrief;
  created_at: string;
  updated_at: string;
}
```

### MeetingNotes
```typescript
{
  decisions: string[];
  action_items: ActionItemRaw[];
  risks: RiskRaw[];
  discussion_points: string[];
  assumptions: string[];
  summary?: string;
}
```

### ActionItem
```typescript
{
  id: string;
  meeting_id: string;
  title: string;
  description?: string;
  owner?: string;
  due_date?: string;
  acceptance_criteria?: string;
  priority: "high" | "medium" | "low";
  status: "todo" | "in_progress" | "blocked" | "done" | "overdue";
  external_id?: string;
  external_url?: string;
  connector?: string;
  created_at: string;
}
```

### RiskItem
```typescript
{
  id: string;
  meeting_id: string;
  title: string;
  description?: string;
  severity: "critical" | "high" | "medium" | "low";
  category: "timeline" | "dependency" | "resource" | "scope" | "other";
  affected_tasks: string[];
  mitigation?: string;
  owner?: string;
  is_resolved: boolean;
}
```

---

## Example: End-to-End Flow

```bash
# 1. Create a meeting
curl -X POST http://localhost:8000/meetings \
  -H "Content-Type: application/json" \
  -d '{"title": "Sprint Review", "project_tags": ["sprint-12"]}'

# 2. Generate pre-meeting brief (replace <id> with the returned id)
curl -X POST http://localhost:8000/meetings/<id>/prepare

# 3. Upload transcript
curl -X POST "http://localhost:8000/meetings/<id>/transcript?transcript_text=We+decided+to+ship+next+week.+Alice+will+update+the+docs+by+Friday."

# 4. Review action items
curl http://localhost:8000/tasks/<id>

# 5. Confirm and sync to GitHub
curl -X POST http://localhost:8000/meetings/<id>/confirm-tasks

# 6. Send Slack follow-up
curl -X POST "http://localhost:8000/meetings/<id>/followup?channels=%23engineering"

# 7. Get weekly report
curl http://localhost:8000/tasks/weekly-report
```
