import { useEffect, useState } from "react";
import { settingsApi } from "../api/client";
import type { AppSettings } from "../api/client";
import { useI18n } from "../i18n";

const ROUTE_EVENTS = [
  "new_task", "status_change", "done", "overdue", "weekly", "reminder", "application", "birthday",
] as const;

export function TopicsSection() {
  const { t } = useI18n();
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    settingsApi.get().then((s) => {
      setSettings(s);
      setInputs(
        Object.fromEntries(
          ROUTE_EVENTS.map((ev) => [ev, s.routes[ev] != null ? String(s.routes[ev]) : ""])
        )
      );
      setLoading(false);
    });
  }, []);

  if (loading || !settings) return null;

  async function save() {
    const routes: Record<string, number | null> = {};
    for (const ev of ROUTE_EVENTS) {
      const v = inputs[ev].trim();
      routes[ev] = v && /^\d+$/.test(v) ? Number(v) : null;
    }
    await settingsApi.update({ routes });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  return (
    <>
      <div className="section-title">{t("settings.topics.routing")}</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 0 12px" }}>
          {t("settings.topics.routingHint")}
        </p>
        {ROUTE_EVENTS.map((ev) => (
          <div className="field" key={ev}>
            <label>{t(`settings.topics.event.${ev}`)}</label>
            <input
              type="number"
              placeholder="topic ID"
              value={inputs[ev]}
              onChange={(e) => setInputs({ ...inputs, [ev]: e.target.value })}
            />
          </div>
        ))}
        <button className="btn btn--primary" onClick={save}>
          {saved ? t("common.saved") : t("common.save")}
        </button>
      </div>
    </>
  );
}
