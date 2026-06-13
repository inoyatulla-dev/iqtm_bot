export type Role = "boss" | "worker";
export type UserStatus = "active" | "pending" | "blocked";
export type TaskType = "standalone" | "personal" | "project";

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

export interface Task {
  id: number;
  name: string;
  description: string | null;
  dep_id: string | null;
  masul_id: number | null;
  masul_name?: string | null;
  masul_photo?: string | null;
  created_by: number;
  deadline: string | null;
  status: string;
  type: TaskType;
  project_id: number | null;
  is_overdue: boolean;
  attachments_count: number;
  created_at?: string;
}

export interface Comment {
  id: number;
  task_id: number;
  user_id: number;
  user_name: string;
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

export interface StatusCounts {
  counts: Record<string, number>;
  overdue: number;
  total: number;
}

export interface RatingRow {
  user_id: number;
  name: string;
  done: number;
  active: number;
  overdue: number;
}

// ── UI yorliqlari ──────────────────────────────────────
export const ROLE_LABEL: Record<Role, string> = {
  boss: "Admin",
  worker: "Xodim",
};
