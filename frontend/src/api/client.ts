import axios from "axios";
import { getInitData } from "../telegram";
import type {
  BoardColumn, Comment, Department, RatingRow, StatusCounts, Task, Topic, User,
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

export async function updateProfile(first_name: string, last_name: string): Promise<User> {
  const { data } = await api.post<User>("/auth/profile", { first_name, last_name });
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
}

export const settingsApi = {
  get: () => api.get<AppSettings>("/settings").then((r) => r.data),
  update: (body: Partial<AppSettings>) =>
    api.put<AppSettings>("/settings", body).then((r) => r.data),
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
  me: () => api.get<StatusCounts>("/stats/me").then((r) => r.data),
  global: () => api.get<StatusCounts>("/stats/global").then((r) => r.data),
  rating: () => api.get<RatingRow[]>("/stats/rating").then((r) => r.data),
};
