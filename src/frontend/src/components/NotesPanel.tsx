import React from "react";
import { MeetingNotes } from "../api/client";

interface Props {
  notes: MeetingNotes | null;
}

function Section({ title, items, emoji }: { title: string; items: string[]; emoji: string }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <h3 className="font-semibold text-gray-900 mb-2">{emoji} {title}</h3>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-gray-700 flex gap-2">
            <span className="text-gray-400 shrink-0">•</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function NotesPanel({ notes }: Props) {
  if (!notes)
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-400">
        No notes yet. Upload a meeting transcript to generate structured notes.
      </div>
    );

  return (
    <div className="space-y-6">
      {notes.summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-1">📄 Summary</h3>
          <p className="text-blue-800 text-sm">{notes.summary}</p>
        </div>
      )}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5 space-y-5">
        <Section title="Decisions" items={notes.decisions} emoji="✅" />
        <Section
          title="Action Items"
          items={notes.action_items?.map((a: any) =>
            typeof a === "string" ? a : `${a.title}${a.owner ? ` (${a.owner})` : ""}`
          )}
          emoji="📌"
        />
        <Section
          title="Risks & Blockers"
          items={notes.risks?.map((r: any) =>
            typeof r === "string" ? r : `[${r.severity || "medium"}] ${r.title}`
          )}
          emoji="⚠️"
        />
        <Section title="Key Discussion Points" items={notes.discussion_points} emoji="💬" />
        <Section title="Assumptions" items={notes.assumptions} emoji="🤔" />
      </div>
    </div>
  );
}
