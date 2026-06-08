import { useState } from "react";
import { Section, Cell, Button } from "@telegram-apps/telegram-ui";
import { depsApi } from "../api/client";
import { useAuth } from "../store/auth";

export function DepartmentsPage() {
  const { deps, reload } = useAuth();
  const [busy, setBusy] = useState(false);

  async function add() {
    const id = prompt("Bo'lim kodi (masalan: it):")?.trim();
    if (!id) return;
    const name = prompt("Bo'lim nomi:")?.trim();
    if (!name) return;
    const emoji = prompt("Emoji:", "🏢")?.trim() || "🏢";
    setBusy(true);
    try {
      await depsApi.create({ id, name, emoji });
      reload();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function edit(id: string, name: string) {
    const action = prompt(`${name}\n\n1 — Nomini o'zgartirish\n2 — O'chirish`);
    try {
      if (action === "1") {
        const newName = prompt("Yangi nom:", name)?.trim();
        if (newName) await depsApi.update(id, { name: newName });
      } else if (action === "2") {
        if (confirm("O'chirilsinmi?")) await depsApi.remove(id);
      }
      reload();
    } catch (e: any) {
      alert(e?.response?.data?.detail || "Xatolik");
    }
  }

  return (
    <div style={{ paddingBottom: 80 }}>
      <Section header={`🏢 Bo'limlar (${deps.length})`}>
        {deps.map((d) => (
          <Cell
            key={d.id}
            subtitle={`kod: ${d.id}`}
            before={<span style={{ fontSize: 22 }}>{d.emoji}</span>}
            onClick={() => edit(d.id, d.name)}
          >
            {d.name}
          </Cell>
        ))}
      </Section>
      <div style={{ padding: 16 }}>
        <Button stretched onClick={add} loading={busy}>
          ➕ Bo'lim qo'shish
        </Button>
      </div>
    </div>
  );
}
