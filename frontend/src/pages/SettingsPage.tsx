import { useEffect, useState } from "react";
import { depsApi, settingsApi, type AppSettings } from "../api/client";
import { useAuth } from "../store/auth";

export function SettingsPage() {
  const { deps, reload } = useAuth();
  const [s, setS] = useState<AppSettings | null>(null);
  const [depTopics, setDepTopics] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    settingsApi.get().then((data) => {
      setS(data);
      setLoading(false);
    });
    setDepTopics(
      Object.fromEntries(deps.map((d) => [d.id, d.topic_id ? String(d.topic_id) : ""]))
    );
  }, [deps]);

  if (loading || !s) return <div className="center-screen">Yuklanmoqda…</div>;

  async function saveGroup() {
    await settingsApi.update({
      group_chat_id: s!.group_chat_id,
      topic_tasks: s!.topic_tasks,
      topic_reports: s!.topic_reports,
    });
    flash();
  }

  async function saveDepTopics() {
    for (const d of deps) {
      const v = depTopics[d.id];
      const topic_id = v ? Number(v) : null;
      if ((d.topic_id || null) !== topic_id) {
        await depsApi.update(d.id, { topic_id });
      }
    }
    await reload();
    flash();
  }

  function flash() {
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <div style={{ paddingBottom: 90 }}>
      <div className="section-title">📡 Guruh</div>
      <div className="sheet__pad">
        <div className="field">
          <label>Guruh chat ID (manfiy, -100…)</label>
          <input
            value={s.group_chat_id}
            placeholder="-1001234567890"
            onChange={(e) => setS({ ...s, group_chat_id: e.target.value })}
          />
        </div>
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>
          💡 Guruhga botni admin qiling va guruhda <b>/set_group</b> yuboring — ID avtomatik
          aniqlanadi.
        </p>
      </div>

      <div className="section-title">🧵 Umumiy mavzular (topic ID)</div>
      <div className="sheet__pad">
        <div className="field">
          <label>📋 Vazifalar mavzusi</label>
          <input
            value={s.topic_tasks}
            placeholder="masalan: 5"
            onChange={(e) => setS({ ...s, topic_tasks: e.target.value })}
          />
        </div>
        <div className="field">
          <label>📊 Hisobotlar mavzusi</label>
          <input
            value={s.topic_reports}
            placeholder="masalan: 8"
            onChange={(e) => setS({ ...s, topic_reports: e.target.value })}
          />
        </div>
        <button className="btn btn--primary" onClick={saveGroup}>
          {saved ? "✅ Saqlandi" : "Saqlash"}
        </button>
      </div>

      <div className="section-title">🏢 Bo'lim mavzulari</div>
      <div className="sheet__pad">
        {deps.map((d) => (
          <div className="field" key={d.id}>
            <label>
              {d.emoji} {d.name}
            </label>
            <input
              value={depTopics[d.id] ?? ""}
              placeholder="topic ID"
              onChange={(e) => setDepTopics({ ...depTopics, [d.id]: e.target.value })}
            />
          </div>
        ))}
        <button className="btn btn--primary" onClick={saveDepTopics}>
          {saved ? "✅ Saqlandi" : "Bo'lim mavzularini saqlash"}
        </button>
      </div>

      <div className="section-title">👑 Adminlar</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>
          Bir nechta admin bo'lishi mumkin. Xodimlar bo'limida xodimni tanlab{" "}
          <b>"Admin qilish"</b> orqali yangi admin tayinlang.
        </p>
      </div>
    </div>
  );
}
