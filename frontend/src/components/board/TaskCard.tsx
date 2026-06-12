import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
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
        {task.type === "personal" ? "👤 " : ""}
        {task.name}
      </div>
      <div className="task-card__meta">
        {dep && (
          <span className="chip chip--dep">
            <span className="dep-dot" style={{ background: dep.color }} />
            {dep.name}
          </span>
        )}
        {task.masul_name && (
          <span className="chip">👤 {task.masul_name}</span>
        )}
        {task.deadline && (
          <span className={`chip${task.is_overdue ? " chip--overdue" : ""}`}>
            {task.is_overdue ? "⚠️" : "⏰"} {formatDeadlineDate(task.deadline)} · {formatCountdown(task.deadline, lang)}
          </span>
        )}
        {task.attachments_count > 0 && (
          <span className="chip">📎 {task.attachments_count}</span>
        )}
      </div>
    </div>
  );
}
