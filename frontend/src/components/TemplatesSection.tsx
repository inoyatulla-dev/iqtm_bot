import { useEffect, useRef, useState } from "react";
import { settingsApi, topicsApi, type AppSettings } from "../api/client";
import type { Topic } from "../api/types";
import { useI18n } from "../i18n";

const TEMPLATE_EVENTS = [
  "new_task", "status_change", "done", "overdue", "weekly", "reminder", "application", "birthday",
] as const;
type TemplateEvent = (typeof TEMPLATE_EVENTS)[number];

const TEMPLATE_VARS: Record<TemplateEvent, string[]> = {
  new_task: ["id", "department", "name", "assignee", "deadline", "description"],
  status_change: ["id", "department", "name", "status", "actor"],
  done: ["id", "department", "name", "assignee", "creator", "checker", "comment"],
  overdue: ["date", "count"],
  weekly: ["date", "total", "done", "percent"],
  reminder: ["id", "name", "deadline"],
  application: ["name", "id", "username"],
  birthday: ["name"],
};

const PREVIEW_VALUES: Record<string, string> = {
  id: "123",
  department: "IT bo'limi",
  name: "Sayt dizaynini tayyorlash",
  assignee: "Aziz Aliyev (@aziz)",
  deadline: "25.06.2026 18:00",
  description: "Bosh sahifa uchun yangi banner tayyorlash",
  status: "🔄 Jarayonda",
  actor: "Aziz Aliyev",
  creator: "Bobur Karimov",
  checker: "Bobur Karimov",
  comment: "Yaxshi ishladingiz!",
  date: "13.06.2026",
  count: "3",
  total: "20",
  done: "15",
  percent: "75",
  username: "aziz",
};

function renderPreview(tpl: string): string {
  return tpl.replace(/\{(\w+)\}/g, (m, key) => PREVIEW_VALUES[key] ?? m);
}

export function TemplatesSection() {
  const { t } = useI18n();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [templates, setTemplates] = useState<Record<string, string>>({});
  const [routes, setRoutes] = useState<Record<string, number | null>>({});
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<TemplateEvent | null>(null);
  const [saved, setSaved] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    Promise.all([settingsApi.get(), topicsApi.list()]).then(([s, tp]) => {
      setTemplates(s.templates || {});
      setRoutes(s.routes || {});
      setTopics(tp);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

  function insertVar(v: string) {
    const ta = textareaRef.current;
    const ev = editing;
    if (!ta || !ev) return;
    const start = ta.selectionStart;
    const end = ta.selectionEnd;
    const cur = templates[ev] || "";
    const next = cur.slice(0, start) + `{${v}}` + cur.slice(end);
    setTemplates({ ...templates, [ev]: next });
    requestAnimationFrame(() => {
      ta.focus();
      const pos = start + v.length + 2;
      ta.setSelectionRange(pos, pos);
    });
  }

  async function save() {
    await settingsApi.update({ templates, routes });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  async function resetDefault() {
    if (!editing) return;
    const ev = editing;
    await settingsApi.update({ templates: { [ev]: "" } });
    const fresh = await settingsApi.get();
    setTemplates(fresh.templates || {});
  }

  if (editing) {
    const ev = editing;
    return (
      <>
        <div className="section-title">{t(`settings.topics.event.${ev}`)}</div>
        <div className="sheet__pad">
          <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 0 12px" }}>
            {t(`settings.templates.desc.${ev}`)}
          </p>
          <div className="field">
            <label>{t("settings.templates.text")}</label>
            <textarea
              ref={textareaRef}
              rows={6}
              value={templates[ev] ?? ""}
              onChange={(e) => setTemplates({ ...templates, [ev]: e.target.value })}
            />
          </div>
          <div className="field">
            <label>{t("settings.templates.vars")}</label>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {TEMPLATE_VARS[ev].map((v) => (
                <button
                  key={v}
                  className="btn btn--ghost"
                  style={{ width: "auto", padding: "4px 10px", fontSize: 12 }}
                  onClick={() => insertVar(v)}
                >
                  {`{${v}}`}
                </button>
              ))}
            </div>
          </div>
          <div className="field">
            <label>{t("settings.templates.topic")}</label>
            <select
              value={routes[ev] != null ? String(routes[ev]) : ""}
              onChange={(e) =>
                setRoutes({ ...routes, [ev]: e.target.value ? Number(e.target.value) : null })
              }
            >
              <option value="">{t("settings.topics.routeDefault")}</option>
              {topics.map((tp) => (
                <option key={tp.id} value={tp.topic_id}>
                  {tp.name} (#{tp.topic_id})
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>{t("settings.templates.preview")}</label>
            <div
              style={{
                whiteSpace: "pre-wrap",
                background: "var(--secondary-bg)",
                border: "1px solid var(--line)",
                borderRadius: 12,
                padding: 12,
                fontSize: 14,
              }}
            >
              {renderPreview(templates[ev] ?? "")}
            </div>
          </div>

          <button className="btn btn--ghost" onClick={resetDefault}>
            {t("settings.templates.reset")}
          </button>
          <button className="btn btn--primary" onClick={save}>
            {saved ? t("common.saved") : t("common.save")}
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      {TEMPLATE_EVENTS.map((ev) => (
        <div className="list-item" key={ev} onClick={() => setEditing(ev)}>
          <div className="list-item__body">
            <div className="list-item__title">{t(`settings.topics.event.${ev}`)}</div>
            <div className="list-item__sub">{t(`settings.templates.desc.${ev}`)}</div>
          </div>
          <span className="list-item__after">›</span>
        </div>
      ))}
    </>
  );
}
