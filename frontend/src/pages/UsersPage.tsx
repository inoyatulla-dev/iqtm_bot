import { useEffect, useState } from "react";
import { usersApi } from "../api/client";
import type { Department, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { copyText, inviteLink, shareInvite } from "../telegram";
import { Sheet, ActionRow } from "../components/Sheet";
import { avatarGradient } from "../utils/avatarColor";
import { birthdayInDays, formatBirthdayDate } from "../utils/birthday";

export function UsersPage() {
  const { deps, user: me } = useAuth();
  const { t } = useI18n();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<User | null>(null);
  const [view, setView] = useState<"actions" | "dep" | "delete" | null>(null);
  const [invite, setInvite] = useState(false);
  const [copied, setCopied] = useState(false);
  const [query, setQuery] = useState("");

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

  const q = query.trim().toLowerCase();
  const visible = q
    ? active.filter(
        (u) => u.name.toLowerCase().includes(q) || (u.username || "").toLowerCase().includes(q)
      )
    : active;

  const birthdayUser = active.find((u) => birthdayInDays(u.birthday) === 0);

  return (
    <div className="page-content">
      {birthdayUser && (
        <div className="birthday-banner">
          <div className="birthday-banner__icon">🎉</div>
          <div>
            <div className="birthday-banner__title">
              {t("users.birthdayToday").replace("{name}", birthdayUser.name)}
            </div>
            <div className="birthday-banner__sub">{t("users.birthdaySub")}</div>
          </div>
        </div>
      )}

      <div className="toolbar">
        <input
          className="search-input"
          placeholder={t("users.search")}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn btn--primary" style={{ width: "auto" }} onClick={() => setInvite(true)}>
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
        {t("users.list")} ({visible.length})
      </div>
      <div className="emp-grid">
        {visible.map((u) => {
          const days = birthdayInDays(u.birthday);
          return (
            <div
              className="emp-card"
              key={u.id}
              style={u.status === "blocked" ? { opacity: 0.6 } : undefined}
              onClick={() => {
                setSel(u);
                setView("actions");
              }}
            >
              <div className="emp-card__head">
                <div className="avatar-wrap">
                  <div className="avatar" style={{ background: avatarGradient(u.id) }}>
                    {u.photo ? <img src={u.photo} alt="" /> : initials(u.name)}
                  </div>
                </div>
                <div>
                  <div className="emp-card__name">
                    {u.role === "boss" ? "👑 " : ""}
                    {u.name}
                  </div>
                  <div className="emp-card__role">
                    {t(`role.${u.role}`)} · {depName(u.dep_id)}
                  </div>
                </div>
              </div>
              {(u.birthday || u.status === "blocked") && (
                <div className="emp-card__row">
                  {u.birthday ? (
                    <span>🎂 {formatBirthdayDate(u.birthday)}</span>
                  ) : (
                    <span />
                  )}
                  {u.status === "blocked" ? (
                    <span className="badge badge--danger">{t("users.blocked")}</span>
                  ) : days != null && days <= 60 ? (
                    <span className={`badge ${days === 0 ? "badge--warn" : "badge--accent"}`}>
                      {days === 0 ? t("users.birthdayBadgeToday") : t("users.birthdayIn").replace("{days}", String(days))}
                    </span>
                  ) : null}
                </div>
              )}
            </div>
          );
        })}
      </div>

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
