import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import { authenticate, boardColumnsApi, depsApi, updateLang } from "../api/client";
import type { BoardColumn, Department, User } from "../api/types";
import { I18nProvider, type Lang } from "../i18n";
import { tg } from "../telegram";

interface AuthState {
  user: User | null;
  deps: Department[];
  columns: BoardColumn[];
  loading: boolean;
  error: string | null;
  isBoss: boolean;
  isObserver: boolean;
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
  const [columns, setColumns] = useState<BoardColumn[]>([]);
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
        const [deps, columns] = await Promise.all([depsApi.list(), boardColumnsApi.list()]);
        setDeps(deps);
        setColumns(columns);
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
      value={{
        user, deps, columns, loading, error,
        isBoss: user?.role === "boss",
        isObserver: user?.role === "observer",
        reload: load,
      }}
    >
      <I18nProvider lang={lang} setLang={setLang}>
        {children}
      </I18nProvider>
    </AuthCtx.Provider>
  );
}
