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
}

export interface Task {
  id: number;
  name: string;
  description: string | null;
  dep_id: string | null;
  masul_id: number | null;
  created_by: number;
  deadline: string | null;
  status: string;
  type: TaskType;
  project_id: number | null;
  is_overdue: boolean;
  created_at?: string;
}

export interface Comment {
  id: number;
  task_id: number;
  user_id: number;
  user_name: string;
  text: string;
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
