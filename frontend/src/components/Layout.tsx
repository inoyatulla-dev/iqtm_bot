import type { ReactNode } from "react";
import type { User } from "../api/types";
import { useI18n } from "../i18n";
import { Logo } from "./Logo";

export type Tab =
  | "board"
  | "applications"
  | "users"
  | "projects"
  | "monitoring"
  | "stats"
  | "settings";

interface Props {
  tab: Tab;
  onTab: (t: Tab) => void;
  user: User;
  pendingCount?: number;
  children: ReactNode;
}

export function Layout({ tab, onTab, user, pendingCount, children }: Props) {
  const { t } = useI18n();
  const isBoss = user.role === "boss";
  const isObserver = user.role === "observer";
  const tabs: { id: Tab; text: string; icon: string; badge?: number }[] = [
    { id: "board", text: t("tabs.board"), icon: "📋" },
    ...(isBoss
      ? [{ id: "applications" as Tab, text: t("tabs.applications"), icon: "📥", badge: pendingCount }]
      : []),
    ...(!isObserver ? [{ id: "users" as Tab, text: t("tabs.users"), icon: "👥" }] : []),
    { id: "projects", text: t("tabs.projects"), icon: "🗂" },
    ...(isBoss || isObserver ? [{ id: "monitoring" as Tab, text: t("tabs.monitoring"), icon: "📊" }] : []),
    ...(!isObserver ? [{ id: "stats" as Tab, text: t("tabs.stats"), icon: "📈" }] : []),
    { id: "settings", text: t("tabs.settings"), icon: "⚙️" },
  ];

  return (
    <div className="app-shell">
      {/* Sidebar (desktop) / Bottom tabbar (mobile) */}
      <nav className="tabbar">
        <div className="tabbar__brand">
          <Logo />
          <span className="tabbar__brand-name">IQTM</span>
        </div>
        {tabs.map((tb) => (
          <button
            key={tb.id}
            className={`tabbar__item${tab === tb.id ? " active" : ""}`}
            onClick={() => onTab(tb.id)}
          >
            <span className="tabbar__icon">{tb.icon}</span>
            <span className="tabbar__text">{tb.text}</span>
            {!!tb.badge && <span className="tabbar__badge">{tb.badge}</span>}
          </button>
        ))}
      </nav>

      {/* Main: header + content */}
      <div className="app-main">
        <header className="app-header">
          <div className="app-header__brand">
            <Logo />
          </div>
          <div className="app-header__user">
            <div className="name">{user.name}</div>
            <div className="role">{t(`role.${user.role}`)}</div>
          </div>
        </header>
        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}
