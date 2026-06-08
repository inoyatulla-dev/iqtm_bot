import { useEffect, useState } from "react";
import { depsApi, settingsApi, type AppSettings } from "../api/client";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";

export function SettingsPage() {
  const { deps, reload } = useAuth();
  const { t, lang, setLang } = useI18n();
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

  if (loading || !s) return <div className="center-screen">{t("common.loading")}</div>;

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
      {/* Til */}
      <div className="section-title">{t("settings.language")}</div>
      <div className="sheet__pad">
        <div style={{ display: "flex", gap: 8 }}>
          {LANGS.map((l) => (
            <button
              key={l.code}
              onClick={() => setLang(l.code as Lang)}
              className={`btn ${lang === l.code ? "btn--primary" : "btn--ghost"}`}
              style={{ fontSize: 14 }}
            >
              {l.flag} {l.label}
            </button>
          ))}
        </div>
      </div>

      <div className="section-title">{t("settings.group")}</div>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("settings.groupId")}</label>
          <input
            value={s.group_chat_id}
            placeholder="-1001234567890"
            onChange={(e) => setS({ ...s, group_chat_id: e.target.value })}
          />
        </div>
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>{t("settings.groupHint")}</p>
      </div>

      <div className="section-title">{t("settings.topics")}</div>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("settings.topicTasks")}</label>
          <input
            value={s.topic_tasks}
            placeholder="5"
            onChange={(e) => setS({ ...s, topic_tasks: e.target.value })}
          />
        </div>
        <div className="field">
          <label>{t("settings.topicReports")}</label>
          <input
            value={s.topic_reports}
            placeholder="8"
            onChange={(e) => setS({ ...s, topic_reports: e.target.value })}
          />
        </div>
        <button className="btn btn--primary" onClick={saveGroup}>
          {saved ? t("common.saved") : t("common.save")}
        </button>
      </div>

      <div className="section-title">{t("settings.deptTopics")}</div>
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
          {saved ? t("common.saved") : t("settings.deptTopicsSave")}
        </button>
      </div>

      <div className="section-title">{t("settings.admins")}</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>{t("settings.adminsHint")}</p>
      </div>
    </div>
  );
}
