import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { TaskStatus } from "../../api/types";
import { STATUS_EMOJI } from "../../api/types";
import { useI18n } from "../../i18n";

const STATUS_COLOR: Record<TaskStatus, string> = {
  new: "#64748b",
  in_progress: "#f59e0b",
  review: "#8b5cf6",
  done: "#10b981",
};

interface Props {
  status: TaskStatus;
  count: number;
  children: ReactNode;
}

export function Column({ status, count, children }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const { t } = useI18n();

  return (
    <div
      ref={setNodeRef}
      className="board-column"
      style={isOver ? { outline: "2px dashed var(--accent)" } : undefined}
    >
      <div className="board-column__header">
        <span className="board-column__dot" style={{ background: STATUS_COLOR[status] }} />
        <span>
          {STATUS_EMOJI[status]} {t(`status.${status}`)}
        </span>
        <span className="board-column__count">{count}</span>
      </div>
      <div className="board-column__list">
        {count === 0 ? <div className="board-column__empty">{t("board.empty")}</div> : children}
      </div>
    </div>
  );
}
