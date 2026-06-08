import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { Department, Task } from "../../api/types";

interface Props {
  task: Task;
  dep?: Department;
  onClick: (t: Task) => void;
}

export function TaskCard({ task, dep, onClick }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: task.id });

  const style = {
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1,
    "--card-color": dep?.color || "#2481cc",
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
          <span>
            {dep.emoji} {dep.name}
          </span>
        )}
        {task.deadline && (
          <span className={task.is_overdue ? "task-card__overdue" : ""}>
            ⏰ {task.deadline}
            {task.is_overdue ? " ⚠️" : ""}
          </span>
        )}
      </div>
    </div>
  );
}
