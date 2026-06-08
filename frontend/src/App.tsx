import { useState } from "react";
import { useAuth } from "./store/auth";
import { Layout, type Tab } from "./components/Layout";
import { BoardPage } from "./pages/BoardPage";
import { UsersPage } from "./pages/UsersPage";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { StatsPage } from "./pages/StatsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { RegisterForm } from "./pages/RegisterForm";
import { Logo } from "./components/Logo";

export function App() {
  const { user, loading, error } = useAuth();
  const [tab, setTab] = useState<Tab>("board");

  if (loading) {
    return (
      <div className="center-screen">
        <Logo />
        <div style={{ color: "var(--hint)" }}>Yuklanmoqda…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="center-screen">
        <h3>Xatolik</h3>
        <p style={{ color: "var(--hint)" }}>{error}</p>
        <button className="btn btn--primary" onClick={() => location.reload()} style={{ maxWidth: 200 }}>
          Qayta urinish
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
        <h3>🚫 Bloklangan</h3>
        <p style={{ color: "var(--hint)" }}>Kirishingiz cheklangan.</p>
      </div>
    );
  }

  return (
    <Layout tab={tab} onTab={setTab} user={user}>
      {tab === "board" && <BoardPage />}
      {tab === "users" && <UsersPage />}
      {tab === "departments" && <DepartmentsPage />}
      {tab === "stats" && <StatsPage />}
      {tab === "settings" && <SettingsPage />}
    </Layout>
  );
}
