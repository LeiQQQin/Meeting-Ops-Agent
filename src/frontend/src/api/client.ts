import axios from "axios";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// --- Types ---
export interface Participant {
  name: string;
  email?: string;
  role?: string;
}

export interface Meeting {
  id: string;
  title: string;
  description?: string;
  status: string;
  scheduled_at?: string;
  participants: Participant[];
  project_tags: string[];
  connectors: string[];
  notes?: MeetingNotes;
  pre_meeting_brief?: PreMeetingBrief;
  created_at: string;
}

export interface MeetingNotes {
  decisions: string[];
  action_items: ActionItem[];
  risks: RiskItem[];
  discussion_points: string[];
  assumptions: string[];
  summary?: string;
}

export interface ActionItem {
  id: string;
  meeting_id: string;
  title: string;
  description?: string;
  owner?: string;
  due_date?: string;
  acceptance_criteria?: string;
  priority: string;
  status: string;
  external_url?: string;
}

export interface RiskItem {
  id: string;
  title: string;
  description?: string;
  severity: string;
  category: string;
  mitigation?: string;
  is_resolved: boolean;
}

export interface PreMeetingBrief {
  meeting_id: string;
  goals: string[];
  pending_items: string[];
  decision_questions: string[];
  suggested_agenda: { topic: string; duration_minutes: number; owner?: string }[];
  context_summary?: string;
}

// --- API calls ---

export const meetingsApi = {
  list: () => client.get<Meeting[]>("/meetings").then((r) => r.data),
  get: (id: string) => client.get<Meeting>(`/meetings/${id}`).then((r) => r.data),
  create: (data: Partial<Meeting>) =>
    client.post<Meeting>("/meetings", data).then((r) => r.data),
  prepare: (id: string) =>
    client.post<PreMeetingBrief>(`/meetings/${id}/prepare`).then((r) => r.data),
  uploadTranscript: (id: string, text: string, requireConfirmation = true) =>
    client
      .post(`/meetings/${id}/transcript`, null, {
        params: { transcript_text: text, require_confirmation: requireConfirmation },
      })
      .then((r) => r.data),
  uploadAudio: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return client
      .post(`/meetings/${id}/transcript`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  confirmTasks: (id: string) =>
    client.post(`/meetings/${id}/confirm-tasks`).then((r) => r.data),
  sendFollowup: (id: string) =>
    client.post(`/meetings/${id}/followup`).then((r) => r.data),
  getNotes: (id: string) =>
    client.get<MeetingNotes>(`/meetings/${id}/notes`).then((r) => r.data),
};

export const tasksApi = {
  list: (meetingId: string) =>
    client.get<ActionItem[]>(`/tasks/${meetingId}`).then((r) => r.data),
  update: (meetingId: string, taskId: string, data: Partial<ActionItem>) =>
    client.patch<ActionItem>(`/tasks/${meetingId}/${taskId}`, data).then((r) => r.data),
  risks: (meetingId: string) =>
    client.get<RiskItem[]>(`/tasks/${meetingId}/risks`).then((r) => r.data),
};

export const agentsApi = {
  list: () => client.get("/agents").then((r) => r.data),
  runRiskCheck: (meetingId: string) =>
    client.post(`/agents/${meetingId}/run-risk-check`).then((r) => r.data),
};

export default client;
