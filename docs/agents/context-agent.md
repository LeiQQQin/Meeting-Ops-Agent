# Context Agent

## Purpose
Aggregates historical meeting notes, project documents, and third-party context (GitHub Issues, Jira tickets, Notion pages) to generate a comprehensive pre-meeting brief.

## Inputs
- `meeting`: The upcoming meeting (title, description, participants, tags)
- `connectors`: Connected BaseConnector instances to query for context
- `recent_meetings`: Recent meetings with the same project tags (for historical notes)

## Output: `PreMeetingBrief`
```json
{
  "goals": ["Align on sprint goals"],
  "pending_items": ["API design decision still open"],
  "decision_questions": ["Should we use GraphQL or REST?"],
  "suggested_agenda": [
    {"topic": "Retro", "duration_minutes": 15, "owner": "Alice"}
  ],
  "context_summary": "Previous sprint had 85% completion."
}
```

## LLM Prompt Strategy
The agent uses a structured JSON prompt asking the LLM to synthesise context items into goals, pending items, decision questions, and agenda suggestions.

## Configuration
No additional configuration required. Uses the shared LLM from `BaseAgent`.
