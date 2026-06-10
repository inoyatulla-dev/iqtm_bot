import { useState } from "react";
import {
  DndContext, type DragEndEvent, PointerSensor, useSensor, useSensors,
} from "@dnd-kit/core";
import {
  SortableContext, useSortable, verticalListSortingStrategy, arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { boardColumnsApi } from "../api/client";
import type { BoardColumn } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet } from "./Sheet";

const EMOJIS = ["🆕", "🔄", "🔍", "✅", "⏸️", "🚀", "🧪", "📦", "🗂️", "⏳"];
const COLORS = ["#64748b", "#f59e0b", "#8b5cf6", "#10b981", "#3b82f6", "#ef4444", "#ec4899"];

export function BoardColumnsSection() {
  const { columns, reload } = useAuth();
  const { t } = useI18n();
  const [edit, setEdit] = useState<BoardColumn | null>(null);
  const [creating, setCreating] = useState(false);
  const [order, setOrder] = useState<BoardColumn[] | null>(null);

  const list = order ?? columns;
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } })
  );

  async function onDragEnd(e: DragEndEvent) {
    const { active, over } = e;
    if (!over || active.id === over.id) return;
    const oldIndex = list.findIndex((c) => c.key === active.id);
    const newIndex = list.findIndex((c) => c.key === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const next = arrayMove(list, oldIndex, newIndex);
    setOrder(next);
    try {
      await boardColumnsApi.reorder(next.map((c) => c.key));
    } catch {
      setOrder(null);
    } finally {
      await reload();
      setOrder(null);
    }
  }

  return (
    <>
      <div className="section-title">{t("boards.title")}</div>
      <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 16px 8px" }}>
        {t("boards.hint")}
      </p>
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <SortableContext items={list.map((c) => c.key)} strategy={verticalListSortingStrategy}>
          {list.map((col) => (
            <ColumnRow key={col.key} column={col} onClick={() => setEdit(col)} />
          ))}
        </SortableContext>
      </DndContext>

      <div className="sheet__pad">
        <button className="btn btn--primary" onClick={() => setCreating(true)}>
          {t("boards.add")}
        </button>
      </div>

      {creating && (
        <ColumnForm
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
      {edit && (
        <ColumnForm
          column={edit}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            reload();
          }}
        />
      )}
    </>
  );
}

function ColumnRow({ column, onClick }: { column: BoardColumn; onClick: () => void }) {
  const { t } = useI18n();
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: column.key,
  });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="col-row">
      <span className="col-row__handle" {...attributes} {...listeners}>
        ⠿
      </span>
      <span className="col-row__emoji">{column.emoji}</span>
      <div className="col-row__body" onClick={onClick}>
        <div className="col-row__title">
          {column.name}
          {column.is_initial && <span className="badge badge--ok">{t("boards.initialBadge")}</span>}
          {column.is_done && <span className="badge badge--danger">{t("boards.doneBadge")}</span>}
        </div>
        <div className="col-row__sub">{column.key}</div>
      </div>
      <span className="dep-dot" style={{ background: column.color, width: 14, height: 14 }} />
    </div>
  );
}

function ColumnForm({
  column,
  onClose,
  onSaved,
}: {
  column?: BoardColumn;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [key, setKey] = useState(column?.key || "");
  const [name, setName] = useState(column?.name || "");
  const [emoji, setEmoji] = useState(column?.emoji || EMOJIS[0]);
  const [color, setColor] = useState(column?.color || COLORS[0]);
  const [isDone, setIsDone] = useState(column?.is_done || false);
  const [notify, setNotify] = useState(column?.notify ?? true);
  const [confirmDel, setConfirmDel] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    if (!column && !/^[a-z0-9_]{2,20}$/.test(key)) {
      setErr(t("boards.keyErr"));
      return;
    }
    if (name.trim().length < 2) {
      setErr(t("boards.nameErr"));
      return;
    }
    try {
      if (column) {
        await boardColumnsApi.update(column.key, { name, emoji, color, is_done: isDone, notify });
      } else {
        await boardColumnsApi.create({ key, name, emoji, color, is_done: isDone, notify });
      }
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    }
  }

  async function remove() {
    if (!column) return;
    try {
      await boardColumnsApi.remove(column.key);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    }
  }

  async function makeInitial() {
    if (!column) return;
    try {
      await boardColumnsApi.makeInitial(column.key);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    }
  }

  return (
    <Sheet title={column ? t("boards.editTitle") : t("boards.newTitle")} onClose={onClose}>
      <div className="sheet__pad">
        {!column && (
          <div className="field">
            <label>{t("boards.key")}</label>
            <input value={key} onChange={(e) => setKey(e.target.value.toLowerCase())} />
          </div>
        )}
        <div className="field">
          <label>{t("boards.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("boards.emoji")}</label>
          <input
            value={emoji}
            maxLength={4}
            placeholder="📋"
            onChange={(e) => setEmoji(e.target.value)}
            style={{ fontSize: 22, width: 80, textAlign: "center" }}
          />
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6 }}>
            {EMOJIS.map((e) => (
              <button
                key={e}
                type="button"
                onClick={() => setEmoji(e)}
                style={{
                  fontSize: 18,
                  padding: 4,
                  borderRadius: 8,
                  border: "1px solid var(--line)",
                  background: "var(--secondary-bg)",
                  cursor: "pointer",
                }}
              >
                {e}
              </button>
            ))}
          </div>
        </div>
        <div className="field">
          <label>{t("boards.color")}</label>
          <div style={{ display: "flex", gap: 10 }}>
            {COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setColor(c)}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: c,
                  border: color === c ? "3px solid var(--text)" : "none",
                  cursor: "pointer",
                }}
              />
            ))}
          </div>
        </div>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
          <input
            type="checkbox"
            checked={isDone}
            onChange={(e) => setIsDone(e.target.checked)}
            style={{ width: "auto" }}
          />
          {t("boards.isDone")}
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
          <input
            type="checkbox"
            checked={notify}
            onChange={(e) => setNotify(e.target.checked)}
            style={{ width: "auto" }}
          />
          {t("boards.notify")}
        </label>

        {err && <div className="form-error">{err}</div>}

        <button className="btn btn--primary" onClick={save}>
          {t("common.save")}
        </button>
        {column && !column.is_initial && (
          <button className="btn btn--ghost" onClick={makeInitial}>
            {t("boards.makeInitial")}
          </button>
        )}
        {column && !confirmDel && (
          <button className="btn btn--danger" onClick={() => setConfirmDel(true)}>
            {t("common.delete")}
          </button>
        )}
        {confirmDel && (
          <button className="btn btn--danger" onClick={remove}>
            {t("boards.confirmDelete")}
          </button>
        )}
      </div>
    </Sheet>
  );
}
