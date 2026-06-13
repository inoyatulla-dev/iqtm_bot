import { useEffect, useState } from "react";
import { usersApi } from "../api/client";
import type { Department, Role, User } from "../api/types";
import { useAuth } from "../store/auth";
import { useI18n } from "../i18n";
import { Sheet, ActionRow } from "../components/Sheet";
import { avatarGradient } from "../utils/avatarColor";

interface Props {
  onChange?: () => void;
}

export function ArizalarPage({ onChange }: Props) {
  const { deps } = useAuth();
  const { t } = useI18n();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState<User | null>(null);
  const [view, setView] = useState<"role" | "dep" | null>(null);
  const [chosenRole, setChosenRole] = useState<Role | null>(null);

  async function load() {
    setLoading(true);
    setUsers(await usersApi.list("pending"));
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const initials = (n: string) => n.trim().charAt(0).toUpperCase();

  async function approve(role: Role, depId: string | null) {
    if (!sel) return;
    try {
      await usersApi.approve(sel.id, role, depId ?? undefined);
      setView(null);
      setSel(null);
      setChosenRole(null);
      load();
      onChange?.();
    } catch (e: any) {
      alert(e?.response?.data?.detail || t("common.error"));
    }
  }

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

  return (
    <div className="page-content">
      <div className="section-title">
        {t("applications.title")} ({users.length})
      </div>

      {users.length === 0 && <div className="empty-state">{t("applications.empty")}</div>}

      {users.map((u) => (
        <div className="list-item" key={u.id}>
          <div className="list-item__avatar" style={{ background: avatarGradient(u.id) }}>
            {u.photo ? <img src={u.photo} alt="" style={{ width: "100%", height: "100%", borderRadius: "50%", objectFit: "cover" }} /> : initials(u.name)}
          </div>
          <div className="list-item__body">
            <div className="list-item__title">{u.name}</div>
            <div className="list-item__sub">
              @{u.username || "—"} · {t("applications.sub")}
            </div>
          </div>
          <div className="list-item__after">
            <button
              className="btn btn--primary"
              style={{ width: "auto", padding: "8px 14px", fontSize: 14 }}
              onClick={() => {
                setSel(u);
                setView("role");
              }}
            >
              {t("applications.approve")}
            </button>
          </div>
        </div>
      ))}

      {sel && view === "role" && (
        <Sheet
          title={t("applications.approveTitle")}
          subtitle={sel.name}
          onClose={() => {
            setView(null);
            setSel(null);
          }}
        >
          <ActionRow icon="👑" label={t("role.boss")} onClick={() => { setChosenRole("boss"); setView("dep"); }} />
          <ActionRow icon="👤" label={t("role.worker")} onClick={() => { setChosenRole("worker"); setView("dep"); }} />
          <ActionRow icon="👁" label={t("role.observer")} onClick={() => { setChosenRole("observer"); approve("observer", null); }} />
        </Sheet>
      )}

      {sel && view === "dep" && chosenRole && (
        <Sheet title={t("applications.chooseDept")} subtitle={sel.name} onClose={() => setView("role")}>
          <ActionRow icon="—" label={t("users.noDept")} onClick={() => approve(chosenRole, null)} />
          {deps.map((d: Department) => (
            <ActionRow key={d.id} icon={d.emoji} label={d.name} onClick={() => approve(chosenRole, d.id)} />
          ))}
        </Sheet>
      )}
    </div>
  );
}
