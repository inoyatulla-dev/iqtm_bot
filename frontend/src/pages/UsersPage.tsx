import { useEffect, useState } from "react";
import { usersApi } from "../api/client";
import type { Department, User } from "../api/types";
import { ROLE_LABEL } from "../api/types";
import { useAuth } from "../store/auth";
import { copyText, inviteLink, shareInvite } from "../telegram";
import { Sheet, ActionRow } from "../components/Sheet";

export function UsersPage() {
  const { deps, user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<User | null>(null);
  const [view, setView] = useState<"actions" | "dep" | "delete" | null>(null);
  const [invite, setInvite] = useState(false);
  const [copied, setCopied] = useState(false);

  async function load() {
    setLoading(true);
    setUsers(await usersApi.list());
    setLoading(false);
  }
  useEffect(() => {
    load();
  }, []);

  async function patch(id: number, body: Partial<User>) {
    try {
      await usersApi.update(id, body);
      setView(null);
      setSel(null);
      load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Xatolik");
    }
  }

  if (loading) return <div className="center-screen">Yuklanmoqda…</div>;

  const pending = users.filter((u) => u.status === "pending");
  const active = users.filter((u) => u.status !== "pending");
  const depName = (id: string | null) => deps.find((d) => d.id === id)?.name || "Bo'limsiz";
  const initials = (n: string) => n.trim().charAt(0).toUpperCase();

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="sheet__pad" style={{ paddingTop: 16 }}>
        <button className="btn btn--primary" onClick={() => setInvite(true)}>
          ➕ Xodim taklif qilish
        </button>
      </div>

      {pending.length > 0 && (
        <>
          <div className="section-title">🔔 Yangi arizalar ({pending.length})</div>
          {pending.map((u) => (
            <div className="list-item" key={u.id}>
              <div className="list-item__avatar">{initials(u.name)}</div>
              <div className="list-item__body">
                <div className="list-item__title">{u.name}</div>
                <div className="list-item__sub">@{u.username || "—"}</div>
              </div>
              <div className="list-item__after">
                <button
                  className="btn btn--primary"
                  style={{ width: "auto", padding: "8px 14px", fontSize: 14 }}
                  onClick={() => patch(u.id, { status: "active", role: "worker" })}
                >
                  Tasdiqlash
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      <div className="section-title">👥 Xodimlar ({active.length})</div>
      {active.map((u) => (
        <div
          className="list-item"
          key={u.id}
          onClick={() => {
            setSel(u);
            setView("actions");
          }}
        >
          <div className="list-item__avatar">{initials(u.name)}</div>
          <div className="list-item__body">
            <div className="list-item__title">
              {u.role === "boss" ? "👑 " : ""}
              {u.name}
            </div>
            <div className="list-item__sub">
              {ROLE_LABEL[u.role]} · {depName(u.dep_id)}
            </div>
          </div>
          <div className="list-item__after">
            {u.status === "blocked" && <span className="badge badge--danger">blok</span>}
          </div>
        </div>
      ))}

      {/* ── Amallar sheet (tugmali) ── */}
      {sel && view === "actions" && (
        <Sheet
          title={sel.name}
          subtitle={`${ROLE_LABEL[sel.role]} · ${depName(sel.dep_id)}`}
          onClose={() => setView(null)}
        >
          {sel.role === "worker" ? (
            <ActionRow
              icon="👑"
              label="Admin qilish"
              onClick={() => patch(sel.id, { role: "boss" })}
            />
          ) : (
            <ActionRow
              icon="👤"
              label="Xodim qilish"
              onClick={() => patch(sel.id, { role: "worker" })}
            />
          )}
          <ActionRow icon="🏢" label="Bo'lim biriktirish" onClick={() => setView("dep")} />
          {sel.status === "blocked" ? (
            <ActionRow
              icon="✅"
              label="Blokdan chiqarish"
              onClick={() => patch(sel.id, { status: "active" })}
            />
          ) : (
            <ActionRow
              icon="🚫"
              label="Bloklash"
              onClick={() => patch(sel.id, { status: "blocked" })}
            />
          )}
          {sel.id !== me?.id && (
            <ActionRow icon="🗑" label="O'chirish" danger onClick={() => setView("delete")} />
          )}
        </Sheet>
      )}

      {/* ── Bo'lim tanlash sheet ── */}
      {sel && view === "dep" && (
        <Sheet title="Bo'lim biriktirish" onClose={() => setView("actions")}>
          <ActionRow
            icon="—"
            label="Bo'limsiz"
            checked={!sel.dep_id}
            onClick={() => patch(sel.id, { dep_id: null })}
          />
          {deps.map((d: Department) => (
            <ActionRow
              key={d.id}
              icon={d.emoji}
              label={d.name}
              checked={sel.dep_id === d.id}
              onClick={() => patch(sel.id, { dep_id: d.id })}
            />
          ))}
        </Sheet>
      )}

      {/* ── O'chirish tasdiqlash ── */}
      {sel && view === "delete" && (
        <Sheet title="O'chirishni tasdiqlang" subtitle={sel.name} onClose={() => setView("actions")}>
          <div className="sheet__pad">
            <button
              className="btn btn--danger"
              onClick={async () => {
                try {
                  await usersApi.remove(sel.id);
                  setView(null);
                  setSel(null);
                  load();
                } catch (e: any) {
                  alert(e?.response?.data?.detail || "Xatolik");
                }
              }}
            >
              🗑 Ha, o'chirish
            </button>
            <button className="btn btn--ghost" onClick={() => setView("actions")}>
              Bekor qilish
            </button>
          </div>
        </Sheet>
      )}

      {/* ── Taklif sheet (copy / share) ── */}
      {invite && (
        <Sheet
          title="Xodim taklif qilish"
          subtitle="Havolani yuboring — xodim botni ochib ariza qoldiradi, keyin uni tasdiqlaysiz"
          onClose={() => setInvite(false)}
        >
          <div className="sheet__pad">
            <div className="field">
              <label>Taklif havolasi</label>
              <input readOnly value={inviteLink()} onFocus={(e) => e.target.select()} />
            </div>
            <button className="btn btn--primary" onClick={() => shareInvite()}>
              📤 Telegram orqali ulashish
            </button>
            <button
              className="btn btn--ghost"
              onClick={async () => {
                const ok = await copyText(inviteLink());
                setCopied(ok);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? "✅ Nusxalandi" : "📋 Nusxalash"}
            </button>
          </div>
        </Sheet>
      )}
    </div>
  );
}
