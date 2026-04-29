import React from "react";

const STATUS_CONFIG: Record<string, { label: string; classes: string }> = {
  scheduled: { label: "Scheduled", classes: "bg-blue-100 text-blue-800" },
  in_progress: { label: "In Progress", classes: "bg-yellow-100 text-yellow-800" },
  completed: { label: "Completed", classes: "bg-green-100 text-green-800" },
  follow_up: { label: "Follow-up", classes: "bg-purple-100 text-purple-800" },
  closed: { label: "Closed", classes: "bg-gray-100 text-gray-600" },
  todo: { label: "To Do", classes: "bg-gray-100 text-gray-700" },
  in_progress_task: { label: "In Progress", classes: "bg-yellow-100 text-yellow-700" },
  blocked: { label: "Blocked", classes: "bg-red-100 text-red-700" },
  done: { label: "Done", classes: "bg-green-100 text-green-700" },
  overdue: { label: "Overdue", classes: "bg-red-100 text-red-800 font-semibold" },
};

export default function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    classes: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs ${config.classes} whitespace-nowrap`}>
      {config.label}
    </span>
  );
}
