import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { meetingsApi } from "../api/client";

export default function NewMeeting() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "",
    description: "",
    project_tags: "",
    participants: "",
    connectors: [] as string[],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connectorOptions = ["github", "jira", "slack", "notion"];

  const toggleConnector = (name: string) => {
    setForm((f) => ({
      ...f,
      connectors: f.connectors.includes(name)
        ? f.connectors.filter((c) => c !== name)
        : [...f.connectors, name],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) {
      setError("Meeting title is required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const participants = form.participants
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .map((name) => ({ name }));
      const project_tags = form.project_tags
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const meeting = await meetingsApi.create({
        title: form.title,
        description: form.description || undefined,
        participants,
        project_tags,
        connectors: form.connectors,
      });
      navigate(`/meetings/${meeting.id}`);
    } catch {
      setError("Failed to create meeting. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Meeting</h1>
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-5">
        {error && (
          <div className="px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Meeting Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="e.g. Q3 Planning Sprint Review"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="What is this meeting about?"
            rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Participants
          </label>
          <input
            type="text"
            value={form.participants}
            onChange={(e) => setForm({ ...form, participants: e.target.value })}
            placeholder="Alice, Bob, Charlie (comma-separated)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Project Tags
          </label>
          <input
            type="text"
            value={form.project_tags}
            onChange={(e) => setForm({ ...form, project_tags: e.target.value })}
            placeholder="frontend, sprint-12, onboarding (comma-separated)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enable Connectors
          </label>
          <div className="flex flex-wrap gap-2">
            {connectorOptions.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => toggleConnector(c)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                  form.connectors.includes(c)
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 border-gray-300 hover:border-blue-400"
                }`}
              >
                {c.charAt(0).toUpperCase() + c.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={() => navigate("/meetings")}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Creating…" : "Create Meeting"}
          </button>
        </div>
      </form>
    </div>
  );
}
