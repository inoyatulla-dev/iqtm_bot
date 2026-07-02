import { useEffect, useMemo, useState } from "react";
import { Paperclip, RotateCcw } from "lucide-react";
import type { BoardColumn, Department, Task } from "../../api/types";
import { formatDeadlineDate } from "../../utils/deadline";
import { AvatarStack, StatusPill } from "./parts";

function assigneePeople(task: Task) {
  if (task.assignees?.length) return task.assignees;
  return task.masul_name ? [{ name: task.masul_name, photo: task.masul_photo }] : [];
}

const PAGE_SIZES = [6, 8, 12, 20];

interface Props {
  tasks: Task[];
  columns: BoardColumn[];
  deps: Department[];
  variant: "list" | "archive";
  onOpen: (t: Task) => void;
  onRestore?: (t: Task) => void;
  restoringId?: number | null;
}

export function TasksTable({ tasks, columns, deps, variant, onOpen, onRestore, restoringId }: Props) {
  const archive = variant === "archive";
  const [pageSize, setPageSize] = useState(archive ? 6 : 8);
  const [page, setPage] = useState(1);

  const colByKey = useMemo(
    () => Object.fromEntries(columns.map((c) => [c.key, c])) as Record<string, BoardColumn>,
    [columns]
  );

  const totalPages = Math.max(1, Math.ceil(tasks.length / pageSize));
  useEffect(() => {
    if (page > totalPages) setPage(1);
  }, [page, totalPages]);

  const slice = tasks.slice((page - 1) * pageSize, page * pageSize);
  const from = tasks.length ? (page - 1) * pageSize + 1 : 0;
  const to = Math.min(page * pageSize, tasks.length);

  if (!tasks.length) {
    return <div className="table-empty">Vazifa topilmadi</div>;
  }

  return (
    <div className="tasks-table-wrap">
      <table className="tasks-table">
        <thead>
          <tr>
            <th>Vazifa</th>
            <th className="hide-sm">Loyiha</th>
            {archive ? <th className="hide-sm">Mas'ul</th> : <th className="hide-sm">Holat</th>}
            <th className="hide-sm">{archive ? "Yakunlandi" : "Muddat"}</th>
            {!archive && <th className="hide-sm">Mas'ul</th>}
            <th style={{ textAlign: archive ? "right" : "center", width: archive ? 110 : 64 }}>
              {archive ? "Amal" : "Fayl"}
            </th>
          </tr>
        </thead>
        <tbody>
          {slice.map((task) => {
            const dep = deps.find((d) => d.id === task.dep_id);
            const col = colByKey[task.status];
            return (
              <tr key={task.id} onClick={() => onOpen(task)}>
                <td>
                  <div className="tt-name">
                    <span className="tt-dot" style={{ background: col?.color || dep?.color || "#64748b" }} />
                    <span className="tt-title">{task.name}</span>
                  </div>
                </td>
                <td className="hide-sm tt-muted">{task.project_name || dep?.name || "—"}</td>
                {archive ? (
                  <td className="hide-sm">
                    <span className="tt-masul">
                      <AvatarStack people={assigneePeople(task)} size={24} />
                      {task.masul_name || "—"}
                    </span>
                  </td>
                ) : (
                  <td className="hide-sm"><StatusPill column={col} /></td>
                )}
                <td className={`hide-sm ${!archive && task.is_overdue ? "tt-overdue" : "tt-muted"}`}>
                  {archive
                    ? task.deadline ? formatDeadlineDate(task.deadline) : (task.created_at ? formatDeadlineDate(task.created_at) : "—")
                    : task.deadline ? formatDeadlineDate(task.deadline) : "—"}
                </td>
                {!archive && (
                  <td className="hide-sm">
                    <AvatarStack people={assigneePeople(task)} size={26} />
                  </td>
                )}
                <td style={{ textAlign: archive ? "right" : "center" }}>
                  {archive ? (
                    onRestore && (
                      <button
                        className="btn btn--ghost btn--sm"
                        onClick={(e) => { e.stopPropagation(); onRestore(task); }}
                        disabled={restoringId === task.id}
                      >
                        <RotateCcw size={14} /> Tiklash
                      </button>
                    )
                  ) : task.attachments_count > 0 ? (
                    <span className="tt-count"><Paperclip size={13} /> {task.attachments_count}</span>
                  ) : (
                    <span className="tt-muted">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="table-foot">
        <span className="tt-muted">{from}–{to} / {tasks.length}</span>
        <label className="table-foot__size">
          Sahifada:
          <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
            {PAGE_SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        {totalPages > 1 && (
          <div className="pager">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                className={`pager__btn${p === page ? " active" : ""}`}
                onClick={() => setPage(p)}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
