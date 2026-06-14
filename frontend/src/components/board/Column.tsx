import { useDroppable } from "@dnd-kit/core";
import type { ReactNode } from "react";
import type { BoardColumn } from "../../api/types";
import { useI18n } from "../../i18n";
import { EmojiIcon } from "../../utils/emojiIcon";

interface Props {
  column: BoardColumn;
  count: number;
  children: ReactNode;
}

export function Column({ column, count, children }: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: column.key });
  const { t } = useI18n();

  return (
    <div
      ref={setNodeRef}
      className="board-column"
      style={isOver ? { outline: "2px dashed var(--accent)" } : undefined}
    >
      <div className="board-column__header">
        <span className="board-column__dot" style={{ background: column.color }} />
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <EmojiIcon emoji={column.emoji} size={14} color={column.color} /> {column.name}
        </span>
        <span className="board-column__count">{count}</span>
      </div>
      <div className="board-column__list">
        {count === 0 ? <div className="board-column__empty">{t("board.empty")}</div> : children}
      </div>
    </div>
  );
}
