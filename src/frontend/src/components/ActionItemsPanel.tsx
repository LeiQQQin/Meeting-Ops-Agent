import React, { useState } from "react";
import { ActionItem, tasksApi } from "../api/client";
import StatusBadge from "./StatusBadge";

interface Props {
  tasks: ActionItem[];
  meetingId: string;
  onUpdate: () => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: "text-red-600",
  medium: "text-yellow-600",
  low: "text-green-600",
};

export default function ActionItemsPanel({ tasks, meetingId, onUpdate }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<ActionItem>>({});
  const [saving, setSaving] = useState(false);

  const startEdit = (task: ActionItem) => {
    setEditingId(task.id);
    setEditForm({
      title: task.title,
      owner: task.owner,
      due_date: task.due_date,
      status: task.status,
      acceptance_criteria: task.acceptance_criteria,
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({});
  };

  const saveEdit = async (taskId: string) => {
    setSaving(true);
    try {
      await tasksApi.update(meetingId, taskId, editForm);
      onUpdate();
      setEditingId(null);
    } catch {
    } finally {
      setSaving(false);
    }
  };

  if (tasks.length === 0)
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center text-gray-400">
        No action items yet. Upload a meeting transcript to generate them.
      </div>
    );

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div
          key={task.id}
          className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
        >
          {editingId === task.id ? (
            <div className="space-y-3">
              <input
                className="w-full border rounded px-2 py-1 text-sm"
                value={editForm.title}
                onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
              />
              <div className="grid grid-cols-2 gap-2">
                <input
                  className="border rounded px-2 py-1 text-sm"
                  placeholder="Owner"
                  value={editForm.owner || ""}
                  onChange={(e) => setEditForm({ ...editForm, owner: e.target.value })}
                />
                <input
                  className="border rounded px-2 py-1 text-sm"
                  type="date"
                  value={editForm.due_date ? editForm.due_date.split("T")[0] : ""}
                  onChange={(e) => setEditForm({ ...editForm, due_date: e.target.value })}
                />
              </div>
              <select
                className="border rounded px-2 py-1 text-sm w-full"
                value={editForm.status}
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
              >
                {["todo", "in_progress", "blocked", "done"].map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <textarea
                className="w-full border rounded px-2 py-1 text-sm"
                rows={2}
                placeholder="Acceptance criteria"
                value={editForm.acceptance_criteria || ""}
                onChange={(e) => setEditForm({ ...editForm, acceptance_criteria: e.target.value })}
              />
              <div className="flex gap-2">
                <button
                  onClick={() => saveEdit(task.id)}
                  disabled={saving}
                  className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Saving…" : "Save"}
                </button>
                <button
                  onClick={cancelEdit}
                  className="px-3 py-1 bg-gray-100 text-gray-700 text-xs rounded hover:bg-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 text-sm">{task.title}</h3>
                  {task.description && (
                    <p className="text-xs text-gray-500 mt-1">{task.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-2 ml-3">
                  <StatusBadge status={task.status} />
                  <button
                    onClick={() => startEdit(task)}
                    className="text-xs text-gray-400 hover:text-gray-600"
                  >
                    Edit
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-500">
                {task.owner && (
                  <span>👤 {task.owner}</span>
                )}
                {task.due_date && (
                  <span>📅 {new Date(task.due_date).toLocaleDateString()}</span>
                )}
                {task.priority && (
                  <span className={PRIORITY_COLORS[task.priority] || ""}>
                    ● {task.priority}
                  </span>
                )}
                {task.external_url && (
                  <a
                    href={task.external_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    🔗 View in {task.external_url.includes("github") ? "GitHub" : "task system"}
                  </a>
                )}
              </div>
              {task.acceptance_criteria && (
                <div className="mt-2 text-xs text-gray-600 bg-gray-50 rounded p-2">
                  <span className="font-medium">Acceptance criteria:</span> {task.acceptance_criteria}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
