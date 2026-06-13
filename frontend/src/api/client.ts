import axios from "axios";
import { getInitData } from "../telegram";
import type {
  Attachment, BoardColumn, Comment, DashboardData, Department, Project, ProjectDetail,
  ProjectTaskCreate, RatingRow, StatusCounts, Task, Topic, User,
} from "./types";

export const api = axios.create({ baseURL: "/api" });

let token: string | null = null;

export function setToken(t: string) {
  token = t;
}

api.interceptors.request.use((config) => {
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auth ───────────────────────────────────────────────
export async function authenticate(): Promise<{ token: string; user: User }> {
  const { data } = await api.post("/auth/telegram", {
    init_data: getInitData(),
  });
  setToken(data.token);
  return data;
}

export async function updateProfile(
  first_name: string, last_name: string, birthday?: string | null, custom_emoji?: string | null
): Promise<User> {
  const { data } = await api.post<User>("/auth/profile", {
    first_name, last_name, birthday, custom_emoji,
  });
  return data;
}

export async function uploadProfilePhoto(file: File): Promise<User> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<User>("/auth/photo", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function updateLang(lang: string): Promise<void> {
  await api.post("/auth/lang", { lang });
}

// ── Tasks ──────────────────────────────────────────────
export const tasksApi = {
  list: () => api.get<Task[]>("/tasks").then((r) => r.data),
  create: (body: Partial<Task>) =>
    api.post<Task>("/tasks", body).then((r) => r.data),
  update: (id: number, body: Partial<Task>) =>
    api.patch<Task>(`/tasks/${id}`, body).then((r) => r.data),
  setStatus: (id: number, status: string) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then((r) => r.data),
  remove: (id: number) => api.delete(`/tasks/${id}`),
};

// ── Izohlar ────────────────────────────────────────────
export const commentsApi = {
  list: (taskId: number) =>
    api.get<Comment[]>(`/tasks/${taskId}/comments`).then((r) => r.data),
  add: (taskId: number, text: string, targetUserId?: number | null, parentId?: number | null) =>
    api
      .post<Comment>(`/tasks/${taskId}/comments`, {
        text,
        target_user_id: targetUserId ?? null,
        parent_id: parentId ?? null,
      })
      .then((r) => r.data),
};

// ── Biriktirmalar ──────────────────────────────────────
export const attachmentsApi = {
  list: (taskId: number) =>
    api.get<Attachment[]>(`/tasks/${taskId}/attachments`).then((r) => r.data),
  upload: (taskId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<Attachment>(`/tasks/${taskId}/attachments`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  remove: (taskId: number, attachmentId: number) =>
    api.delete(`/tasks/${taskId}/attachments/${attachmentId}`),
  download: (taskId: number, attachmentId: number) =>
    api
      .get(`/tasks/${taskId}/attachments/${attachmentId}/download`, { responseType: "blob" })
      .then((r) => r.data as Blob),
};

// ── Doska ustunlari ────────────────────────────────────
export const boardColumnsApi = {
  list: () => api.get<BoardColumn[]>("/board-columns").then((r) => r.data),
  create: (body: Partial<BoardColumn>) =>
    api.post<BoardColumn>("/board-columns", body).then((r) => r.data),
  update: (key: string, body: Partial<BoardColumn>) =>
    api.patch<BoardColumn>(`/board-columns/${key}`, body).then((r) => r.data),
  makeInitial: (key: string) =>
    api.post<BoardColumn>(`/board-columns/${key}/make-initial`).then((r) => r.data),
  reorder: (keys: string[]) =>
    api.put<BoardColumn[]>("/board-columns/reorder", { keys }).then((r) => r.data),
  remove: (key: string) => api.delete(`/board-columns/${key}`),
};

// ── Users ──────────────────────────────────────────────
export const usersApi = {
  list: (statusFilter?: string) =>
    api
      .get<User[]>("/users", { params: { status_filter: statusFilter } })
      .then((r) => r.data),
  create: (body: Partial<User>) =>
    api.post<User>("/users", body).then((r) => r.data),
  update: (id: number, body: Partial<User>) =>
    api.patch<User>(`/users/${id}`, body).then((r) => r.data),
  approve: (id: number, role: string, depId?: string) =>
    api
      .post<User>(`/users/${id}/approve`, null, {
        params: { role, dep_id: depId },
      })
      .then((r) => r.data),
  remove: (id: number) => api.delete(`/users/${id}`),
};

// ── Departments ────────────────────────────────────────
export const depsApi = {
  list: () => api.get<Department[]>("/departments").then((r) => r.data),
  create: (body: Partial<Department>) =>
    api.post<Department>("/departments", body).then((r) => r.data),
  update: (id: string, body: Partial<Department>) =>
    api.patch<Department>(`/departments/${id}`, body).then((r) => r.data),
  remove: (id: string) => api.delete(`/departments/${id}`),
};

// ── Settings ───────────────────────────────────────────
export interface AppSettings {
  group_chat_id: string;
  routes: Record<string, number | null>;
  templates: Record<string, string>;
  max_file_mb: number;
  storage_limit_gb: number;
  archive_channel_id: string;
  logo_path: string;
  logo_size: number;
}

export interface Branding {
  logo_path: string;
  logo_size: number;
}

export const brandingApi = {
  get: () => api.get<Branding>("/settings/branding").then((r) => r.data),
};

export const settingsApi = {
  get: () => api.get<AppSettings>("/settings").then((r) => r.data),
  update: (body: Partial<AppSettings>) =>
    api.put<AppSettings>("/settings", body).then((r) => r.data),
  uploadLogo: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<AppSettings>("/settings/logo", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};

// ── Topics (bildirishnoma mavzulari) ───────────────────
export const topicsApi = {
  list: () => api.get<Topic[]>("/topics").then((r) => r.data),
  create: (body: { name: string; topic_id: number }) =>
    api.post<Topic>("/topics", body).then((r) => r.data),
  update: (id: number, body: Partial<{ name: string; topic_id: number }>) =>
    api.patch<Topic>(`/topics/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/topics/${id}`),
};

// ── Stats ──────────────────────────────────────────────
export const statsApi = {
  me: (period?: string) => api.get<StatusCounts>("/stats/me", { params: { period } }).then((r) => r.data),
  global: (period?: string) => api.get<StatusCounts>("/stats/global", { params: { period } }).then((r) => r.data),
  rating: (period?: string) => api.get<RatingRow[]>("/stats/rating", { params: { period } }).then((r) => r.data),
  dashboard: (period?: string) =>
    api.get<DashboardData>("/stats/dashboard", { params: { period } }).then((r) => r.data),
};

// ── Loyihalar ──────────────────────────────────────────
export const projectsApi = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  get: (id: number) => api.get<ProjectDetail>(`/projects/${id}`).then((r) => r.data),
  create: (body: { name: string; description?: string | null; deadline?: string | null; tasks: ProjectTaskCreate[] }) =>
    api.post<ProjectDetail>("/projects", body).then((r) => r.data),
  update: (id: number, body: Partial<Project>) =>
    api.patch<Project>(`/projects/${id}`, body).then((r) => r.data),
  remove: (id: number) => api.delete(`/projects/${id}`),
};

// ── Hisobotlar ─────────────────────────────────────────
export type ReportPeriod = "week" | "month" | "year";
export type ReportFormat = "pdf" | "docx";

export const reportsApi = {
  download: (period: ReportPeriod, fmt: ReportFormat) =>
    api.get(`/reports/${period}.${fmt}`, { responseType: "blob" }).then((r) => r.data as Blob),
  send: (period: ReportPeriod, fmt: ReportFormat) =>
    api.post(`/reports/send/${period}.${fmt}`).then((r) => r.data as { ok: boolean }),
};
