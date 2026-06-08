import axios from "axios";
import { getInitData } from "../telegram";
import type {
  Department, RatingRow, StatusCounts, Task, TaskStatus, User,
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

// ── Tasks ──────────────────────────────────────────────
export const tasksApi = {
  list: () => api.get<Task[]>("/tasks").then((r) => r.data),
  create: (body: Partial<Task>) =>
    api.post<Task>("/tasks", body).then((r) => r.data),
  update: (id: number, body: Partial<Task>) =>
    api.patch<Task>(`/tasks/${id}`, body).then((r) => r.data),
  setStatus: (id: number, status: TaskStatus) =>
    api.patch<Task>(`/tasks/${id}/status`, { status }).then((r) => r.data),
  remove: (id: number) => api.delete(`/tasks/${id}`),
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
  topic_tasks: string;
  topic_reports: string;
}

export const settingsApi = {
  get: () => api.get<AppSettings>("/settings").then((r) => r.data),
  update: (body: Partial<AppSettings>) =>
    api.put<AppSettings>("/settings", body).then((r) => r.data),
};

// ── Stats ──────────────────────────────────────────────
export const statsApi = {
  me: () => api.get<StatusCounts>("/stats/me").then((r) => r.data),
  global: () => api.get<StatusCounts>("/stats/global").then((r) => r.data),
  rating: () => api.get<RatingRow[]>("/stats/rating").then((r) => r.data),
};
