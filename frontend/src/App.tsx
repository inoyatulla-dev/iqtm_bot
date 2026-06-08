import { useState } from "react";
import { Spinner, Placeholder, Button } from "@telegram-apps/telegram-ui";
import { useAuth } from "./store/auth";
import { Layout, type Tab } from "./components/Layout";
import { BoardPage } from "./pages/BoardPage";
import { UsersPage } from "./pages/UsersPage";
import { DepartmentsPage } from "./pages/DepartmentsPage";
import { StatsPage } from "./pages/StatsPage";

export function App() {
  const { user, loading, error } = useAuth();
  const [tab, setTab] = useState<Tab>("board");

  if (loading) {
    return (
      <div className="center-screen">
        <Spinner size="l" />
        <div>Yuklanmoqda…</div>
      </div>
    );
  }

  if (error) {
    return (
      <Placeholder header="Xatolik" description={error}>
        <Button onClick={() => location.reload()}>Qayta urinish</Button>
      </Placeholder>
    );
  }

  if (!user || user.status === "pending") {
    return (
      <Placeholder
        header="⏳ Ariza ko'rib chiqilmoqda"
        description="Boshliq tasdiqlagunicha kuting. Tasdiqlangач, ilovani qayta oching."
      />
    );
  }

  if (user.status === "blocked") {
    return <Placeholder header="🚫 Bloklangan" description="Kirishingiz cheklangan." />;
  }

  return (
    <Layout tab={tab} onTab={setTab} isBoss={user.role === "boss"}>
      {tab === "board" && <BoardPage />}
      {tab === "users" && <UsersPage />}
      {tab === "departments" && <DepartmentsPage />}
      {tab === "stats" && <StatsPage />}
    </Layout>
  );
}
