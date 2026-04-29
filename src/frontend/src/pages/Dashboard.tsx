import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { meetingsApi, Meeting } from "../api/client";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    meetingsApi
      .list()
      .then(setMeetings)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const stats = {
    total: meetings.length,
    completed: meetings.filter((m) => ["completed", "follow_up", "closed"].includes(m.status)).length,
    inProgress: meetings.filter((m) => m.status === "in_progress").length,
    scheduled: meetings.filter((m) => m.status === "scheduled").length,
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Meeting Ops Agent — AI-powered meeting lifecycle management</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Meetings", value: stats.total, color: "blue" },
          { label: "Completed", value: stats.completed, color: "green" },
          { label: "In Progress", value: stats.inProgress, color: "yellow" },
          { label: "Scheduled", value: stats.scheduled, color: "indigo" },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {loading ? "—" : stat.value}
            </p>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🤖 How Meeting Ops Agent Works</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {[
            {
              emoji: "📋",
              title: "1. Pre-meeting Prep",
              desc: "Context Agent aggregates historical notes, Jira tickets, and GitHub issues. Generates a brief with goals, pending items, and agenda suggestions.",
            },
            {
              emoji: "🎙️",
              title: "2. Post-meeting Processing",
              desc: "Upload transcript or audio. Note-taking Agent extracts decisions, action items, risks, and assumptions. Task Agent enriches items with owners and deadlines.",
            },
            {
              emoji: "🔁",
              title: "3. Follow-up & Tracking",
              desc: "Follow-up Agent sends Slack/email reminders. Risk Agent monitors overdue tasks and dependency blockers. Weekly reports keep everyone aligned.",
            },
          ].map((step) => (
            <div key={step.title} className="p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">{step.emoji}</div>
              <h3 className="font-medium text-gray-900 mb-1">{step.title}</h3>
              <p className="text-sm text-gray-600">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent meetings */}
      {meetings.length > 0 && (
        <div>
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Recent Meetings</h2>
            <Link to="/meetings" className="text-sm text-blue-600 hover:underline">
              View all →
            </Link>
          </div>
          <div className="space-y-2">
            {meetings.slice(0, 5).map((m) => (
              <Link
                key={m.id}
                to={`/meetings/${m.id}`}
                className="flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 p-3 hover:shadow-md transition-shadow"
              >
                <div>
                  <span className="font-medium text-gray-900 text-sm">{m.title}</span>
                  {m.project_tags.length > 0 && (
                    <span className="ml-2 text-xs text-gray-400">{m.project_tags.slice(0, 2).join(", ")}</span>
                  )}
                </div>
                <StatusBadge status={m.status} />
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Agents */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">🧠 Active Agents</h2>
        <div className="grid md:grid-cols-2 gap-3">
          {[
            { name: "Orchestrator", desc: "Central coordinator — manages meeting lifecycle state machine and dispatches to specialised agents.", icon: "🎛️" },
            { name: "Context Agent", desc: "Aggregates historical meeting notes, PRDs, Jira/GitHub issues, and generates the pre-meeting brief.", icon: "🔍" },
            { name: "Note-taking Agent", desc: "Processes transcripts and extracts decisions, action items, risks, and assumptions.", icon: "📝" },
            { name: "Task Agent", desc: "Enriches action items with owners, due dates, acceptance criteria and syncs to task systems.", icon: "✅" },
            { name: "Follow-up Agent", desc: "Sends reminders, monitors task progress, and generates weekly status reports.", icon: "📨" },
            { name: "Risk & Alignment Agent", desc: "Detects delays, blockers and goal drift. Generates risk registers and health scores.", icon: "⚠️" },
          ].map((agent) => (
            <div key={agent.name} className="flex gap-3 p-3 bg-gray-50 rounded-lg">
              <span className="text-xl">{agent.icon}</span>
              <div>
                <p className="font-medium text-gray-900 text-sm">{agent.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">{agent.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
