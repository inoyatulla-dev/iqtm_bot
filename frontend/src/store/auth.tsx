import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import { authenticate, depsApi, updateLang } from "../api/client";
import type { Department, User } from "../api/types";
import { I18nProvider, type Lang } from "../i18n";
import { tg } from "../telegram";

interface AuthState {
  user: User | null;
  deps: Department[];
  loading: boolean;
  error: string | null;
  isBoss: boolean;
  reload: () => void;
}

const AuthCtx = createContext<AuthState>(null!);
export const useAuth = () => useContext(AuthCtx);

function detectLang(): Lang {
  const code = tg?.initDataUnsafe?.user?.language_code || "";
  if (code.startsWith("ru")) return "ru";
  if (code.startsWith("en")) return "en";
  return "uz";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [deps, setDeps] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLangState] = useState<Lang>(detectLang());

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const { user } = await authenticate();
      setUser(user);
      if (user.lang) setLangState(user.lang as Lang);
      if (user.status === "active") {
        setDeps(await depsApi.list());
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Xatolik");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function setLang(l: Lang) {
    setLangState(l);
    updateLang(l).catch(() => {});
    setUser((u) => (u ? { ...u, lang: l } : u));
  }

  return (
    <AuthCtx.Provider
      value={{ user, deps, loading, error, isBoss: user?.role === "boss", reload: load }}
    >
      <I18nProvider lang={lang} setLang={setLang}>
        {children}
      </I18nProvider>
    </AuthCtx.Provider>
  );
}
