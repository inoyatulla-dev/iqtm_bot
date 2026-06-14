import { useState } from "react";
import { updateProfile } from "../api/client";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";
import { Logo } from "../components/Logo";

/** Yangi xodim /start bergach to'ldiradigan forma: Ism + Familiya + til. */
export function RegisterForm() {
  const { user, reload } = useAuth();
  const { t, lang, setLang } = useI18n();
  const parts = (user?.name || "").split(" ");
  const [first, setFirst] = useState(parts[0] || "");
  const [last, setLast] = useState(parts.slice(1).join(" ") || "");
  const appliedKey = user ? `iqtm_applied_${user.id}` : "";
  const [sent, setSent] = useState(() => !!user && localStorage.getItem(appliedKey) === "1");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit() {
    if (first.trim().length < 2) {
      setErr(t("register.nameErr"));
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await updateProfile(first.trim(), last.trim());
      if (appliedKey) localStorage.setItem(appliedKey, "1");
      setSent(true);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("common.error"));
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div className="center-screen">
        <Logo />
        <h3>{t("register.sentTitle")}</h3>
        <p style={{ color: "var(--hint)" }}>{t("register.sentMsg")}</p>
        <button className="btn btn--ghost" style={{ maxWidth: 220 }} onClick={reload}>
          {t("register.checkStatus")}
        </button>
      </div>
    );
  }

  return (
    <div className="center-screen" style={{ justifyContent: "flex-start", paddingTop: 40 }}>
      <Logo />
      {/* Til tanlash */}
      <div style={{ display: "flex", gap: 8 }}>
        {LANGS.map((l) => (
          <button
            key={l.code}
            onClick={() => setLang(l.code as Lang)}
            className={`btn ${lang === l.code ? "btn--primary" : "btn--ghost"}`}
            style={{ width: "auto", padding: "8px 12px", fontSize: 14 }}
          >
            {l.label}
          </button>
        ))}
      </div>
      <h3 style={{ marginBottom: 0 }}>{t("register.title")}</h3>
      <p style={{ color: "var(--hint)", marginTop: 4 }}>{t("register.subtitle")}</p>
      <div className="sheet__pad" style={{ width: "100%", maxWidth: 360 }}>
        <div className="field">
          <label>{t("register.firstName")}</label>
          <input value={first} onChange={(e) => setFirst(e.target.value)} />
        </div>
        <div className="field">
          <label>{t("register.lastName")}</label>
          <input value={last} onChange={(e) => setLast(e.target.value)} />
        </div>
        {err && <div className="form-error">{err}</div>}
        <button className="btn btn--primary" onClick={submit} disabled={busy}>
          {busy ? t("register.submitting") : t("register.submit")}
        </button>
      </div>
    </div>
  );
}
