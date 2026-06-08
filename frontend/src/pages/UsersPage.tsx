import { useEffect, useState } from "react";
import {
  Section, Cell, Button, Spinner, Badge,
} from "@telegram-apps/telegram-ui";
import { usersApi } from "../api/client";
import type { User } from "../api/types";
import { ROLE_LABEL } from "../api/types";
import { useAuth } from "../store/auth";

export function UsersPage() {
  const { deps } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setUsers(await usersApi.list());
    setLoading(false);
  }
  useEffect(() => {
    load();
  }, []);

  if (loading) return <div className="center-screen"><Spinner size="l" /></div>;

  const pending = users.filter((u) => u.status === "pending");
  const active = users.filter((u) => u.status !== "pending");

  const depName = (id: string | null) =>
    deps.find((d) => d.id === id)?.name || "—";

  return (
    <div style={{ paddingBottom: 80 }}>
      {pending.length > 0 && (
        <Section header="🔔 Yangi arizalar">
          {pending.map((u) => (
            <Cell
              key={u.id}
              subtitle={`@${u.username || "—"} · ${u.id}`}
              after={
                <Button
                  size="s"
                  onClick={async () => {
                    await usersApi.approve(u.id, "worker");
                    load();
                  }}
                >
                  Tasdiqlash
                </Button>
              }
            >
              {u.name}
            </Cell>
          ))}
        </Section>
      )}

      <Section header={`👥 Xodimlar (${active.length})`}>
        {active.map((u) => (
          <Cell
            key={u.id}
            subtitle={`${ROLE_LABEL[u.role]} · ${depName(u.dep_id)}`}
            after={
              u.status === "blocked" ? <Badge type="number">blok</Badge> : null
            }
            onClick={() => editUser(u, deps, load)}
          >
            {u.name}
          </Cell>
        ))}
      </Section>
    </div>
  );
}

// Oddiy prompt-asosli tahrir (keyinchalik modalga o'tkazsa bo'ladi)
async function editUser(
  u: User,
  deps: { id: string; name: string }[],
  reload: () => void
) {
  const action = prompt(
    `${u.name}\n\n1 — Rol o'zgartirish\n2 — Bo'lim biriktirish\n3 — ${
      u.status === "blocked" ? "Blokdan chiqarish" : "Bloklash"
    }\n4 — O'chirish\n\nRaqam kiriting:`
  );
  if (!action) return;
  try {
    if (action === "1") {
      const role = u.role === "boss" ? "worker" : "boss";
      if (confirm(`Rol → ${role}?`)) await usersApi.update(u.id, { role });
    } else if (action === "2") {
      const list = deps.map((d) => `${d.id} — ${d.name}`).join("\n");
      const depId = prompt(`Bo'lim kodi:\n${list}`);
      if (depId) await usersApi.update(u.id, { dep_id: depId });
    } else if (action === "3") {
      await usersApi.update(u.id, {
        status: u.status === "blocked" ? "active" : "blocked",
      });
    } else if (action === "4") {
      if (confirm("O'chirilsinmi?")) await usersApi.remove(u.id);
    }
    reload();
  } catch (e: any) {
    alert(e?.response?.data?.detail || "Xatolik");
  }
}
