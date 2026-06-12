import { useEffect, useRef, useState } from "react";
import {
  depsApi, settingsApi, updateProfile, uploadProfilePhoto, type AppSettings,
} from "../api/client";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";
import { BoardColumnsSection } from "../components/BoardColumnsSection";
import { TopicsSection } from "../components/TopicsSection";

function splitName(name?: string): [string, string] {
  if (!name) return ["", ""];
  const [first, ...rest] = name.trim().split(/\s+/);
  return [first || "", rest.join(" ")];
}

type TabKey = "profile" | "group" | "board" | "branding";

export function SettingsPage() {
  const { isBoss } = useAuth();
  const { t } = useI18n();
  const [tab, setTab] = useState<TabKey>("profile");

  const tabs: { key: TabKey; label: string }[] = [
    { key: "profile", label: t("settings.tab.profile") },
    ...(isBoss
      ? ([
          { key: "group", label: t("settings.tab.group") },
          { key: "board", label: t("settings.tab.board") },
          { key: "branding", label: t("settings.tab.branding") },
        ] as { key: TabKey; label: string }[])
      : []),
  ];

  return (
    <div className="page-content">
      <div className="settings-tabs">
        {tabs.map((tb) => (
          <button
            key={tb.key}
            className={`btn ${tab === tb.key ? "btn--primary" : "btn--ghost"}`}
            onClick={() => setTab(tb.key)}
          >
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "profile" && <ProfileTab />}
      {isBoss && tab === "group" && <GroupTab />}
      {isBoss && tab === "board" && <BoardColumnsSection />}
      {isBoss && tab === "branding" && <BrandingTab />}
    </div>
  );
}

function ProfileTab() {
  const { user, reload } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [first0, last0] = splitName(user?.name);
  const [firstName, setFirstName] = useState(first0);
  const [lastName, setLastName] = useState(last0);
  const [birthday, setBirthday] = useState(user?.birthday || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const [f, l] = splitName(user?.name);
    setFirstName(f);
    setLastName(l);
    setBirthday(user?.birthday || "");
  }, [user?.name, user?.birthday]);

  async function save() {
    if (firstName.trim().length < 1) {
      setErr(t("register.nameErr"));
      return;
    }
    setSaving(true);
    setErr("");
    try {
      await updateProfile(firstName.trim(), lastName.trim(), birthday || null);
      await reload();
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setSaving(false);
    }
  }

  async function onPhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setErr("");
    try {
      await uploadProfilePhoto(file);
      await reload();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <>
      <div className="section-title">{t("settings.profile")}</div>
      <div className="sheet__pad">
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 8 }}>
          {user?.photo ? (
            <img
              src={user.photo}
              alt=""
              style={{ width: 64, height: 64, borderRadius: "50%", objectFit: "cover" }}
            />
          ) : (
            <div className="list-item__avatar" style={{ width: 64, height: 64, fontSize: 24 }}>
              {firstName.slice(0, 1).toUpperCase()}
            </div>
          )}
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={onPhotoChange}
            />
            <button
              className="btn btn--ghost"
              style={{ width: "auto", padding: "8px 14px" }}
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? t("common.loading") : t("settings.photoUpload")}
            </button>
          </div>
        </div>
        <div className="field">
          <label>{t("register.firstName")}</label>
          <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("register.lastName")}</label>
          <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("settings.birthday")}</label>
          <input
            type="date"
            value={birthday ?? ""}
            onChange={(e) => setBirthday(e.target.value)}
          />
        </div>
        {err && <div className="form-error">{err}</div>}
        <button className="btn btn--primary" onClick={save} disabled={saving}>
          {saved ? t("settings.profileSaved") : t("common.save")}
        </button>
      </div>

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
    </>
  );
}

function GroupTab() {
  const { deps, reload } = useAuth();
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

  function flash() {
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

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
    </>
  );
}

function BrandingTab() {
  const { t } = useI18n();
  const [s, setS] = useState<AppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    settingsApi.get().then((data) => {
      setS(data);
      setLoading(false);
    });
  }, []);

  if (loading || !s) return <div className="center-screen">{t("common.loading")}</div>;

  async function saveAll() {
    await settingsApi.update({
      logo_size: s!.logo_size,
      max_file_mb: s!.max_file_mb,
      storage_limit_gb: s!.storage_limit_gb,
      archive_channel_id: s!.archive_channel_id,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  }

  async function onLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setErr("");
    try {
      const updated = await settingsApi.uploadLogo(file);
      setS(updated);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <>
      <div className="section-title">{t("settings.logo")}</div>
      <div className="sheet__pad">
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 8 }}>
          <img
            src={s.logo_path}
            alt=""
            style={{ height: s.logo_size, maxWidth: 160, objectFit: "contain" }}
          />
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={onLogoChange}
            />
            <button
              className="btn btn--ghost"
              style={{ width: "auto", padding: "8px 14px" }}
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? t("common.loading") : t("settings.logoUpload")}
            </button>
          </div>
        </div>
        <div className="field">
          <label>{t("settings.logoSize")}</label>
          <input
            type="number"
            min={16}
            max={120}
            value={s.logo_size}
            onChange={(e) => setS({ ...s, logo_size: Number(e.target.value) })}
          />
        </div>
        {err && <div className="form-error">{err}</div>}
      </div>

      <div className="section-title">{t("settings.fileLimits")}</div>
      <div className="sheet__pad">
        <div className="field">
          <label>{t("settings.maxFileMb")}</label>
          <input
            type="number"
            min={1}
            value={s.max_file_mb}
            onChange={(e) => setS({ ...s, max_file_mb: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>{t("settings.storageLimitGb")}</label>
          <input
            type="number"
            min={1}
            value={s.storage_limit_gb}
            onChange={(e) => setS({ ...s, storage_limit_gb: Number(e.target.value) })}
          />
        </div>
        <div className="field">
          <label>{t("settings.archiveChannel")}</label>
          <input
            value={s.archive_channel_id}
            placeholder="-1001234567890"
            onChange={(e) => setS({ ...s, archive_channel_id: e.target.value })}
          />
        </div>
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>
          {t("settings.archiveChannelHint")}
        </p>
        <button className="btn btn--primary" onClick={saveAll}>
          {saved ? t("common.saved") : t("common.save")}
        </button>
      </div>

      <div className="section-title">{t("settings.admins")}</div>
      <div className="sheet__pad">
        <p style={{ color: "var(--hint)", fontSize: 13, margin: 0 }}>{t("settings.adminsHint")}</p>
      </div>
    </>
  );
}
