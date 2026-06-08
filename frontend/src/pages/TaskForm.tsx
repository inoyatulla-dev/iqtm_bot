import { useEffect, useState } from "react";
import { tasksApi, usersApi } from "../api/client";
import type { Task, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet } from "../components/Sheet";

interface Props {
  task: Task | null; // null = yangi
  isBoss: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function TaskForm({ task, isBoss, onClose, onSaved }: Props) {
  const { deps, user } = useAuth();
  const { t } = useI18n();
  const [name, setName] = useState(task?.name || "");
  const [desc, setDesc] = useState(task?.description || "");
  const [depId, setDepId] = useState(task?.dep_id || "");
  const [masulId, setMasulId] = useState(task?.masul_id ? String(task.masul_id) : "");
  const [deadline, setDeadline] = useState(task?.deadline || "");
  const [workers, setWorkers] = useState<User[]>([]);
  const [saving, setSaving] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (isBoss) usersApi.list("active").then(setWorkers);
  }, [isBoss]);

  const canEdit = !task || isBoss || task.created_by === user?.id;

  async function save() {
    if (name.trim().length < 3) {
      setErr(t("task.nameErr"));
      return;
    }
    setSaving(true);
    setErr("");
    try {
      const body: Partial<Task> = {
        name: name.trim(),
        description: desc.trim() || null,
        deadline: deadline || null,
        dep_id: depId || null,
      };
      if (task) {
        body.masul_id = masulId ? Number(masulId) : null;
        await tasksApi.update(task.id, body);
      } else if (isBoss) {
        body.masul_id = masulId ? Number(masulId) : null;
        body.type = "standalone";
        await tasksApi.create(body);
      } else {
        body.type = "personal";
        await tasksApi.create(body);
      }
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!task) return;
    await tasksApi.remove(task.id);
    onSaved();
  }

  return (
    <Sheet title={task ? `#${task.id}` : t("task.new")} onClose={onClose}>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("task.name")}</label>
          <input
            value={name}
            placeholder={t("task.namePh")}
            disabled={!canEdit}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="field">
          <label>{t("task.desc")}</label>
          <textarea
            value={desc}
            placeholder={t("task.descPh")}
            disabled={!canEdit}
            onChange={(e) => setDesc(e.target.value)}
          />
        </div>
        {isBoss && (
          <>
            <div className="field">
              <label>{t("task.dept")}</label>
              <select value={depId} onChange={(e) => setDepId(e.target.value)}>
                <option value="">{t("task.unassigned")}</option>
                {deps.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.emoji} {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{t("task.masul")}</label>
              <select value={masulId} onChange={(e) => setMasulId(e.target.value)}>
                <option value="">{t("task.unassigned")}</option>
                {workers.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        <div className="field">
          <label>{t("task.deadline")}</label>
          <input
            type="date"
            value={deadline}
            disabled={!canEdit}
            onChange={(e) => setDeadline(e.target.value)}
          />
        </div>

        {err && <div className="form-error">{err}</div>}

        {canEdit && (
          <button className="btn btn--primary" onClick={save} disabled={saving}>
            {saving ? t("task.saving") : t("common.save")}
          </button>
        )}
        {task && canEdit && !confirmDel && (
          <button className="btn btn--danger" onClick={() => setConfirmDel(true)}>
            {t("task.delete")}
          </button>
        )}
        {confirmDel && (
          <button className="btn btn--danger" onClick={remove}>
            {t("task.confirmDelete")}
          </button>
        )}
        <button className="btn btn--ghost" onClick={onClose}>
          {t("common.close")}
        </button>
      </div>
    </Sheet>
  );
}
