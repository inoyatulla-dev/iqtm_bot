import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { TaskStatus } from "../../api/types";
import { STATUS_EMOJI, STATUS_LABEL } from "../../api/types";

interface Props {
  status: TaskStatus;
  count: number;
  children: ReactNode;
}

export function Column({ status, count, children }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: status });

  return (
    <div
      ref={setNodeRef}
      className="board-column"
      style={isOver ? { outline: "2px dashed var(--tgui--link_color,#2481cc)" } : undefined}
    >
      <div className="board-column__header">
        <span>
          {STATUS_EMOJI[status]} {STATUS_LABEL[status]}
        </span>
        <span style={{ opacity: 0.6 }}>{count}</span>
      </div>
      <div className="board-column__list">{children}</div>
    </div>
  );
}
