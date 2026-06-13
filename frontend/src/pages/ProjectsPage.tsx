import { useEffect, useState, type CSSProperties } from "react";
import { projectsApi, usersApi } from "../api/client";
import type { ProjectDetail, ProjectTaskCreate, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet } from "../components/Sheet";

export function ProjectsPage() {
  const { isBoss, columns } = useAuth();
  const { t } = useI18n();
  const [projects, setProjects] = useState<ProjectDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [works, setWorks] = useState<ProjectTaskCreate[]>([{ name: "", masul_id: null }]);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

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

  function openCreate() {
    setName("");
    setDescription("");
    setWorks([{ name: "", masul_id: null }]);
    if (isBoss && users.length === 0) {
      usersApi.list().then(setUsers);
    }
    setCreating(true);
  }

  async function submit() {
    if (!name.trim()) return;
    try {
      await projectsApi.create({
        name: name.trim(),
        description: description.trim() || null,
        tasks: works.filter((w) => w.name.trim()),
      });
      setCreating(false);
      load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    }
  }

  async function remove(id: number) {
    try {
      await projectsApi.remove(id);
      setConfirmDeleteId(null);
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
          <div className="card project-card" key={p.id}>
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
            {p.tasks.length > 0 && (
              <div className="project-tasks">
                {p.tasks.map((task) => {
                  const col = columns.find((c) => c.key === task.status);
                  const icon = col?.emoji || "🆕";
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
                    <div className="project-task" key={task.id}>
                      <span className={cls} style={style}>{icon}</span>
                      {task.name}
                      <span className="project-task__assignee">
                        {task.masul_name || t("projects.unassigned")}
                        {task.is_overdue ? ` · ${t("monitoring.dist.overdue").toLowerCase()}` : ""}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
            {isBoss &&
              (confirmDeleteId === p.id ? (
                <button className="btn btn--danger" onClick={() => remove(p.id)}>
                  {t("projects.deleteConfirm")}
                </button>
              ) : (
                <button className="btn btn--ghost" onClick={() => setConfirmDeleteId(p.id)}>
                  {t("projects.delete")}
                </button>
              ))}
          </div>
        ))}
      </div>

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
    </div>
  );
}
