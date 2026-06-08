import { useState } from "react";
import { depsApi } from "../api/client";
import type { Department } from "../api/types";
import { useAuth } from "../store/auth";
import { Sheet } from "../components/Sheet";

const EMOJIS = ["🔌", "💻", "📐", "🔧", "🎨", "🏢", "📦", "🔬", "⚙️", "📊"];
const COLORS = ["#3b82f6", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444", "#ec4899"];

export function DepartmentsPage() {
  const { deps, reload } = useAuth();
  const [edit, setEdit] = useState<Department | null>(null);
  const [creating, setCreating] = useState(false);

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="sheet__pad" style={{ paddingTop: 16 }}>
        <button className="btn btn--primary" onClick={() => setCreating(true)}>
          ➕ Bo'lim qo'shish
        </button>
      </div>

      <div className="section-title">🏢 Bo'limlar ({deps.length})</div>
      {deps.map((d) => (
        <div className="list-item" key={d.id} onClick={() => setEdit(d)}>
          <span style={{ fontSize: 24 }}>{d.emoji}</span>
          <div className="list-item__body">
            <div className="list-item__title">{d.name}</div>
            <div className="list-item__sub">kod: {d.id}</div>
          </div>
          <span className="dep-dot" style={{ background: d.color, width: 14, height: 14 }} />
        </div>
      ))}

      {creating && (
        <DeptForm
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      )}
      {edit && (
        <DeptForm
          dep={edit}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

function DeptForm({
  dep,
  onClose,
  onSaved,
}: {
  dep?: Department;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [id, setId] = useState(dep?.id || "");
  const [name, setName] = useState(dep?.name || "");
  const [emoji, setEmoji] = useState(dep?.emoji || "🏢");
  const [color, setColor] = useState(dep?.color || COLORS[0]);
  const [err, setErr] = useState("");

  async function save() {
    if (!dep && !/^[a-z0-9]{2,10}$/.test(id)) {
      setErr("Kod: 2-10 ta kichik harf/raqam (masalan: it)");
      return;
    }
    if (name.trim().length < 2) {
      setErr("Nom kamida 2 harf");
      return;
    }
    try {
      if (dep) await depsApi.update(dep.id, { name, emoji, color });
      else await depsApi.create({ id, name, emoji, color });
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Xatolik");
    }
  }

  async function remove() {
    if (!dep) return;
    try {
      await depsApi.remove(dep.id);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Xatolik");
    }
  }

  return (
    <Sheet title={dep ? "Bo'limni tahrirlash" : "Yangi bo'lim"} onClose={onClose}>
      <div className="sheet__pad">
        {!dep && (
          <div className="field">
            <label>Kod (lotin, masalan: it)</label>
            <input value={id} onChange={(e) => setId(e.target.value.toLowerCase())} />
          </div>
        )}
        <div className="field">
          <label>Nomi</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label>Emoji</label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {EMOJIS.map((e) => (
              <button
                key={e}
                onClick={() => setEmoji(e)}
                style={{
                  fontSize: 22,
                  padding: 6,
                  borderRadius: 10,
                  border: emoji === e ? "2px solid var(--accent)" : "1px solid var(--line)",
                  background: "var(--secondary-bg)",
                  cursor: "pointer",
                }}
              >
                {e}
              </button>
            ))}
          </div>
        </div>
        <div className="field">
          <label>Rang</label>
          <div style={{ display: "flex", gap: 10 }}>
            {COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setColor(c)}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: c,
                  border: color === c ? "3px solid var(--text)" : "none",
                  cursor: "pointer",
                }}
              />
            ))}
          </div>
        </div>

        {err && <div className="form-error">{err}</div>}

        <button className="btn btn--primary" onClick={save}>
          Saqlash
        </button>
        {dep && (
          <button className="btn btn--danger" onClick={remove}>
            🗑 O'chirish
          </button>
        )}
      </div>
    </Sheet>
  );
}
