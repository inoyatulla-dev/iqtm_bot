export type Role = "boss" | "worker" | "observer";
export type UserStatus = "active" | "pending" | "blocked";
export type TaskType = "standalone" | "personal" | "project";
export type ProjectStatus = "active" | "done";

export interface User {
  id: number;
  name: string;
  username: string | null;
  role: Role;
  dep_id: string | null;
  status: UserStatus;
  lang?: string;
  photo?: string | null;
  birthday?: string | null;
  birthday_in_days?: number | null;
  custom_emoji?: string | null;
  login?: string | null;
  created_at?: string;
}

export interface Department {
  id: string;
  name: string;
  emoji: string;
  color: string;
  topic_id: number | null;
}

export interface BoardColumn {
  id: number;
  key: string;
  name: string;
  emoji: string;
  color: string;
  seq: number;
  is_initial: boolean;
  is_done: boolean;
  notify: boolean;
}

export interface Assignee {
  id: number;
  name: string;
  photo?: string | null;
  emoji?: string | null;
}

export interface Task {
  id: number;
  name: string;
  description: string | null;
  dep_id: string | null;
  masul_id: number | null;
  masul_name?: string | null;
  masul_photo?: string | null;
  masul_emoji?: string | null;
  assignees?: Assignee[];
  /** Faqat yuborish uchun (create/update body) */
  assignee_ids?: number[];
  created_by: number;
  deadline: string | null;
  status: string;
  type: TaskType;
  project_id: number | null;
  project_name?: string | null;
  is_overdue: boolean;
  is_archived?: boolean;
  attachments_count: number;
  comments_count?: number;
  created_at?: string;
  updated_at?: string;
  done_at?: string | null;
  progress: number;
}

export interface Comment {
  id: number;
  task_id: number;
  user_id: number;
  user_name: string;
  user_photo?: string | null;
  text: string;
  target_user_id?: number | null;
  target_name?: string | null;
  parent_id?: number | null;
  reply_to?: string | null;
  created_at?: string;
}

export interface Attachment {
  id: number;
  task_id: number;
  uploaded_by: number;
  uploader_name?: string | null;
  file_name: string;
  mime_type: string | null;
  size: number;
  url: string | null;
  created_at?: string;
}

export interface Topic {
  id: number;
  name: string;
  topic_id: number;
}

export interface AppNotification {
  id: number;
  type: string;
  task_id: number | null;
  task_name?: string | null;
  text: string;
  is_read: boolean;
  is_archived: boolean;
  created_at: string;
}

export interface StatusCounts {
  counts: Record<string, number>;
  overdue: number;
  total: number;
  done_in_period: number;
}

export interface RatingRow {
  user_id: number;
  name: string;
  done: number;
  active: number;
  overdue: number;
  done_in_period: number;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  status: ProjectStatus;
  created_by: number;
  created_at?: string | null;
  deadline?: string | null;
  task_count: number;
  done_count: number;
  percent: number;
}

export interface ProjectDetail extends Project {
  tasks: Task[];
}

export interface ProjectTaskCreate {
  name: string;
  masul_id?: number | null;
  dep_id?: string | null;
}

export interface DeptProgress {
  dep_id: string;
  name: string;
  emoji: string;
  color: string;
  total: number;
  done: number;
  percent: number;
}

export interface DistributionSlice {
  key: string;
  label: string;
  color: string;
  percent: number;
}

export interface DashboardData {
  total: number;
  done: number;
  in_progress: number;
  overdue: number;
  new_in_period: number;
  closed_in_period: number;
  departments: DeptProgress[];
  distribution: DistributionSlice[];
}

// ── UI yorliqlari ──────────────────────────────────────
export const ROLE_LABEL: Record<Role, string> = {
  boss: "Admin",
  worker: "Xodim",
  observer: "Kuzatuvchi",
};

// ── Profil emoji tanlovi ────────────────────────────────
export const PROFILE_EMOJI_OPTIONS = ["🚀", "🎯", "⚡", "🎨", "📊", "🧠", "🔥", "🌟"];
