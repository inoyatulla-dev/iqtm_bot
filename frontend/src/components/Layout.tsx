import type { ReactNode } from "react";
import { BarChart3, FolderKanban, Inbox, LayoutGrid, Settings, TrendingUp, Users } from "lucide-react";
import type { User } from "../api/types";
import { useI18n } from "../i18n";
import { Logo } from "./Logo";
import { NotificationBell } from "./NotificationBell";

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
  onOpenTask: (taskId: number) => void;
  children: ReactNode;
}

export function Layout({ tab, onTab, user, pendingCount, onOpenTask, children }: Props) {
  const { t } = useI18n();
  const isBoss = user.role === "boss";
  const isObserver = user.role === "observer";
  const tabs: { id: Tab; text: string; icon: ReactNode; badge?: number }[] = [
    { id: "board", text: t("tabs.board"), icon: <LayoutGrid size={20} /> },
    ...(isBoss
      ? [{ id: "applications" as Tab, text: t("tabs.applications"), icon: <Inbox size={20} />, badge: pendingCount }]
      : []),
    ...(!isObserver ? [{ id: "users" as Tab, text: t("tabs.users"), icon: <Users size={20} /> }] : []),
    { id: "projects", text: t("tabs.projects"), icon: <FolderKanban size={20} /> },
    ...(isBoss || isObserver ? [{ id: "monitoring" as Tab, text: t("tabs.monitoring"), icon: <BarChart3 size={20} /> }] : []),
    ...(!isObserver ? [{ id: "stats" as Tab, text: t("tabs.stats"), icon: <TrendingUp size={20} /> }] : []),
    { id: "settings", text: t("tabs.settings"), icon: <Settings size={20} /> },
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
          <div className="app-header__right">
            <NotificationBell onOpenTask={onOpenTask} />
            <div className="app-header__user">
              <div className="name">{user.name}</div>
              <div className="role">{t(`role.${user.role}`)}</div>
            </div>
          </div>
        </header>
        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}
