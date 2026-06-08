import { useState } from "react";
import { updateProfile } from "../api/client";
import { useAuth } from "../store/auth";
import { Logo } from "../components/Logo";

/** Yangi xodim /start bergach to'ldiradigan forma: Ism + Familiya. */
export function RegisterForm() {
  const { user, reload } = useAuth();
  const parts = (user?.name || "").split(" ");
  const [first, setFirst] = useState(parts[0] || "");
  const [last, setLast] = useState(parts.slice(1).join(" ") || "");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function submit() {
    if (first.trim().length < 2) {
      setErr("Ismingizni kiriting");
      return;
    }
    setBusy(true);
    setErr("");
    try {
      await updateProfile(first.trim(), last.trim());
      setSent(true);
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <div className="center-screen">
        <Logo />
        <h3>✅ Ariza yuborildi</h3>
        <p style={{ color: "var(--hint)" }}>
          Admin tasdiqlagunicha kuting. Tasdiqlangach, ilovani qayta oching.
        </p>
        <button className="btn btn--ghost" style={{ maxWidth: 200 }} onClick={reload}>
          Holatni tekshirish
        </button>
      </div>
    );
  }

  return (
    <div className="center-screen" style={{ justifyContent: "flex-start", paddingTop: 48 }}>
      <Logo />
      <h3 style={{ marginBottom: 0 }}>Ro'yxatdan o'tish</h3>
      <p style={{ color: "var(--hint)", marginTop: 4 }}>
        Ism va familiyangizni kiriting — admin tasdiqlaydi.
      </p>
      <div className="sheet__pad" style={{ width: "100%", maxWidth: 360 }}>
        <div className="field">
          <label>Ism</label>
          <input value={first} onChange={(e) => setFirst(e.target.value)} placeholder="Ism" />
        </div>
        <div className="field">
          <label>Familiya</label>
          <input value={last} onChange={(e) => setLast(e.target.value)} placeholder="Familiya" />
        </div>
        {err && <div className="form-error">{err}</div>}
        <button className="btn btn--primary" onClick={submit} disabled={busy}>
          {busy ? "Yuborilmoqda…" : "Yuborish"}
        </button>
      </div>
    </div>
  );
}
