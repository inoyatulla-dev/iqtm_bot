import { useEffect, useState } from "react";
import { Ban, Cake, Check, Crown, PartyPopper, Pencil, Trash2 } from "lucide-react";
import { usersApi } from "../api/client";
import type { Department, Role, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { copyText, inviteLink, shareInvite } from "../telegram";
import { Sheet, ActionRow } from "../components/Sheet";
import { avatarGradient } from "../utils/avatarColor";
import { birthdayInDays } from "../utils/birthday";
import { EmojiIcon } from "../utils/emojiIcon";

export function UsersPage() {
  const { deps, user: me, isBoss } = useAuth();
  const { t } = useI18n();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<User | null>(null);
  const [view, setView] = useState<"profile" | "edit" | "delete" | null>(null);
  const [invite, setInvite] = useState(false);
  const [copied, setCopied] = useState(false);
  const [query, setQuery] = useState("");

  const [editName, setEditName] = useState("");
  const [editRole, setEditRole] = useState<Role>("worker");
  const [editDep, setEditDep] = useState("");
  const [editBirthday, setEditBirthday] = useState("");
  const [editSaving, setEditSaving] = useState(false);

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

  function openProfile(u: User) {
    setSel(u);
    setView("profile");
  }

  function openEdit(u: User) {
    setEditName(u.name);
    setEditRole(u.role);
    setEditDep(u.dep_id || "");
    setEditBirthday(u.birthday || "");
    setView("edit");
  }

  async function saveEdit() {
    if (!sel) return;
    setEditSaving(true);
    try {
      const updated = await usersApi.update(sel.id, {
        name: editName.trim(),
        role: editRole,
        dep_id: editDep || null,
        birthday: editBirthday || null,
      });
      setSel(updated);
      setView("profile");
      load();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    } finally {
      setEditSaving(false);
    }
  }

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

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
  const selDays = birthdayInDays(sel?.birthday);

  return (
    <div className="page-content">
      {birthdayUser && (
        <div className="birthday-banner">
          <div className="birthday-banner__icon"><PartyPopper size={24} /></div>
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
        {isBoss && (
          <button className="btn btn--primary" style={{ width: "auto" }} onClick={() => setInvite(true)}>
            {t("users.invite")}
          </button>
        )}
      </div>

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
              onClick={() => openProfile(u)}
            >
              <div className="emp-card__head">
                <div className="avatar-wrap">
                  <div className="avatar" style={{ background: avatarGradient(u.id) }}>
                    {u.photo ? <img src={u.photo} alt="" /> : initials(u.name)}
                  </div>
                  {u.custom_emoji && <span className="emoji-badge"><EmojiIcon emoji={u.custom_emoji} size={11} /></span>}
                </div>
                <div>
                  <div className="emp-card__name">
                    {u.role === "boss" && <Crown size={16} />}
                    {u.name}
                  </div>
                  <div className="emp-card__role">
                    {t(`role.${u.role}`)} · {depName(u.dep_id)}
                  </div>
                </div>
              </div>
              {((days != null && days <= 3) || u.status === "blocked") && (
                <div className="emp-card__row">
                  {days != null && days <= 3 ? (
                    <span className={`badge ${days === 0 ? "badge--warn" : "badge--accent"}`} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                      <Cake size={12} /> {days === 0 ? t("users.birthdayBadgeToday") : t("users.birthdayIn").replace("{days}", String(days))}
                    </span>
                  ) : (
                    <span />
                  )}
                  {u.status === "blocked" && (
                    <span className="badge badge--danger">{t("users.blocked")}</span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {sel && view === "profile" && (
        <Sheet
          title={sel.name}
          subtitle={`${t(`role.${sel.role}`)} · ${depName(sel.dep_id)}`}
          onClose={() => { setView(null); setSel(null); }}
        >
          <div className="sheet__pad">
            <div className="emp-card__head">
              <div className="avatar-wrap" style={{ width: 64, height: 64, fontSize: 24 }}>
                <div className="avatar" style={{ background: avatarGradient(sel.id) }}>
                  {sel.photo ? <img src={sel.photo} alt="" /> : initials(sel.name)}
                </div>
                {sel.custom_emoji && <span className="emoji-badge"><EmojiIcon emoji={sel.custom_emoji} size={13} /></span>}
              </div>
              <div>
                <div className="emp-card__name">
                  {sel.role === "boss" && <Crown size={16} />}
                  {sel.name}
                </div>
                <div className="emp-card__role">
                  {t(`role.${sel.role}`)} · {depName(sel.dep_id)}
                </div>
              </div>
            </div>
            {((selDays != null && selDays <= 3) || sel.status === "blocked") && (
              <div className="emp-card__row" style={{ marginTop: 12 }}>
                {selDays != null && selDays <= 3 ? (
                  <span className={`badge ${selDays === 0 ? "badge--warn" : "badge--accent"}`} style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    <Cake size={12} /> {selDays === 0 ? t("users.birthdayBadgeToday") : t("users.birthdayIn").replace("{days}", String(selDays))}
                  </span>
                ) : (
                  <span />
                )}
                {sel.status === "blocked" && (
                  <span className="badge badge--danger">{t("users.blocked")}</span>
                )}
              </div>
            )}
          </div>
          {isBoss && (
            <>
              <ActionRow icon={<Pencil size={20} />} label={t("users.edit")} onClick={() => openEdit(sel)} />
              {sel.status === "blocked" ? (
                <ActionRow icon={<Check size={20} />} label={t("users.unblock")} onClick={() => patch(sel.id, { status: "active" })} />
              ) : (
                <ActionRow icon={<Ban size={20} />} label={t("users.block")} onClick={() => patch(sel.id, { status: "blocked" })} />
              )}
              {sel.id !== me?.id && (
                <ActionRow icon={<Trash2 size={20} />} label={t("users.delete")} danger onClick={() => setView("delete")} />
              )}
            </>
          )}
        </Sheet>
      )}

      {sel && view === "edit" && (
        <Sheet title={t("users.editTitle")} subtitle={sel.name} onClose={() => setView("profile")}>
          <div className="sheet__pad">
            <div className="field">
              <label>{t("users.name")}</label>
              <input value={editName} onChange={(e) => setEditName(e.target.value)} />
            </div>
            <div className="field">
              <label>{t("users.role")}</label>
              <select value={editRole} onChange={(e) => setEditRole(e.target.value as Role)}>
                <option value="boss">{t("role.boss")}</option>
                <option value="worker">{t("role.worker")}</option>
                <option value="observer">{t("role.observer")}</option>
              </select>
            </div>
            <div className="field">
              <label>{t("users.assignDept")}</label>
              <select value={editDep} onChange={(e) => setEditDep(e.target.value)}>
                <option value="">{t("users.noDept")}</option>
                {deps.map((d: Department) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>{t("users.birthday")}</label>
              <input type="date" value={editBirthday} onChange={(e) => setEditBirthday(e.target.value)} />
            </div>
            <button className="btn btn--primary" onClick={saveEdit} disabled={editSaving}>
              {editSaving ? t("task.saving") : t("common.save")}
            </button>
          </div>
        </Sheet>
      )}

      {sel && view === "delete" && (
        <Sheet title={t("users.confirmDelTitle")} subtitle={sel.name} onClose={() => setView("profile")}>
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
            <button className="btn btn--ghost" onClick={() => setView("profile")}>
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
