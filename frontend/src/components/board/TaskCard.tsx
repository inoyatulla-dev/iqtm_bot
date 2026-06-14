import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { AlertTriangle, Clock, Paperclip, User } from "lucide-react";
import type { Department, Task } from "../../api/types";
import { useI18n } from "../../i18n";
import { formatCountdown, formatDeadlineDate } from "../../utils/deadline";

interface Props {
  task: Task;
  dep?: Department;
  onClick: (t: Task) => void;
}

export function TaskCard({ task, dep, onClick }: Props) {
  const { lang } = useI18n();
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: task.id });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1,
    "--card-color": dep?.color || "#3390ec",
  } as React.CSSProperties;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="task-card"
      {...listeners}
      {...attributes}
      onClick={() => !isDragging && onClick(task)}
    >
      <div className="task-card__title">
        {task.type === "personal" && <User size={14} style={{ verticalAlign: "-2px", marginRight: 4 }} />}
        {task.name}
      </div>
      {task.masul_name && (
        <div className="task-card__assignee">
          <span className="avatar-wrap" style={{ width: 20, height: 20 }}>
            <span className="avatar" style={{ fontSize: 11 }}>
              {task.masul_photo ? (
                <img src={task.masul_photo} alt="" />
              ) : (
                task.masul_name.slice(0, 1).toUpperCase()
              )}
            </span>
          </span>
          {task.masul_name}
        </div>
      )}
      <div className="task-card__meta">
        {dep && (
          <span className="chip chip--dep">
            <span className="dep-dot" style={{ background: dep.color }} />
            {dep.name}
          </span>
        )}
        {task.deadline && (
          <span className={`chip${task.is_overdue ? " chip--overdue" : ""}`}>
            {task.is_overdue ? <AlertTriangle size={12} /> : <Clock size={12} />} {formatDeadlineDate(task.deadline)} · {formatCountdown(task.deadline, lang)}
          </span>
        )}
        {task.attachments_count > 0 && (
          <span className="chip"><Paperclip size={12} /> {task.attachments_count}</span>
        )}
      </div>
    </div>
  );
}
