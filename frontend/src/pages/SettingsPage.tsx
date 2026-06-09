import { useEffect, useState } from "react";
import { depsApi, settingsApi, updateProfile, type AppSettings } from "../api/client";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";
import { BoardColumnsSection } from "../components/BoardColumnsSection";
import { TopicsSection } from "../components/TopicsSection";

function splitName(name?: string): [string, string] {
  if (!name) return ["", ""];
  const [first, ...rest] = name.trim().split(/\s+/);
  return [first || "", rest.join(" ")];
}

export function SettingsPage() {
  const { deps, isBoss, reload } = useAuth();
  const { t, lang, setLang } = useI18n();

  return (
    <div className="page-content">
      <ProfileSection />

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

      {isBoss && <AdminSection deps={deps} reload={reload} />}
    </div>
  );
}

function ProfileSection() {
  const { user, reload } = useAuth();
  const { t } = useI18n();
  const [first0, last0] = splitName(user?.name);
  const [firstName, setFirstName] = useState(first0);
  const [lastName, setLastName] = useState(last0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const [f, l] = splitName(user?.name);
    setFirstName(f);
    setLastName(l);
  }, [user?.name]);

  async function save() {
    if (firstName.trim().length < 1) {
      setErr(t("register.nameErr"));
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await updateProfile(firstName.trim(), lastName.trim());
      await reload();
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="section-title">{t("settings.profile")}</div>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("register.firstName")}</label>
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("register.lastName")}</label>
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
        {err && <div className="form-error">{err}</div>}
        <button className="btn btn--primary" onClick={save} disabled={saving}>
          {saved ? t("settings.profileSaved") : t("common.save")}
        </button>
      </div>
    </>
  );
}

function AdminSection({
  deps,
  reload,
}: {
  deps: ReturnType<typeof useAuth>["deps"];
  reload: () => void;
}) {
  const { t } = useI18n();
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
    await settingsApi.update({ group_chat_id: s!.group_chat_id });
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
    <>
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
        <button className="btn btn--primary" onClick={saveGroup}>
          {saved ? t("common.saved") : t("common.save")}
        </button>
      </div>

      <TopicsSection />

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

      <BoardColumnsSection />

      <div className="section-title">{t("settings.admins")}</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>{t("settings.adminsHint")}</p>
      </div>
    </>
  );
}
