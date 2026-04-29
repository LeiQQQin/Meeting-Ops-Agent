import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingsApi, Meeting } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function MeetingList() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    meetingsApi
      .list()
      .then(setMeetings)
      .catch(() => setError("Failed to load meetings. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );

  if (error)
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
      </div>
    );

  if (meetings.length === 0)
    return (
      <div className="text-center py-20">
        <p className="text-gray-500 text-lg mb-4">No meetings yet.</p>
        <Link
          to="/new-meeting"
          className="btn-primary inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Create your first meeting
        </Link>
      </div>
    );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Meetings</h1>
        <Link
          to="/new-meeting"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          + New Meeting
        </Link>
      </div>
      <div className="space-y-3">
        {meetings.map((m) => (
          <Link
            key={m.id}
            to={`/meetings/${m.id}`}
            className="block bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-gray-900">{m.title}</h2>
                {m.description && (
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {m.description}
                  </p>
                )}
                {m.project_tags.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {m.project_tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <StatusBadge status={m.status} />
            </div>
            <div className="text-xs text-gray-400 mt-2">
              {m.participants.length > 0 &&
                `${m.participants.length} participant${m.participants.length > 1 ? "s" : ""} · `}
              {new Date(m.created_at).toLocaleDateString()}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
