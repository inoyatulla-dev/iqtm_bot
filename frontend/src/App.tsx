import { useCallback, useEffect, useState } from "react";
import { usersApi } from "./api/client";
import { useAuth } from "./store/auth";
import { useI18n } from "./i18n";
import { Layout, type Tab } from "./components/Layout";
import { BoardPage } from "./pages/BoardPage";
import { ArizalarPage } from "./pages/ArizalarPage";
import { UsersPage } from "./pages/UsersPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import { MonitoringPage } from "./pages/MonitoringPage";
import { StatsPage } from "./pages/StatsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { RegisterForm } from "./pages/RegisterForm";
import { Logo } from "./components/Logo";

export function App() {
  const { user, loading, error, isBoss } = useAuth();
  const { t } = useI18n();
  const [tab, setTab] = useState<Tab>("board");
  const [pendingCount, setPendingCount] = useState(0);

  const refreshPending = useCallback(() => {
    if (isBoss) {
      usersApi.list("pending").then((arr) => setPendingCount(arr.length));
    }
  }, [isBoss]);

  useEffect(() => {
    refreshPending();
  }, [refreshPending]);

  if (loading) {
    return (
      <div className="center-screen">
        <Logo />
        <div style={{ color: "var(--hint)" }}>{t("common.loading")}</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="center-screen">
        <h3>{t("common.error")}</h3>
        <p style={{ color: "var(--hint)" }}>{error}</p>
        <button className="btn btn--primary" onClick={() => location.reload()} style={{ maxWidth: 200 }}>
          {t("common.retry")}
        </button>
      </div>
    );
  }

  if (!user || user.status === "pending") {
    return <RegisterForm />;
  }

  if (user.status === "blocked") {
    return (
      <div className="center-screen">
        <h3>{t("blocked.title")}</h3>
        <p style={{ color: "var(--hint)" }}>{t("blocked.msg")}</p>
      </div>
    );
  }

  return (
    <Layout tab={tab} onTab={setTab} user={user} pendingCount={pendingCount}>
      {tab === "board" && <BoardPage />}
      {tab === "applications" && <ArizalarPage onChange={refreshPending} />}
      {tab === "users" && <UsersPage />}
      {tab === "projects" && <ProjectsPage />}
      {tab === "monitoring" && <MonitoringPage />}
      {tab === "stats" && <StatsPage />}
      {tab === "settings" && <SettingsPage />}
    </Layout>
  );
}
