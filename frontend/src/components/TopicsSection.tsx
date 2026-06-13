import { useEffect, useState } from "react";
import { topicsApi } from "../api/client";
import type { Topic } from "../api/types";
import { useI18n } from "../i18n";
import { Sheet } from "./Sheet";

export function TopicsSection() {
  const { t } = useI18n();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [edit, setEdit] = useState<Topic | null>(null);
  const [creating, setCreating] = useState(false);

  async function load() {
    setTopics(await topicsApi.list());
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <div className="center-screen">{t("common.loading")}</div>;

  return (
    <>
      <div className="sheet__pad" style={{ paddingTop: 16 }}>
        <p style={{ color: "var(--hint)", fontSize: 13, margin: "0 0 12px" }}>
          {t("settings.topics.hint")}
        </p>
        <button className="btn btn--primary" onClick={() => setCreating(true)}>
          {t("settings.topics.add")}
        </button>
      </div>

      {topics.length === 0 ? (
        <div className="empty-state">{t("settings.topics.empty")}</div>
      ) : (
        topics.map((tp) => (
          <div className="list-item" key={tp.id} onClick={() => setEdit(tp)}>
            <div className="list-item__body">
              <div className="list-item__title">{tp.name}</div>
              <div className="list-item__sub">#{tp.topic_id}</div>
            </div>
            <span className="list-item__after">›</span>
          </div>
        ))
      )}

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
  const [err, setErr] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);

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
          <input value={topicId} onChange={(e) => setTopicId(e.target.value)} inputMode="numeric" />
          <p style={{ color: "var(--hint)", fontSize: 12, margin: "6px 0 0" }}>
            {t("settings.topics.topicIdHint")}
          </p>
        </div>

        {err && <div className="form-error">{err}</div>}

        <button className="btn btn--primary" onClick={save}>
          {t("common.save")}
        </button>
        {topic && (
          confirmDelete ? (
            <button className="btn btn--danger" onClick={remove}>
              {t("settings.topics.confirmDelete")}
            </button>
          ) : (
            <button className="btn btn--danger" onClick={() => setConfirmDelete(true)}>
              🗑 {t("settings.topics.delete")}
            </button>
          )
        )}
      </div>
    </Sheet>
  );
}
