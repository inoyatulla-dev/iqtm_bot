import { useCallback, useEffect, useState } from "react";
import { notificationsApi, tasksApi, usersApi } from "./api/client";
import type { Task } from "./api/types";
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
import { NotificationsPage } from "./pages/NotificationsPage";
import { RegisterForm } from "./pages/RegisterForm";
import { LoginPage } from "./pages/LoginPage";
import { Logo } from "./components/Logo";
import { TaskForm } from "./pages/TaskForm";

export function App() {
  const { user, loading, error, needsLogin, isBoss, isObserver } = useAuth();
  const { t } = useI18n();
  const [tab, setTab] = useState<Tab>("board");
  const [pendingCount, setPendingCount] = useState(0);
  const [notifTask, setNotifTask] = useState<Task | null>(null);
  const [unreadNotifications, setUnreadNotifications] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  async function openTaskFromNotification(taskId: number) {
    try {
      setNotifTask(await tasksApi.get(taskId));
    } catch {
      /* jim */
    }
  }

  const refreshUnreadNotifications = useCallback(() => {
    notificationsApi.unreadCount().then(setUnreadNotifications).catch(() => {});
  }, []);

  useEffect(() => {
    refreshUnreadNotifications();
    const id = setInterval(refreshUnreadNotifications, 30000);
    return () => clearInterval(id);
  }, [refreshUnreadNotifications]);

  function handleTab(newTab: Tab) {
    setShowNotifications(false);
    setTab(newTab);
  }

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

  if (needsLogin) {
    return <LoginPage />;
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
    <Layout
      tab={tab}
      onTab={handleTab}
      user={user}
      pendingCount={pendingCount}
      unreadNotifications={unreadNotifications}
      onOpenNotifications={() => setShowNotifications(true)}
    >
      {showNotifications ? (
        <NotificationsPage
          onOpenTask={openTaskFromNotification}
          onBack={() => setShowNotifications(false)}
          onChanged={refreshUnreadNotifications}
        />
      ) : (
        <>
          {tab === "board" && <BoardPage />}
          {tab === "applications" && <ArizalarPage onChange={refreshPending} />}
          {tab === "users" && <UsersPage />}
          {tab === "projects" && <ProjectsPage />}
          {tab === "monitoring" && <MonitoringPage />}
          {tab === "stats" && <StatsPage />}
          {tab === "settings" && <SettingsPage />}
        </>
      )}
      {notifTask && (
        <TaskForm
          task={notifTask}
          isBoss={isBoss}
          isObserver={isObserver}
          onClose={() => setNotifTask(null)}
          onSaved={() => setNotifTask(null)}
          onStatusChanged={(updated) => setNotifTask(updated)}
        />
      )}
    </Layout>
  );
}
