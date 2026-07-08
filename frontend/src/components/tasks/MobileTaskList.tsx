import { useRef, useState } from "react";
import {
  AlertTriangle, Archive as ArchiveIcon, Check, Clock, MessageCircle, Pencil, Trash2,
} from "lucide-react";
import type { BoardColumn, Department, Task } from "../../api/types";
import { useI18n } from "../../i18n";
import { formatCountdown, formatDeadlineShort } from "../../utils/deadline";
import { progressColor } from "../../utils/progress";
import { AvatarStack, StatusPill } from "./parts";

const BTN_W = 76;

interface Props {
  tasks: Task[];
  columns: BoardColumn[];
  deps: Department[];
  doneKeys: Set<string>;
  canEdit: (t: Task) => boolean;
  canDelete: (t: Task) => boolean;
  canMarkDone: boolean;
  onOpen: (t: Task) => void;
  onEdit: (t: Task) => void;
  onDelete: (t: Task) => void;
  onMarkDone: (t: Task) => void;
  onArchive: (t: Task) => void;
}

export function MobileTaskList({
  tasks, columns, deps, doneKeys, canEdit, canDelete, canMarkDone,
  onOpen, onEdit, onDelete, onMarkDone, onArchive,
}: Props) {
  const colByKey = Object.fromEntries(columns.map((c) => [c.key, c])) as Record<string, BoardColumn>;

  if (!tasks.length) {
    return <div className="table-empty">Vazifa topilmadi</div>;
  }

  return (
    <div className="mobile-task-list">
      {tasks.map((task) => (
        <SwipeCard
          key={task.id}
          task={task}
          dep={deps.find((d) => d.id === task.dep_id)}
          col={colByKey[task.status]}
          done={doneKeys.has(task.status)}
          canEdit={canEdit(task)}
          canDelete={canDelete(task)}
          canMarkDone={canMarkDone}
          onOpen={() => onOpen(task)}
          onEdit={() => onEdit(task)}
          onDelete={() => onDelete(task)}
          onMarkDone={() => onMarkDone(task)}
          onArchive={() => onArchive(task)}
        />
      ))}
    </div>
  );
}

interface CardProps {
  task: Task;
  dep?: Department;
  col?: BoardColumn;
  done: boolean;
  canEdit: boolean;
  canDelete: boolean;
  canMarkDone: boolean;
  onOpen: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onMarkDone: () => void;
  onArchive: () => void;
}

function SwipeCard({
  task, dep, col, done, canEdit, canDelete, canMarkDone,
  onOpen, onEdit, onDelete, onMarkDone, onArchive,
}: CardProps) {
  const { lang } = useI18n();
  const [dx, setDx] = useState(0);
  const drag = useRef<{ startX: number; startDx: number; active: boolean } | null>(null);

  // Chapga (manfiy) surilganda o'ngdagi panel ochiladi: vazifa hali
  // bajarilmagan bo'lsa — "Tayyor", allaqachon bajarilgan bo'lsa — "Arxiv".
  const rightAvailable = done || canMarkDone;
  const leftCount = (canEdit ? 1 : 0) + (canDelete ? 1 : 0);
  const maxLeft = leftCount * BTN_W;
  const maxRight = rightAvailable ? BTN_W : 0;

  function onPointerDown(e: React.PointerEvent) {
    if (maxLeft === 0 && maxRight === 0) return;
    drag.current = { startX: e.clientX, startDx: dx, active: true };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onPointerMove(e: React.PointerEvent) {
    if (!drag.current?.active) return;
    const delta = e.clientX - drag.current.startX;
    const next = Math.min(maxLeft, Math.max(-maxRight, drag.current.startDx + delta));
    setDx(next);
  }
  function endDrag() {
    if (!drag.current) return;
    drag.current.active = false;
    setDx((d) => {
      if (d > maxLeft / 2) return maxLeft;
      if (d < -maxRight / 2) return -maxRight;
      return 0;
    });
  }
  function act(fn: () => void) {
    setDx(0);
    fn();
  }
  function handleClick() {
    if (Math.abs(dx) > 4) {
      setDx(0);
      return;
    }
    onOpen();
  }

  const cd = task.deadline ? formatCountdown(task.deadline, lang) : "";
  const deadlineLabel = task.deadline
    ? (task.is_overdue || cd === "Bugun" ? cd : formatDeadlineShort(task.deadline, lang))
    : "";

  return (
    <div className="mtc-wrap">
      {leftCount > 0 && (
        <div className="mtc-actions mtc-actions--left" style={{ width: maxLeft }}>
          {canEdit && (
            <button className="mtc-btn mtc-btn--edit" onClick={() => act(onEdit)}>
              <Pencil size={16} /> Tahrir
            </button>
          )}
          {canDelete && (
            <button className="mtc-btn mtc-btn--delete" onClick={() => act(onDelete)}>
              <Trash2 size={16} /> O'chir
            </button>
          )}
        </div>
      )}
      {rightAvailable && (
        <div className="mtc-actions mtc-actions--right" style={{ width: maxRight }}>
          {done ? (
            <button className="mtc-btn mtc-btn--archive" onClick={() => act(onArchive)}>
              <ArchiveIcon size={16} /> Arxiv
            </button>
          ) : (
            <button className="mtc-btn mtc-btn--done" onClick={() => act(onMarkDone)}>
              <Check size={16} /> Tayyor
            </button>
          )}
        </div>
      )}

      <div
        className="task-card mtc-card"
        style={{ transform: `translateX(${dx}px)`, "--card-color": dep?.color || "#3390ec" } as React.CSSProperties}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
        onClick={handleClick}
      >
        <div className="task-card__title">{task.name}</div>
        <div className="task-card__meta">
          {(dep || task.project_name) && (
            <span className="chip chip--dep">
              {dep && <span className="dep-dot" style={{ background: dep.color }} />}
              {task.project_name || dep?.name}
            </span>
          )}
          {task.deadline && (
            <span className={`chip${task.is_overdue ? " chip--overdue" : ""}`}>
              {task.is_overdue ? <AlertTriangle size={12} /> : <Clock size={12} />} {deadlineLabel}
            </span>
          )}
          <span className="chip"><MessageCircle size={12} /> {task.comments_count ?? 0}</span>
        </div>
        {task.progress > 0 && (
          <div className="progress-bar task-card__progress">
            <div
              className="progress-bar__fill"
              style={{ width: `${task.progress}%`, background: progressColor(task.progress) }}
            />
          </div>
        )}
        <div className="mtc-foot">
          <StatusPill column={col} />
          <AvatarStack
            people={task.assignees?.length ? task.assignees : [{ name: task.masul_name, photo: task.masul_photo }]}
            size={22}
          />
        </div>
      </div>
    </div>
  );
}
