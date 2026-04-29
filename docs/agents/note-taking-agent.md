# Note-taking Agent

## Purpose
Processes meeting transcripts (text or audio) and extracts structured meeting notes.

## Inputs
- `transcript`: Raw meeting transcript text

## Output: `MeetingNotes`
```json
{
  "decisions": ["We will ship in Q3"],
  "action_items": [
    {
      "title": "Update API docs",
      "owner": "Alice",
      "due_date": "2024-06-15",
      "acceptance_criteria": "All endpoints documented",
      "priority": "high"
    }
  ],
  "risks": [{"title": "Third-party API rate limit", "severity": "medium"}],
  "discussion_points": ["Discussed migration path"],
  "assumptions": ["Budget is approved"],
  "summary": "Team aligned on Q3 roadmap."
}
```

## Audio Transcription
The agent supports audio files via:
1. **Local Whisper** (if `openai-whisper` is installed)
2. **OpenAI Audio API** (fallback, requires `OPENAI_API_KEY`)

Supported formats: MP3, MP4, WAV, M4A, WebM, OGG

## Extraction Rules
- Extracts ALL action items — does not miss any commitment made
- Marks blockers and dependencies as risks
- Returns structured JSON, not markdown
