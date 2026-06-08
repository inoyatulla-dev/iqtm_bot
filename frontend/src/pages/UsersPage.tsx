import { useEffect, useState } from "react";
import { usersApi } from "../api/client";
import type { Department, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { copyText, inviteLink, shareInvite } from "../telegram";
import { Sheet, ActionRow } from "../components/Sheet";

export function UsersPage() {
  const { deps, user: me } = useAuth();
  const { t } = useI18n();
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
      alert(e?.response?.data?.detail || t("common.error"));
    }
  }

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

  const pending = users.filter((u) => u.status === "pending");
  const active = users.filter((u) => u.status !== "pending");
  const depName = (id: string | null) => deps.find((d) => d.id === id)?.name || t("users.noDept");
  const initials = (n: string) => n.trim().charAt(0).toUpperCase();

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="sheet__pad" style={{ paddingTop: 16 }}>
        <button className="btn btn--primary" onClick={() => setInvite(true)}>
          {t("users.invite")}
        </button>
      </div>

      {pending.length > 0 && (
        <>
          <div className="section-title">
            {t("users.pending")} ({pending.length})
          </div>
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
                  {t("users.approve")}
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      <div className="section-title">
        {t("users.list")} ({active.length})
      </div>
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
              {t(`role.${u.role}`)} · {depName(u.dep_id)}
            </div>
          </div>
          <div className="list-item__after">
            {u.status === "blocked" && <span className="badge badge--danger">{t("users.blocked")}</span>}
          </div>
        </div>
      ))}

      {sel && view === "actions" && (
        <Sheet
          title={sel.name}
          subtitle={`${t(`role.${sel.role}`)} · ${depName(sel.dep_id)}`}
          onClose={() => setView(null)}
        >
          {sel.role === "worker" ? (
            <ActionRow icon="👑" label={t("users.makeAdmin")} onClick={() => patch(sel.id, { role: "boss" })} />
          ) : (
            <ActionRow icon="👤" label={t("users.makeWorker")} onClick={() => patch(sel.id, { role: "worker" })} />
          )}
          <ActionRow icon="🏢" label={t("users.assignDept")} onClick={() => setView("dep")} />
          {sel.status === "blocked" ? (
            <ActionRow icon="✅" label={t("users.unblock")} onClick={() => patch(sel.id, { status: "active" })} />
          ) : (
            <ActionRow icon="🚫" label={t("users.block")} onClick={() => patch(sel.id, { status: "blocked" })} />
          )}
          {sel.id !== me?.id && (
            <ActionRow icon="🗑" label={t("users.delete")} danger onClick={() => setView("delete")} />
          )}
        </Sheet>
      )}

      {sel && view === "dep" && (
        <Sheet title={t("users.assignDept")} onClose={() => setView("actions")}>
          <ActionRow
            icon="—"
            label={t("users.noDept")}
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

      {sel && view === "delete" && (
        <Sheet title={t("users.confirmDelTitle")} subtitle={sel.name} onClose={() => setView("actions")}>
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
                  alert(e?.response?.data?.detail || t("common.error"));
                }
              }}
            >
              {t("users.confirmDelBtn")}
            </button>
            <button className="btn btn--ghost" onClick={() => setView("actions")}>
              {t("common.cancel")}
            </button>
          </div>
        </Sheet>
      )}

      {invite && (
        <Sheet title={t("users.inviteTitle")} subtitle={t("users.inviteSub")} onClose={() => setInvite(false)}>
          <div className="sheet__pad">
            <div className="field">
              <label>{t("users.linkLabel")}</label>
              <input readOnly value={inviteLink()} onFocus={(e) => e.target.select()} />
            </div>
            <button className="btn btn--primary" onClick={() => shareInvite()}>
              {t("users.share")}
            </button>
            <button
              className="btn btn--ghost"
              onClick={async () => {
                const ok = await copyText(inviteLink());
                setCopied(ok);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? t("users.copied") : t("users.copy")}
            </button>
          </div>
        </Sheet>
      )}
    </div>
  );
}
