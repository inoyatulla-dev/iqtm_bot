import { useState } from "react";
import { Eye, EyeOff, Lock, LogIn, User } from "lucide-react";
import { useAuth } from "../store/auth";
import { useI18n, LANGS, type Lang } from "../i18n";
import { Logo } from "../components/Logo";

export function LoginPage() {
  const { loginWeb } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [login, setLoginVal] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
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
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__logo">
          <Logo />
        </div>
        <h1 className="login-card__title">{t("login.title")}</h1>
        <p className="login-card__subtitle">{t("login.subtitle")}</p>

        <form className="login-form" onSubmit={submit}>
          <div className="login-field">
            <User className="login-field__icon" size={18} />
            <input
              value={login}
              onChange={(e) => setLoginVal(e.target.value)}
              placeholder={t("login.loginLabel")}
              autoComplete="username"
              autoCapitalize="none"
              autoFocus
            />
          </div>
          <div className="login-field">
            <Lock className="login-field__icon" size={18} />
            <input
              type={showPw ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("login.passwordLabel")}
              autoComplete="current-password"
              style={{ paddingRight: 44 }}
            />
            <button
              type="button"
              className="login-field__toggle"
              onClick={() => setShowPw((v) => !v)}
              tabIndex={-1}
            >
              {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          {err && <div className="form-error">{err}</div>}

          <button className="btn btn--primary login-submit" type="submit" disabled={busy}>
            {busy ? (
              t("login.submitting")
            ) : (
              <>
                <LogIn size={18} />
                {t("login.submit")}
              </>
            )}
          </button>
        </form>

        <div className="login-card__langs">
          {LANGS.map((l) => (
            <button
              key={l.code}
              type="button"
              onClick={() => setLang(l.code as Lang)}
              className={`login-lang${lang === l.code ? " login-lang--active" : ""}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
