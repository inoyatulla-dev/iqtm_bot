import { useMemo, useState } from "react";
import { FolderKanban, Search, X } from "lucide-react";
import type { Project } from "../../api/types";

interface Props {
  projects: Project[];
  value: number | null;
  onChange: (id: number | null) => void;
  disabled?: boolean;
}

export function ProjectPicker({ projects, value, onChange, disabled }: Props) {
  const [q, setQ] = useState("");
  const selected = projects.find((p) => p.id === value) || null;

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    return s ? projects.filter((p) => p.name.toLowerCase().includes(s)) : projects;
  }, [projects, q]);

  if (selected) {
    return (
      <div className="proj-selected">
        <span className="proj-selected__body">
          <FolderKanban size={15} />
          {selected.name}
        </span>
        {!disabled && (
          <button className="proj-selected__clear" onClick={() => onChange(null)}>
            <X size={15} />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="proj-picker">
      <div className="proj-picker__search">
        <Search size={15} />
        <input
          placeholder="Loyiha qidirish…"
          value={q}
          disabled={disabled}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <div className="proj-picker__list">
        {filtered.length === 0 && <div className="proj-picker__empty">Loyiha topilmadi</div>}
        {filtered.map((p) => (
          <button key={p.id} className="proj-picker__item" disabled={disabled} onClick={() => onChange(p.id)}>
            {p.name}
          </button>
        ))}
      </div>
    </div>
  );
}
