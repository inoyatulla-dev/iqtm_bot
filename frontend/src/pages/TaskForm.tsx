import { useEffect, useState } from "react";
import { tasksApi, usersApi } from "../api/client";
import type { Task, User } from "../api/types";
import { useAuth } from "../store/auth";
import { Sheet } from "../components/Sheet";

interface Props {
  task: Task | null; // null = yangi
  isBoss: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function TaskForm({ task, isBoss, onClose, onSaved }: Props) {
  const { deps, user } = useAuth();
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
      setErr("Nom kamida 3 harf bo'lsin");
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
    <Sheet title={task ? `Vazifa #${task.id}` : "Yangi vazifa"} onClose={onClose}>
      <div className="sheet__pad">
        <div className="field">
          <label>Nomi</label>
          <input
            value={name}
            placeholder="Vazifa nomi"
            disabled={!canEdit}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div className="field">
          <label>Tavsif</label>
          <textarea
            value={desc}
            placeholder="Ixtiyoriy"
            disabled={!canEdit}
            onChange={(e) => setDesc(e.target.value)}
          />
        </div>
        {isBoss && (
          <>
            <div className="field">
              <label>Bo'lim</label>
              <select value={depId} onChange={(e) => setDepId(e.target.value)}>
                <option value="">— tanlanmagan —</option>
                {deps.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.emoji} {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Mas'ul xodim</label>
              <select value={masulId} onChange={(e) => setMasulId(e.target.value)}>
                <option value="">— tanlanmagan —</option>
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
          <label>Muddat</label>
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
            {saving ? "Saqlanmoqda…" : "Saqlash"}
          </button>
        )}
        {task && canEdit && !confirmDel && (
          <button className="btn btn--danger" onClick={() => setConfirmDel(true)}>
            🗑 O'chirish
          </button>
        )}
        {confirmDel && (
          <button className="btn btn--danger" onClick={remove}>
            🗑 Rostdan o'chirilsinmi? (bosing)
          </button>
        )}
        <button className="btn btn--ghost" onClick={onClose}>
          Yopish
        </button>
      </div>
    </Sheet>
  );
}
