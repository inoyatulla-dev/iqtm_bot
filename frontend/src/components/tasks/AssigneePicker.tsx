import { useMemo, useState } from "react";
import { Check, Search, X } from "lucide-react";
import type { User } from "../../api/types";
import { ROLE_LABEL } from "../../api/types";
import { Avatar } from "./parts";

interface Props {
  workers: User[];
  value: number[];
  onChange: (ids: number[]) => void;
  disabled?: boolean;
}

export function AssigneePicker({ workers, value, onChange, disabled }: Props) {
  const [q, setQ] = useState("");

  const byId = useMemo(() => new Map(workers.map((w) => [w.id, w])), [workers]);
  const selected = value.map((id) => byId.get(id)).filter(Boolean) as User[];

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    if (!s) return workers;
    return workers.filter(
      (w) => w.name.toLowerCase().includes(s) || ROLE_LABEL[w.role].toLowerCase().includes(s)
    );
  }, [workers, q]);

  function toggle(id: number) {
    if (disabled) return;
    onChange(value.includes(id) ? value.filter((x) => x !== id) : [...value, id]);
  }

  return (
    <div className="asg-picker">
      <div className="asg-picker__head">
        <span className="asg-picker__count">{value.length} tanlandi</span>
      </div>

      {selected.length > 0 && (
        <div className="asg-chips">
          {selected.map((w) => (
            <span key={w.id} className="asg-chip">
              <Avatar name={w.name} photo={w.photo} size={20} />
              {w.name}
              {!disabled && (
                <button className="asg-chip__x" onClick={() => toggle(w.id)}>
                  <X size={13} />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      <div className="asg-picker__search">
        <Search size={15} />
        <input
          placeholder="Xodim qidirish (ism yoki lavozim)…"
          value={q}
          disabled={disabled}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      <div className="asg-picker__list">
        {filtered.length === 0 && <div className="asg-picker__empty">Xodim topilmadi</div>}
        {filtered.map((w) => {
          const on = value.includes(w.id);
          return (
            <button
              key={w.id}
              className={`asg-row${on ? " on" : ""}`}
              disabled={disabled}
              onClick={() => toggle(w.id)}
            >
              <Avatar name={w.name} photo={w.photo} size={34} />
              <span className="asg-row__body">
                <span className="asg-row__name">{w.name}</span>
                <span className="asg-row__sub">{ROLE_LABEL[w.role]}</span>
              </span>
              <span className={`asg-check${on ? " on" : ""}`}>{on && <Check size={13} />}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
