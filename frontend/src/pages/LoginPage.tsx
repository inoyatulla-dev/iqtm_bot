import { useState } from "react";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";
import { Logo } from "../components/Logo";

export function LoginPage() {
  const { loginWeb } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [login, setLoginVal] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!login.trim() || !password) return;
    setBusy(true);
    setErr("");
    try {
      await loginWeb(login.trim(), password);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t("login.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="center-screen" style={{ justifyContent: "flex-start", paddingTop: 40 }}>
      <Logo />
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
      <h3 style={{ marginBottom: 0 }}>{t("login.title")}</h3>
      <p style={{ color: "var(--hint)", marginTop: 4 }}>{t("login.subtitle")}</p>
      <form className="sheet__pad" style={{ width: "100%", maxWidth: 360 }} onSubmit={submit}>
        <div className="field">
          <label>{t("login.loginLabel")}</label>
          <input
            value={login}
            onChange={(e) => setLoginVal(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
          />
        </div>
        <div className="field">
          <label>{t("login.passwordLabel")}</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        {err && <div className="form-error">{err}</div>}
        <button className="btn btn--primary" type="submit" disabled={busy}>
          {busy ? t("login.submitting") : t("login.submit")}
        </button>
      </form>
    </div>
  );
}
