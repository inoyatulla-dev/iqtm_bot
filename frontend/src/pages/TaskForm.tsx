import { useEffect, useRef, useState } from "react";
import {
  AlertTriangle, Clock, CornerUpLeft, FolderKanban, Image, Paperclip, Pencil, X,
} from "lucide-react";
import { attachmentsApi, commentsApi, projectsApi, tasksApi, usersApi } from "../api/client";
import type { Attachment, BoardColumn, Comment, Project, Task, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet, ActionRow } from "../components/Sheet";
import { EmojiIcon } from "../utils/emojiIcon";
import { formatDateTime } from "../utils/datetime";
import { formatCountdown, formatDeadlineDate } from "../utils/deadline";
import { ClockPicker } from "../components/tasks/ClockPicker";
import { ProjectPicker } from "../components/tasks/ProjectPicker";
import { AssigneePicker } from "../components/tasks/AssigneePicker";
import { AvatarStack, StatusPill } from "../components/tasks/parts";

interface Props {
  task: Task | null; // null = yangi
  isBoss: boolean;
  isObserver?: boolean;
  /** Ochilishi bilan darhol "Bajarildi" tasdiqlash+izoh ekraniga o'tadi (svayp tezkor amali) */
  autoConfirmDone?: boolean;
  onClose: () => void;
  onSaved: () => void;
  onStatusChanged?: (task: Task) => void;
}

export function TaskForm({
  task, isBoss, isObserver, autoConfirmDone, onClose, onSaved, onStatusChanged,
}: Props) {
  const { deps, columns, user, timezone } = useAuth();
  const { t, lang } = useI18n();
  const [mode, setMode] = useState<"view" | "edit">(task ? "view" : "edit");
  const [statusOpen, setStatusOpen] = useState(false);
  const [name, setName] = useState(task?.name || "");
  const [desc, setDesc] = useState(task?.description || "");
  const [depId, setDepId] = useState(task?.dep_id || "");
  const [assigneeIds, setAssigneeIds] = useState<number[]>(() => {
    if (task?.assignees?.length) return task.assignees.map((a) => a.id);
    return task?.masul_id ? [task.masul_id] : [];
  });
  const [dueDate, setDueDate] = useState(task?.deadline ? task.deadline.slice(0, 10) : "");
  const [dueTime, setDueTime] = useState(() => {
    const t = task?.deadline ? task.deadline.slice(11, 16) : "";
    return t === "00:00" ? "" : t;
  });
  const [clockOpen, setClockOpen] = useState(false);
  const [projectId, setProjectId] = useState<number | null>(task?.project_id ?? null);
  const [projects, setProjects] = useState<Project[]>([]);
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

  // ── Biriktirmalar ──
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [viewImage, setViewImage] = useState<{ name: string; src: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const cameraRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isBoss) usersApi.list("active").then(setWorkers);
  }, [isBoss]);

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(() => {});
  }, []);

  useEffect(() => {
    if (autoConfirmDone && task) {
      const doneCol = columns.find((c) => c.is_done);
      if (doneCol) {
        setPendingDone(doneCol);
        setDoneComment("");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (task) {
      commentsApi.list(task.id).then(setComments);
      attachmentsApi.list(task.id).then(setAttachments);
    }
  }, [task?.id]);

  const canEdit = !task || isBoss || task.created_by === user?.id;
  const canChangeStatus =
    !!task &&
    (isBoss ||
      task.masul_id === user?.id ||
      !!task.assignees?.some((a) => a.id === user?.id) ||
      (task.type === "personal" && task.created_by === user?.id));
  const targetColumns = columns.filter((c) => isBoss || !c.is_done);
  const dep = deps.find((d) => d.id === task?.dep_id);
  const assigneePeople = task?.assignees?.length
    ? task.assignees
    : task?.masul_name
      ? [{ name: task.masul_name, photo: task.masul_photo }]
      : [];

  async function save() {
    if (name.trim().length < 3) {
      setErr(t("task.nameErr"));
      return;
    }
    setSaving(true);
    setErr("");
    try {
      const deadline = dueDate ? `${dueDate}T${dueTime || "00:00"}` : null;
      const body: Partial<Task> = {
        name: name.trim(),
        description: desc.trim() || null,
        deadline,
        dep_id: depId || null,
        project_id: projectId,
      };
      if (task) {
        if (isBoss) body.assignee_ids = assigneeIds;
        await tasksApi.update(task.id, body);
      } else if (isBoss) {
        body.assignee_ids = assigneeIds;
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
      setStatusOpen(false);
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

  async function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!task || !file) return;
    setUploading(true);
    setErr("");
    try {
      const a = await attachmentsApi.upload(task.id, file);
      setAttachments((prev) => [...prev, a]);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function removeAttachment(a: Attachment) {
    if (!task) return;
    await attachmentsApi.remove(task.id, a.id);
    setAttachments((prev) => prev.filter((x) => x.id !== a.id));
  }

  async function downloadAttachment(a: Attachment) {
    if (!task) return;
    const blob = await attachmentsApi.download(task.id, a.id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = a.file_name;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function openImage(a: Attachment) {
    if (!task) return;
    if (a.url) {
      setViewImage({ name: a.file_name, src: a.url });
      return;
    }
    const blob = await attachmentsApi.download(task.id, a.id);
    setViewImage({ name: a.file_name, src: URL.createObjectURL(blob) });
  }

  function closeImage() {
    if (viewImage?.src.startsWith("blob:")) URL.revokeObjectURL(viewImage.src);
    setViewImage(null);
  }

  return (
    <Sheet
      title={task ? `#${task.id}` : t("task.new")}
      subtitle={task?.project_name ? <><FolderKanban size={14} /> {task.project_name}</> : undefined}
      onClose={onClose}
    >
      {mode === "view" && task && (
        <div className="sheet__pad task-view">
          <div className="task-view__name">{task.name}</div>
          {task.description && <p className="task-view__desc">{task.description}</p>}
          <div className="task-view__meta">
            {dep && (
              <span className="chip chip--dep">
                <span className="dep-dot" style={{ background: dep.color }} />
                {dep.name}
              </span>
            )}
            {task.deadline && (
              <span className={`chip${task.is_overdue ? " chip--overdue" : ""}`}>
                {task.is_overdue ? <AlertTriangle size={12} /> : <Clock size={12} />}{" "}
                {formatDeadlineDate(task.deadline)} · {formatCountdown(task.deadline, lang)}
              </span>
            )}
          </div>
          <div className="field">
            <label>{t("task.assignees")}</label>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <AvatarStack people={assigneePeople} size={30} />
              <span style={{ fontSize: 13, color: "var(--hint)" }}>
                {assigneePeople.map((p) => p.name).join(", ") || t("task.unassigned")}
              </span>
            </div>
          </div>
          {canEdit && (
            <button className="btn btn--ghost" onClick={() => setMode("edit")}>
              <Pencil size={15} /> {t("task.edit")}
            </button>
          )}
        </div>
      )}

      {mode === "edit" && (
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
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>{t("task.masul")}</label>
                <AssigneePicker
                  workers={workers}
                  value={assigneeIds}
                  onChange={setAssigneeIds}
                  disabled={!canEdit}
                />
              </div>
            </>
          )}
          <div className="deadline-fields">
            <div className="field">
              <label>{t("task.deadline")}</label>
              <input
                type="date"
                value={dueDate}
                disabled={!canEdit}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
            <div className="field">
              <label>{t("task.time")}</label>
              <button
                type="button"
                className="time-btn"
                disabled={!canEdit || !dueDate}
                onClick={() => setClockOpen(true)}
              >
                <Clock size={15} />
                {dueTime || t("task.timePh")}
                {dueTime && canEdit && (
                  <X
                    size={14}
                    className="time-btn__clear"
                    onClick={(e) => { e.stopPropagation(); setDueTime(""); }}
                  />
                )}
              </button>
            </div>
          </div>
          {clockOpen && (
            <ClockPicker
              value={dueTime}
              onCancel={() => setClockOpen(false)}
              onConfirm={(v) => { setDueTime(v); setClockOpen(false); }}
            />
          )}

          <div className="field">
            <label>{t("task.project")}</label>
            <ProjectPicker
              projects={projects}
              value={projectId}
              onChange={setProjectId}
              disabled={!canEdit}
            />
          </div>

          {err && <div className="form-error">{err}</div>}

          {canEdit && (
            <button className="btn btn--primary" onClick={save} disabled={saving}>
              {saving ? t("task.saving") : t("common.save")}
            </button>
          )}
          {task && (
            <button className="btn btn--ghost" onClick={() => setMode("view")} disabled={saving}>
              {t("common.cancel")}
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
      )}

      {mode === "view" && task && canChangeStatus && (
        <>
          <div className="section-title">{t("task.statusSection")}</div>
          <div className="sheet__pad task-view__status-row">
            <StatusPill column={columns.find((c) => c.key === task.status)} />
            <button className="btn btn--ghost btn--sm" onClick={() => setStatusOpen((v) => !v)}>
              {t("task.changeStatus")}
            </button>
          </div>
          {statusOpen && (
            <div style={{ borderTop: "1px solid var(--line)" }}>
              {targetColumns.map((col) => (
                <ActionRow
                  key={col.key}
                  icon={<EmojiIcon emoji={col.emoji} color={col.color} size={20} />}
                  label={col.name}
                  checked={task.status === col.key}
                  onClick={() => {
                    changeStatus(col);
                    if (!col.is_done) setStatusOpen(false);
                  }}
                />
              ))}
            </div>
          )}
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

      {mode === "view" && task && (
        <>
          <div className="section-title">{t("task.attachments")}</div>
          <div className="sheet__pad">
            <div className="attachment-list">
              {attachments.length === 0 && (
                <div className="comment-empty">{t("task.attachmentEmpty")}</div>
              )}
              {attachments.map((a) => {
                const isImage = a.mime_type?.startsWith("image/");
                return (
                  <div className="attachment" key={a.id}>
                    {isImage ? (
                      <button
                        className="attachment__name attachment__link"
                        onClick={() => openImage(a)}
                      >
                        <Image size={14} style={{ verticalAlign: "middle", marginRight: 4 }} /> {a.file_name}
                      </button>
                    ) : a.url ? (
                      <a
                        className="attachment__name"
                        href={a.url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        <Paperclip size={14} style={{ verticalAlign: "middle", marginRight: 4 }} /> {a.file_name}
                      </a>
                    ) : (
                      <button
                        className="attachment__name attachment__link"
                        onClick={() => downloadAttachment(a)}
                      >
                        <Paperclip size={14} style={{ verticalAlign: "middle", marginRight: 4 }} /> {a.file_name}
                      </button>
                    )}
                    <span className="attachment__size">{formatFileSize(a.size)}</span>
                    {(isBoss || a.uploaded_by === user?.id) && (
                      <button className="attachment__remove" onClick={() => removeAttachment(a)}>
                        <X size={14} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
            {!isObserver && (
              <>
                <input
                  ref={fileRef}
                  type="file"
                  style={{ display: "none" }}
                  onChange={onFileChange}
                />
                <input
                  ref={cameraRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  style={{ display: "none" }}
                  onChange={onFileChange}
                />
                <div className="report-row">
                  <button
                    className="btn btn--ghost"
                    onClick={() => fileRef.current?.click()}
                    disabled={uploading}
                  >
                    {uploading ? t("task.attachmentUploading") : t("task.attachmentUpload")}
                  </button>
                  <button
                    className="btn btn--ghost"
                    onClick={() => cameraRef.current?.click()}
                    disabled={uploading}
                  >
                    {t("task.attachmentCamera")}
                  </button>
                </div>
              </>
            )}
          </div>

          {!isObserver && (
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
                    <span>{formatDateTime(c.created_at, timezone)}</span>
                  </div>
                  {c.reply_to && (
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 12,
                        color: "var(--hint)",
                        borderLeft: "2px solid var(--line)",
                        paddingLeft: 8,
                        margin: "2px 0",
                      }}
                    >
                      <CornerUpLeft size={12} /> {c.reply_to}
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
                <span style={{ display: "flex", alignItems: "center", gap: 4, color: "var(--hint)" }}>
                  <CornerUpLeft size={14} /> {replyTo.user_name}: {replyTo.text.slice(0, 40)}
                </span>
                <button
                  onClick={() => setReplyTo(null)}
                  style={{ display: "flex", alignItems: "center", background: "none", border: "none", color: "var(--hint)", cursor: "pointer" }}
                >
                  <X size={14} />
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
        </>
      )}

      {viewImage && (
        <div className="image-viewer" onClick={closeImage}>
          <img src={viewImage.src} alt={viewImage.name} onClick={(e) => e.stopPropagation()} />
          <button className="image-viewer__close" onClick={closeImage}>
            <X size={18} />
          </button>
        </div>
      )}
    </Sheet>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
