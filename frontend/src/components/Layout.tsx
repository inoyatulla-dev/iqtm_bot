import { Tabbar } from "@telegram-apps/telegram-ui";
import type { ReactNode } from "react";

export type Tab = "board" | "users" | "departments" | "stats";

interface Props {
  tab: Tab;
  onTab: (t: Tab) => void;
  isBoss: boolean;
  children: ReactNode;
}

export function Layout({ tab, onTab, isBoss, children }: Props) {
  const tabs: { id: Tab; text: string; icon: string }[] = [
    { id: "board", text: "Doska", icon: "📋" },
    ...(isBoss
      ? ([
          { id: "users", text: "Xodimlar", icon: "👥" },
          { id: "departments", text: "Bo'limlar", icon: "🏢" },
        ] as const)
      : []),
    { id: "stats", text: "Statistika", icon: "📊" },
  ];

  return (
    <div className="app-shell">
      <div className="app-content">{children}</div>
      <Tabbar>
        {tabs.map((t) => (
          <Tabbar.Item
            key={t.id}
            text={t.text}
            selected={tab === t.id}
            onClick={() => onTab(t.id)}
          >
            <span style={{ fontSize: 22 }}>{t.icon}</span>
          </Tabbar.Item>
        ))}
      </Tabbar>
    </div>
  );
}
