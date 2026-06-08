import { useEffect, useState } from "react";
import { settingsApi, topicsApi, type AppSettings } from "../api/client";
import type { Topic } from "../api/types";
import { useI18n } from "../i18n";
import { Sheet } from "./Sheet";

const ROUTE_EVENTS = [
  "new_task", "status_change", "done", "overdue", "weekly", "reminder", "application",
] as const;

export function TopicsSection() {
  const { t } = useI18n();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [edit, setEdit] = useState<Topic | null>(null);
  const [creating, setCreating] = useState(false);
  const [saved, setSaved] = useState(false);

  async function load() {
    const [tp, s] = await Promise.all([topicsApi.list(), settingsApi.get()]);
    setTopics(tp);
    setSettings(s);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  if (loading || !settings) return <div className="center-screen">{t("common.loading")}</div>;

  async function setRoute(event: string, topicPk: number | null) {
    const prev = settings!;
    setSettings({ ...prev, routes: { ...prev.routes, [event]: topicPk } });
    try {
      await settingsApi.update({ routes: { [event]: topicPk } });
      setSaved(true);
      setTimeout(() => setSaved(false), 1200);
    } catch {
      setSettings(prev);
    }
  }

  return (
    <>
      <div className="section-title">{t("settings.topics.title")}</div>
      <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 16px 8px" }}>
        {t("settings.topics.hint")}
      </p>
      {topics.length === 0 && (
        <div className="sheet__pad">
          <div className="comment-empty">{t("settings.topics.empty")}</div>
        </div>
      )}
      {topics.map((tp) => (
        <div className="list-item" key={tp.id} onClick={() => setEdit(tp)}>
          <span style={{ fontSize: 24 }}>🧵</span>
          <div className="list-item__body">
            <div className="list-item__title">{tp.name}</div>
            <div className="list-item__sub">ID: {tp.topic_id}</div>
          </div>
        </div>
      ))}
      <div className="sheet__pad">
        <button className="btn btn--primary" onClick={() => setCreating(true)}>
          {t("settings.topics.add")}
        </button>
      </div>

      <div className="section-title">{t("settings.topics.routing")}</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 0 12px" }}>
          {t("settings.topics.routingHint")}
        </p>
        {ROUTE_EVENTS.map((ev) => (
          <div className="field" key={ev}>
            <label>{t(`settings.topics.event.${ev}`)}</label>
            <select
              value={settings.routes[ev] ?? ""}
              onChange={(e) => setRoute(ev, e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">{t("settings.topics.routeDefault")}</option>
              {topics.map((tp) => (
                <option key={tp.id} value={tp.id}>
                  {tp.name}
                </option>
              ))}
            </select>
          </div>
        ))}
        {saved && <div style={{ color: "var(--accent)", fontSize: 13 }}>{t("common.saved")}</div>}
      </div>

      {creating && (
        <TopicForm
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            load();
          }}
        />
      )}
      {edit && (
        <TopicForm
          topic={edit}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            load();
          }}
        />
      )}
    </>
  );
}

function TopicForm({
  topic,
  onClose,
  onSaved,
}: {
  topic?: Topic;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [name, setName] = useState(topic?.name || "");
  const [topicId, setTopicId] = useState(topic ? String(topic.topic_id) : "");
  const [confirmDel, setConfirmDel] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    if (name.trim().length < 2) {
      setErr(t("settings.topics.nameErr"));
      return;
    }
    if (!/^-?\d+$/.test(topicId.trim())) {
      setErr(t("settings.topics.idErr"));
      return;
    }
    try {
      const body = { name: name.trim(), topic_id: Number(topicId) };
      if (topic) await topicsApi.update(topic.id, body);
      else await topicsApi.create(body);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    }
  }

  async function remove() {
    if (!topic) return;
    try {
      await topicsApi.remove(topic.id);
      onSaved();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    }
  }

  return (
    <Sheet title={topic ? t("settings.topics.editTitle") : t("settings.topics.newTitle")} onClose={onClose}>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("settings.topics.name")}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("settings.topics.topicId")}</label>
          <input
            value={topicId}
            placeholder="5"
            onChange={(e) => setTopicId(e.target.value.replace(/[^\d-]/g, ""))}
          />
          <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>
            {t("settings.topics.topicIdHint")}
          </p>
        </div>

        {err && <div className="form-error">{err}</div>}

        <button className="btn btn--primary" onClick={save}>
          {t("common.save")}
        </button>
        {topic && !confirmDel && (
          <button className="btn btn--danger" onClick={() => setConfirmDel(true)}>
            {t("settings.topics.delete")}
          </button>
        )}
        {confirmDel && (
          <button className="btn btn--danger" onClick={remove}>
            {t("settings.topics.confirmDelete")}
          </button>
        )}
      </div>
    </Sheet>
  );
}
