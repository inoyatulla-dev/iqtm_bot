import { useEffect, useState } from "react";
import {
  Button, Input, Textarea, Select, Section,
} from "@telegram-apps/telegram-ui";
import { tasksApi, usersApi } from "../api/client";
import type { Task, User } from "../api/types";
import { useAuth } from "../store/auth";

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
  const [masulId, setMasulId] = useState<string>(
    task?.masul_id ? String(task.masul_id) : ""
  );
  const [deadline, setDeadline] = useState(task?.deadline || "");
  const [workers, setWorkers] = useState<User[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isBoss) usersApi.list("active").then(setWorkers);
  }, [isBoss]);

  async function save() {
    if (name.trim().length < 3) {
      alert("Nom kamida 3 harf bo'lsin");
      return;
    }
    setSaving(true);
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
        // Xodim — shaxsiy vazifa
        body.type = "personal";
        await tasksApi.create(body);
      }
      onSaved();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  async function remove() {
    if (!task || !confirm("Vazifa o'chirilsinmi?")) return;
    await tasksApi.remove(task.id);
    onSaved();
  }

  const canEdit = !task || isBoss || task.created_by === user?.id;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <Section header={task ? `Vazifa #${task.id}` : "Yangi vazifa"}>
          <Input
            header="Nomi"
            placeholder="Vazifa nomi"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={!canEdit}
          />
          <Textarea
            header="Tavsif"
            placeholder="Ixtiyoriy"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            disabled={!canEdit}
          />
          {isBoss && (
            <>
              <Select
                header="Bo'lim"
                value={depId}
                onChange={(e) => setDepId(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {deps.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.emoji} {d.name}
                  </option>
                ))}
              </Select>
              <Select
                header="Mas'ul xodim"
                value={masulId}
                onChange={(e) => setMasulId(e.target.value)}
              >
                <option value="">— tanlanmagan —</option>
                {workers.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name}
                  </option>
                ))}
              </Select>
            </>
          )}
          <Input
            header="Muddat"
            type="date"
            value={deadline}
            onChange={(e) => setDeadline(e.target.value)}
            disabled={!canEdit}
          />
        </Section>

        <div style={{ display: "flex", gap: 8, padding: "0 16px 16px" }}>
          <Button stretched onClick={onClose} mode="outline">
            Yopish
          </Button>
          {canEdit && (
            <Button stretched onClick={save} loading={saving}>
              Saqlash
            </Button>
          )}
        </div>
        {task && canEdit && (
          <div style={{ padding: "0 16px 16px" }}>
            <Button stretched mode="outline" onClick={remove}>
              🗑 O'chirish
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
