import { useEffect, useState } from "react";
import { commentsApi, tasksApi, usersApi } from "../api/client";
import type { BoardColumn, Comment, Task, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet, ActionRow } from "../components/Sheet";

interface Props {
  task: Task | null; // null = yangi
  isBoss: boolean;
  onClose: () => void;
  onSaved: () => void;
  onStatusChanged?: (task: Task) => void;
}

export function TaskForm({ task, isBoss, onClose, onSaved, onStatusChanged }: Props) {
  const { deps, columns, user } = useAuth();
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

  // ── Holat ──
  const [statusBusy, setStatusBusy] = useState(false);
  const [pendingDone, setPendingDone] = useState<BoardColumn | null>(null);
  const [doneComment, setDoneComment] = useState("");

  // ── Izohlar ──
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState("");
  const [commentBusy, setCommentBusy] = useState(false);
  const [commentTarget, setCommentTarget] = useState("");
  const [replyTo, setReplyTo] = useState<Comment | null>(null);

  useEffect(() => {
    if (isBoss) usersApi.list("active").then(setWorkers);
  }, [isBoss]);

  useEffect(() => {
    if (task) commentsApi.list(task.id).then(setComments);
  }, [task?.id]);

  const canEdit = !task || isBoss || task.created_by === user?.id;
  const canChangeStatus =
    !!task &&
    (isBoss ||
      task.masul_id === user?.id ||
      (task.type === "personal" && task.created_by === user?.id));
  const targetColumns = columns.filter((c) => isBoss || !c.is_done);

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

  async function changeStatus(col: BoardColumn) {
    if (!task || statusBusy || task.status === col.key) return;
    if (col.is_done) {
      setPendingDone(col);
      setDoneComment("");
      return;
    }
    setStatusBusy(true);
    setErr("");
    try {
      const updated = await tasksApi.setStatus(task.id, col.key);
      onStatusChanged?.(updated);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setStatusBusy(false);
    }
  }

  async function confirmDone() {
    if (!task || !pendingDone) return;
    setStatusBusy(true);
    setErr("");
    try {
      const text = doneComment.trim();
      if (text) {
        const c = await commentsApi.add(task.id, text);
        setComments((prev) => [...prev, c]);
      }
      const updated = await tasksApi.setStatus(task.id, pendingDone.key);
      onStatusChanged?.(updated);
      setPendingDone(null);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setStatusBusy(false);
    }
  }

  async function sendComment() {
    if (!task) return;
    const text = commentText.trim();
    if (!text) return;
    setCommentBusy(true);
    setErr("");
    try {
      const target = commentTarget
        ? Number(commentTarget)
        : replyTo
          ? replyTo.user_id
          : null;
      const c = await commentsApi.add(task.id, text, target, replyTo?.id ?? null);
      setComments((prev) => [...prev, c]);
      setCommentText("");
      setReplyTo(null);
      setCommentTarget("");
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setCommentBusy(false);
    }
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
      </div>

      {task && canChangeStatus && (
        <>
          <div className="section-title">{t("task.statusSection")}</div>
          <div style={{ borderTop: "1px solid var(--line)" }}>
            {targetColumns.map((col) => (
              <ActionRow
                key={col.key}
                icon={col.emoji}
                label={col.name}
                checked={task.status === col.key}
                onClick={() => changeStatus(col)}
              />
            ))}
          </div>
          {pendingDone && (
            <div className="sheet__pad">
              <div style={{ fontWeight: 600 }}>{t("task.confirmDoneTitle")}</div>
              <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>
                {t("task.confirmDoneHint")}
              </p>
              <textarea
                value={doneComment}
                placeholder={t("comment.placeholder")}
                onChange={(e) => setDoneComment(e.target.value)}
              />
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="btn btn--ghost"
                  onClick={() => setPendingDone(null)}
                  disabled={statusBusy}
                >
                  {t("common.cancel")}
                </button>
                <button className="btn btn--primary" onClick={confirmDone} disabled={statusBusy}>
                  {t("task.confirmDoneBtn")}
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {task && (
        <>
          <div className="section-title">{t("comment.title")}</div>
          <div className="sheet__pad">
            <div className="comment-list">
              {comments.length === 0 && <div className="comment-empty">{t("comment.empty")}</div>}
              {comments.map((c) => (
                <div className="comment" key={c.id}>
                  <div className="comment__head">
                    <span className="comment__author">
                      {c.user_name}
                      {c.target_name ? ` → ${c.target_name}` : ""}
                    </span>
                    <span>{formatDateTime(c.created_at)}</span>
                  </div>
                  {c.reply_to && (
                    <div
                      style={{
                        fontSize: 12,
                        color: "var(--hint)",
                        borderLeft: "2px solid var(--line)",
                        paddingLeft: 8,
                        margin: "2px 0",
                      }}
                    >
                      ↩ {c.reply_to}
                    </div>
                  )}
                  <div className="comment__text">{c.text}</div>
                  <button
                    onClick={() => setReplyTo(c)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--accent)",
                      fontSize: 12,
                      cursor: "pointer",
                      padding: "2px 0",
                    }}
                  >
                    {t("comment.reply")}
                  </button>
                </div>
              ))}
            </div>

            {replyTo && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  background: "var(--secondary-bg)",
                  borderRadius: 8,
                  padding: "6px 10px",
                  fontSize: 13,
                  marginBottom: 6,
                }}
              >
                <span style={{ color: "var(--hint)" }}>
                  ↩ {replyTo.user_name}: {replyTo.text.slice(0, 40)}
                </span>
                <button
                  onClick={() => setReplyTo(null)}
                  style={{ background: "none", border: "none", color: "var(--hint)", cursor: "pointer" }}
                >
                  ✕
                </button>
              </div>
            )}

            {workers.length > 0 && (
              <div className="field" style={{ marginBottom: 8 }}>
                <label>{t("comment.target")}</label>
                <select value={commentTarget} onChange={(e) => setCommentTarget(e.target.value)}>
                  <option value="">{t("comment.toAll")}</option>
                  {workers.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="comment-input">
              <textarea
                value={commentText}
                placeholder={t("comment.placeholder")}
                onChange={(e) => setCommentText(e.target.value)}
              />
              <button
                className="btn btn--primary"
                style={{ width: "auto", padding: "12px 16px" }}
                onClick={sendComment}
                disabled={commentBusy || !commentText.trim()}
              >
                {t("comment.send")}
              </button>
            </div>
          </div>
        </>
      )}

      <div className="sheet__pad">
        <button className="btn btn--ghost" onClick={onClose}>
          {t("common.close")}
        </button>
      </div>
    </Sheet>
  );
}

function formatDateTime(value?: string): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}
