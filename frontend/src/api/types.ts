export type Role = "boss" | "worker";
export type UserStatus = "active" | "pending" | "blocked";
export type TaskStatus = "new" | "in_progress" | "review" | "done";
export type TaskType = "standalone" | "personal" | "project";

export interface User {
  id: number;
  name: string;
  username: string | null;
  role: Role;
  dep_id: string | null;
  status: UserStatus;
  created_at?: string;
}

export interface Department {
  id: string;
  name: string;
  emoji: string;
  color: string;
  topic_id: number | null;
}

export interface Task {
  id: number;
  name: string;
  description: string | null;
  dep_id: string | null;
  masul_id: number | null;
  created_by: number;
  deadline: string | null;
  status: TaskStatus;
  type: TaskType;
  project_id: number | null;
  is_overdue: boolean;
  created_at?: string;
}

export interface StatusCounts {
  new: number;
  in_progress: number;
  review: number;
  done: number;
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
export const STATUS_LABEL: Record<TaskStatus, string> = {
  new: "Yangi",
  in_progress: "Jarayonda",
  review: "Tekshiruvda",
  done: "Bajarildi",
};

export const STATUS_EMOJI: Record<TaskStatus, string> = {
  new: "🆕",
  in_progress: "🔄",
  review: "🔍",
  done: "✅",
};

export const STATUS_ORDER: TaskStatus[] = ["new", "in_progress", "review", "done"];

export const ROLE_LABEL: Record<Role, string> = {
  boss: "Boshliq",
  worker: "Xodim",
};
