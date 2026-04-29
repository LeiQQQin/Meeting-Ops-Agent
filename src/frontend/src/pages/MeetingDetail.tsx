import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { meetingsApi, tasksApi, agentsApi, Meeting, ActionItem, RiskItem, MeetingNotes } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import ActionItemsPanel from "../components/ActionItemsPanel";
import RiskPanel from "../components/RiskPanel";
import TranscriptUploader from "../components/TranscriptUploader";
import NotesPanel from "../components/NotesPanel";

type Tab = "overview" | "notes" | "tasks" | "risks" | "brief";

export default function MeetingDetail() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [notes, setNotes] = useState<MeetingNotes | null>(null);
  const [tasks, setTasks] = useState<ActionItem[]>([]);
  const [risks, setRisks] = useState<RiskItem[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    if (!id) return;
    try {
      const m = await meetingsApi.get(id);
      setMeeting(m);
      try {
        const n = await meetingsApi.getNotes(id);
        setNotes(n);
      } catch {}
      try {
        const t = await tasksApi.list(id);
        setTasks(t);
      } catch {}
      try {
        const r = await tasksApi.risks(id);
        setRisks(r);
      } catch {}
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [id]);

  const handlePrepare = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await meetingsApi.prepare(id);
      setMessage("Pre-meeting brief generated!");
      loadData();
    } catch {
      setMessage("Failed to generate brief.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmTasks = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await meetingsApi.confirmTasks(id);
      setMessage("Tasks synced to external systems!");
      loadData();
    } catch {
      setMessage("Task sync failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleFollowup = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await meetingsApi.sendFollowup(id);
      setMessage("Follow-up messages sent!");
    } catch {
      setMessage("Follow-up failed.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRiskCheck = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await agentsApi.runRiskCheck(id);
      setMessage("Risk check complete!");
      loadData();
    } catch {
      setMessage("Risk check failed.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading)
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );

  if (!meeting)
    return (
      <div className="text-center py-20 text-gray-500">
        Meeting not found.{" "}
        <Link to="/meetings" className="text-blue-600 underline">
          Back to meetings
        </Link>
      </div>
    );

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "brief", label: "Pre-meeting Brief" },
    { key: "notes", label: "Meeting Notes" },
    { key: "tasks", label: `Tasks (${tasks.length})` },
    { key: "risks", label: `Risks (${risks.length})` },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/meetings" className="text-blue-600 hover:underline text-sm">
          ← Back to meetings
        </Link>
        <div className="flex items-start justify-between mt-2">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{meeting.title}</h1>
            {meeting.description && (
              <p className="text-gray-500 mt-1">{meeting.description}</p>
            )}
            <div className="flex flex-wrap gap-1 mt-2">
              {meeting.project_tags.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                  {t}
                </span>
              ))}
            </div>
          </div>
          <StatusBadge status={meeting.status} />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={handlePrepare}
          disabled={actionLoading}
          className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          📋 Generate Brief
        </button>
        <button
          onClick={handleConfirmTasks}
          disabled={actionLoading || tasks.length === 0}
          className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          ✅ Confirm & Sync Tasks
        </button>
        <button
          onClick={handleFollowup}
          disabled={actionLoading}
          className="px-3 py-1.5 bg-yellow-600 text-white text-sm rounded-lg hover:bg-yellow-700 disabled:opacity-50"
        >
          📨 Send Follow-up
        </button>
        <button
          onClick={handleRiskCheck}
          disabled={actionLoading}
          className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700 disabled:opacity-50"
        >
          ⚠️ Run Risk Check
        </button>
      </div>

      {message && (
        <div className="mb-4 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg text-blue-700 text-sm">
          {message}
          <button onClick={() => setMessage(null)} className="ml-2 text-blue-400 hover:text-blue-600">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Participants</h3>
            {meeting.participants.length === 0 ? (
              <p className="text-gray-400 text-sm">No participants added.</p>
            ) : (
              <ul className="space-y-1">
                {meeting.participants.map((p, i) => (
                  <li key={i} className="text-sm text-gray-700">
                    {p.name}{p.role && <span className="text-gray-400"> · {p.role}</span>}
                    {p.email && <span className="text-gray-400"> · {p.email}</span>}
                  </li>
                ))}
              </ul>
            )}
          </div>
          <TranscriptUploader meetingId={meeting.id} onSuccess={loadData} />
        </div>
      )}

      {activeTab === "brief" && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          {meeting.pre_meeting_brief ? (
            <div className="space-y-4">
              {meeting.pre_meeting_brief.context_summary && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Context Summary</h3>
                  <p className="text-gray-700 text-sm">{meeting.pre_meeting_brief.context_summary}</p>
                </div>
              )}
              {meeting.pre_meeting_brief.goals?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Goals</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {meeting.pre_meeting_brief.goals.map((g: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700">{g}</li>
                    ))}
                  </ul>
                </div>
              )}
              {meeting.pre_meeting_brief.pending_items?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Pending Items</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {meeting.pre_meeting_brief.pending_items.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700">{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {meeting.pre_meeting_brief.decision_questions?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Decision Questions</h3>
                  <ul className="list-disc list-inside space-y-1">
                    {meeting.pre_meeting_brief.decision_questions.map((q: string, i: number) => (
                      <li key={i} className="text-sm text-gray-700">{q}</li>
                    ))}
                  </ul>
                </div>
              )}
              {meeting.pre_meeting_brief.suggested_agenda?.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Suggested Agenda</h3>
                  <div className="space-y-2">
                    {meeting.pre_meeting_brief.suggested_agenda.map((item: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                        <span className="text-xs font-mono text-gray-500 w-10">{item.duration_minutes}m</span>
                        <span className="text-sm text-gray-800">{item.topic}</span>
                        {item.owner && <span className="text-xs text-gray-400 ml-auto">{item.owner}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-10 text-gray-400">
              <p>No pre-meeting brief generated yet.</p>
              <button
                onClick={handlePrepare}
                className="mt-3 px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
              >
                Generate Brief
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === "notes" && <NotesPanel notes={notes} />}
      {activeTab === "tasks" && (
        <ActionItemsPanel
          tasks={tasks}
          meetingId={meeting.id}
          onUpdate={loadData}
        />
      )}
      {activeTab === "risks" && <RiskPanel risks={risks} />}
    </div>
  );
}
