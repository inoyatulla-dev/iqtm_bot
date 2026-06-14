import { useEffect, useState, type CSSProperties } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { projectsApi, tasksApi, usersApi } from "../api/client";
import type { ProjectDetail, ProjectStatus, ProjectTaskCreate, Task, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet, ActionRow } from "../components/Sheet";
import { TaskForm } from "./TaskForm";
import { formatCountdown, formatDeadlineDate } from "../utils/deadline";
import { EmojiIcon } from "../utils/emojiIcon";

export function ProjectsPage() {
  const { isBoss, isObserver, columns } = useAuth();
  const { t, lang } = useI18n();
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [deadline, setDeadline] = useState("");
  const [works, setWorks] = useState<ProjectTaskCreate[]>([{ name: "", masul_id: null }]);

  const [selId, setSelId] = useState<number | null>(null);
  const [view, setView] = useState<"detail" | "edit" | "addTask" | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editStatus, setEditStatus] = useState<ProjectStatus>("active");
  const [editDeadline, setEditDeadline] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  const [taskName, setTaskName] = useState("");
  const [taskMasul, setTaskMasul] = useState<number | "">("");
  const [taskSaving, setTaskSaving] = useState(false);

  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [taskFormOpen, setTaskFormOpen] = useState(false);

  const sel = projects.find((p) => p.id === selId) || null;

  async function load() {
    setLoading(true);
    const list = await projectsApi.list();
    const details = await Promise.all(list.map((p) => projectsApi.get(p.id)));
    setProjects(details);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  function ensureUsers() {
    if (isBoss && users.length === 0) {
      usersApi.list().then(setUsers);
    }
  }

  function openCreate() {
    setName("");
    setDescription("");
    setDeadline("");
    setWorks([{ name: "", masul_id: null }]);
    ensureUsers();
    setCreating(true);
  }

  async function submit() {
    if (!name.trim()) return;
    try {
      await projectsApi.create({
        name: name.trim(),
        description: description.trim() || null,
        deadline: deadline || null,
        tasks: works.filter((w) => w.name.trim()),
      });
      setCreating(false);
      load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    }
  }

  function openDetail(p: ProjectDetail) {
    setSelId(p.id);
    setView("detail");
    setConfirmDelete(false);
    ensureUsers();
  }

  function openEdit(p: ProjectDetail) {
    setEditName(p.name);
    setEditDesc(p.description || "");
    setEditStatus(p.status);
    setEditDeadline(p.deadline ? p.deadline.slice(0, 10) : "");
    setView("edit");
  }

  async function saveEdit() {
    if (!sel) return;
    setEditSaving(true);
    try {
      await projectsApi.update(sel.id, {
        name: editName.trim(),
        description: editDesc.trim() || null,
        status: editStatus,
        deadline: editDeadline || null,
      });
      await load();
      setView("detail");
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    } finally {
      setEditSaving(false);
    }
  }

  function openAddTask() {
    setTaskName("");
    setTaskMasul("");
    setView("addTask");
  }

  async function submitAddTask() {
    if (!sel || !taskName.trim()) return;
    setTaskSaving(true);
    try {
      await tasksApi.create({
        name: taskName.trim(),
        masul_id: taskMasul === "" ? null : taskMasul,
        type: "standalone",
        project_id: sel.id,
      });
      await load();
      setView("detail");
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    } finally {
      setTaskSaving(false);
    }
  }

  async function remove() {
    if (!sel) return;
    try {
      await projectsApi.remove(sel.id);
      setView(null);
      setSelId(null);
      load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    }
  }

  function progressColor(percent: number) {
    if (percent >= 100) return "var(--ok)";
    if (percent > 0) return "var(--accent)";
    return "var(--warn)";
  }

  function renderTasks(tasks: ProjectDetail["tasks"]) {
    return (
      <div className="project-tasks" style={{ marginTop: 12 }}>
        {tasks.map((task) => {
          const col = columns.find((c) => c.key === task.status);
          let cls = "badge badge--accent";
          let style: CSSProperties | undefined;
          if (task.is_overdue) {
            cls = "badge badge--danger";
          } else if (col?.is_done) {
            cls = "badge badge--ok";
          } else if (col?.is_initial) {
            cls = "badge";
            style = { background: "var(--surface)", color: "var(--hint)" };
          }
          return (
            <div
              className="project-task"
              key={task.id}
              style={{ cursor: "pointer" }}
              onClick={() => { setEditingTask(task); setTaskFormOpen(true); }}
            >
              <span className={cls} style={style}><EmojiIcon emoji={col?.emoji} size={12} /></span>
              {task.name}
              <span className="project-task__assignee">
                {task.masul_name || t("projects.unassigned")}
                {task.is_overdue ? ` · ${t("monitoring.dist.overdue").toLowerCase()}` : ""}
              </span>
            </div>
          );
        })}
      </div>
    );
  }

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

  return (
    <div className="page-content">
      {isBoss && (
        <div className="toolbar">
          <div />
          <button className="btn btn--primary" style={{ width: "auto" }} onClick={openCreate}>
            {t("projects.new")}
          </button>
        </div>
      )}

      {projects.length === 0 && <div className="empty-state">{t("projects.empty")}</div>}

      <div className="project-grid">
        {projects.map((p) => (
          <div className="card project-card" key={p.id} style={{ cursor: "pointer" }} onClick={() => openDetail(p)}>
            <div className="project-card__head">
              <div className="project-card__name">{p.name}</div>
              <span className={`badge ${p.status === "done" ? "badge--accent" : "badge--ok"}`}>
                {t(`projects.status.${p.status}`)}
              </span>
            </div>
            <div className="dept-row__head">
              <div className="dept-row__count">
                {t("projects.progress")
                  .replace("{done}", String(p.done_count))
                  .replace("{total}", String(p.task_count))}
              </div>
              <div className="dept-row__count">{p.percent}%</div>
            </div>
            <div className="progress-bar">
              <div
                className="progress-bar__fill"
                style={{ width: `${p.percent}%`, background: progressColor(p.percent) }}
              />
            </div>
            {p.deadline && (
              <div className="project-task__assignee" style={{ marginTop: 6 }}>
                {t("task.deadline")}: {formatDeadlineDate(p.deadline)} · {formatCountdown(p.deadline, lang)}
              </div>
            )}
          </div>
        ))}
      </div>

      {sel && view === "detail" && (
        <Sheet
          title={sel.name}
          subtitle={t(`projects.status.${sel.status}`)}
          onClose={() => { setView(null); setSelId(null); }}
        >
          <div className="sheet__pad">
            {sel.description && (
              <p style={{ marginTop: 0, color: "var(--hint)" }}>{sel.description}</p>
            )}
            {sel.deadline && (
              <p style={{ marginTop: 0, color: "var(--hint)" }}>
                {t("task.deadline")}: {formatDeadlineDate(sel.deadline)} · {formatCountdown(sel.deadline, lang)}
              </p>
            )}
            <div className="dept-row__head">
              <div className="dept-row__count">
                {t("projects.progress")
                  .replace("{done}", String(sel.done_count))
                  .replace("{total}", String(sel.task_count))}
              </div>
              <div className="dept-row__count">{sel.percent}%</div>
            </div>
            <div className="progress-bar">
              <div
                className="progress-bar__fill"
                style={{ width: `${sel.percent}%`, background: progressColor(sel.percent) }}
              />
            </div>
            {sel.tasks.length > 0 ? renderTasks(sel.tasks) : (
              <div className="empty-state">{t("monitoring.noTasks")}</div>
            )}
          </div>
          {isBoss && (
            <>
              <ActionRow icon={<Pencil size={20} />} label={t("projects.edit")} onClick={() => openEdit(sel)} />
              <ActionRow icon={<Plus size={20} />} label={t("projects.addTask")} onClick={openAddTask} />
              {confirmDelete ? (
                <div className="sheet__pad">
                  <button className="btn btn--danger" onClick={remove}>
                    {t("projects.deleteConfirm")}
                  </button>
                </div>
              ) : (
                <ActionRow icon={<Trash2 size={20} />} label={t("projects.delete")} danger onClick={() => setConfirmDelete(true)} />
              )}
            </>
          )}
        </Sheet>
      )}

      {sel && view === "edit" && (
        <Sheet title={t("projects.editTitle")} subtitle={sel.name} onClose={() => setView("detail")}>
          <div className="sheet__pad">
            <div className="field">
              <label>{t("projects.name")}</label>
              <input value={editName} onChange={(e) => setEditName(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("projects.description")}</label>
              <textarea value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("projects.statusLabel")}</label>
              <select value={editStatus} onChange={(e) => setEditStatus(e.target.value as ProjectStatus)}>
                <option value="active">{t("projects.status.active")}</option>
                <option value="done">{t("projects.status.done")}</option>
              </select>
            </div>
            <div className="field">
              <label>{t("task.deadline")}</label>
              <input type="date" value={editDeadline} onChange={(e) => setEditDeadline(e.target.value)} />
            </div>
            <button className="btn btn--primary" onClick={saveEdit} disabled={editSaving}>
              {editSaving ? t("task.saving") : t("common.save")}
            </button>
          </div>
        </Sheet>
      )}

      {sel && view === "addTask" && (
        <Sheet title={t("projects.addTaskTitle")} subtitle={sel.name} onClose={() => setView("detail")}>
          <div className="sheet__pad">
            <div className="field">
              <label>{t("projects.tasksLabel")}</label>
              <input
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
                placeholder={t("projects.taskNamePh")}
              />
            </div>
            <div className="field">
              <label>{t("task.masul")}</label>
              <select
                value={taskMasul}
                onChange={(e) => setTaskMasul(e.target.value ? Number(e.target.value) : "")}
              >
                <option value="">{t("projects.unassigned")}</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>{u.name}</option>
                ))}
              </select>
            </div>
            <button className="btn btn--primary" onClick={submitAddTask} disabled={taskSaving}>
              {taskSaving ? t("task.saving") : t("projects.addTask")}
            </button>
          </div>
        </Sheet>
      )}

      {creating && (
        <Sheet title={t("projects.newTitle")} onClose={() => setCreating(false)}>
          <div className="sheet__pad">
            <div className="field">
              <label>{t("projects.name")}</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder={t("projects.namePh")} />
            </div>
            <div className="field">
              <label>{t("projects.description")}</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={t("projects.descPh")}
              />
            </div>
            <div className="field">
              <label>{t("task.deadline")}</label>
              <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("projects.tasksLabel")}</label>
              {works.map((w, i) => (
                <div className="work-row" key={i}>
                  <input
                    placeholder={t("projects.taskNamePh")}
                    value={w.name}
                    onChange={(e) => {
                      const next = [...works];
                      next[i] = { ...next[i], name: e.target.value };
                      setWorks(next);
                    }}
                  />
                  <select
                    value={w.masul_id ?? ""}
                    onChange={(e) => {
                      const next = [...works];
                      next[i] = { ...next[i], masul_id: e.target.value ? Number(e.target.value) : null };
                      setWorks(next);
                    }}
                  >
                    <option value="">{t("projects.unassigned")}</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.name}
                      </option>
                    ))}
                  </select>
                  {works.length > 1 && (
                    <button
                      type="button"
                      className="work-row__remove"
                      onClick={() => setWorks(works.filter((_, idx) => idx !== i))}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => setWorks([...works, { name: "", masul_id: null }])}
              >
                {t("projects.addTask")}
              </button>
            </div>
            <button className="btn btn--primary" onClick={submit}>
              {t("projects.create")}
            </button>
          </div>
        </Sheet>
      )}

      {taskFormOpen && (
        <TaskForm
          key={editingTask?.id ?? "new"}
          task={editingTask}
          isBoss={isBoss}
          isObserver={isObserver}
          onClose={() => setTaskFormOpen(false)}
          onSaved={() => {
            setTaskFormOpen(false);
            setEditingTask(null);
            load();
          }}
          onStatusChanged={(updated) => setEditingTask(updated)}
        />
      )}
    </div>
  );
}
