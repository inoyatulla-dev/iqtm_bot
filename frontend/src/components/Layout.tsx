import type { ReactNode } from "react";
import type { User } from "../api/types";
import { useI18n } from "../i18n";
import { Logo } from "./Logo";

export type Tab = "board" | "users" | "departments" | "stats" | "settings";

interface Props {
  tab: Tab;
  onTab: (t: Tab) => void;
  user: User;
  children: ReactNode;
}

export function Layout({ tab, onTab, user, children }: Props) {
  const { t } = useI18n();
  const isBoss = user.role === "boss";
  const tabs: { id: Tab; text: string; icon: string }[] = [
    { id: "board", text: t("tabs.board"), icon: "📋" },
    ...(isBoss
      ? ([
          { id: "users", text: t("tabs.users"), icon: "👥" },
          { id: "departments", text: t("tabs.departments"), icon: "🏢" },
        ] as const)
      : []),
    { id: "stats", text: t("tabs.stats"), icon: "📊" },
    { id: "settings", text: t("tabs.settings"), icon: "⚙️" },
  ];

  return (
    <div className="app-shell">
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

      <nav className="tabbar">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tabbar__item${tab === t.id ? " active" : ""}`}
            onClick={() => onTab(t.id)}
          >
            <span className="tabbar__icon">{t.icon}</span>
            <span className="tabbar__text">{t.text}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
