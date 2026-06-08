import { useEffect, useState } from "react";
import {
  DndContext, DragEndEvent, PointerSensor, useSensor, useSensors,
} from "@dnd-kit/core";
import { tasksApi } from "../api/client";
import type { Task } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { haptic } from "../telegram";
import { Column } from "../components/board/Column";
import { TaskCard } from "../components/board/TaskCard";
import { TaskForm } from "./TaskForm";

export function BoardPage() {
  const { deps, columns, isBoss } = useAuth();
  const { t } = useI18n();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  async function load() {
    setLoading(true);
    setTasks(await tasksApi.list());
    setLoading(false);
  }
  useEffect(() => {
    load();
  }, []);

  async function moveTask(taskId: number, newStatus: string) {
    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === newStatus) return;

    haptic();
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
    );
    try {
      const updated = await tasksApi.setStatus(taskId, newStatus);
      setTasks((prev) => prev.map((t) => (t.id === taskId ? updated : t)));
    } catch {
      load(); // xato bo'lsa — qayta yuklash
    }
  }

  async function onDragEnd(e: DragEndEvent) {
    const newStatus = e.over?.id as string | undefined;
    if (!newStatus) return;
    await moveTask(Number(e.active.id), newStatus);
  }

  if (loading) {
    return <div className="center-screen">{t("common.loading")}</div>;
  }

  return (
    <>
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <div className="board">
          {columns.map((col) => {
            const colTasks = tasks.filter((t) => t.status === col.key);
            return (
              <Column key={col.key} column={col} count={colTasks.length}>
                {colTasks.map((t) => (
                  <TaskCard
                    key={t.id}
                    task={t}
                    dep={deps.find((d) => d.id === t.dep_id)}
                    onClick={(task) => {
                      setEditing(task);
                      setFormOpen(true);
                    }}
                  />
                ))}
              </Column>
            );
          })}
        </div>
      </DndContext>

      <button
        className="fab"
        onClick={() => {
          setEditing(null);
          setFormOpen(true);
        }}
      >
        +
      </button>

      {formOpen && (
        <TaskForm
          task={editing}
          isBoss={isBoss}
          onClose={() => setFormOpen(false)}
          onSaved={() => {
            setFormOpen(false);
            load();
          }}
          onStatusChanged={(updated) => {
            setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
            setEditing(updated);
          }}
        />
      )}
    </>
  );
}
