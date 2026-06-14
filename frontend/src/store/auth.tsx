import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import {
  authenticate, boardColumnsApi, brandingApi, clearToken, depsApi, fetchMe, getToken,
  loginWithCredentials, updateLang,
} from "../api/client";
import type { BoardColumn, Department, User } from "../api/types";
import { I18nProvider, type Lang } from "../i18n";
import { getInitData, tg } from "../telegram";

interface AuthState {
  user: User | null;
  deps: Department[];
  columns: BoardColumn[];
  loading: boolean;
  error: string | null;
  needsLogin: boolean;
  isBoss: boolean;
  isObserver: boolean;
  timezone: string;
  reload: () => void;
  loginWeb: (login: string, password: string) => Promise<void>;
  logout: () => void;
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
  const [needsLogin, setNeedsLogin] = useState(false);
  const [lang, setLangState] = useState<Lang>(detectLang());
  const [timezone, setTimezone] = useState("Asia/Tashkent");

  async function applyUser(u: User) {
    setUser(u);
    if (u.lang) setLangState(u.lang as Lang);
    if (u.status === "active") {
      const [deps, columns] = await Promise.all([depsApi.list(), boardColumnsApi.list()]);
      setDeps(deps);
      setColumns(columns);
    }
  }

  async function load() {
    setLoading(true);
    setError(null);
    setNeedsLogin(false);
    try {
      if (getInitData()) {
        const { user } = await authenticate();
        await applyUser(user);
      } else if (getToken()) {
        const user = await fetchMe();
        await applyUser(user);
      } else {
        setNeedsLogin(true);
      }
    } catch (e: any) {
      if (getToken() && !getInitData()) {
        clearToken();
        setNeedsLogin(true);
      } else {
        setError(e?.response?.data?.detail || e.message || "Xatolik");
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    brandingApi
      .get()
      .then((b) => setTimezone(b.timezone || "Asia/Tashkent"))
      .catch(() => {});
  }, []);

  async function loginWeb(login: string, password: string) {
    const { user } = await loginWithCredentials(login, password);
    await applyUser(user);
    setNeedsLogin(false);
  }

  function logout() {
    clearToken();
    setUser(null);
    setDeps([]);
    setColumns([]);
    setNeedsLogin(true);
  }

  function setLang(l: Lang) {
    setLangState(l);
    updateLang(l).catch(() => {});
    setUser((u) => (u ? { ...u, lang: l } : u));
  }

  return (
    <AuthCtx.Provider
      value={{
        user, deps, columns, loading, error, needsLogin,
        isBoss: user?.role === "boss",
        isObserver: user?.role === "observer",
        timezone,
        reload: load,
        loginWeb,
        logout,
      }}
    >
      <I18nProvider lang={lang} setLang={setLang}>
        {children}
      </I18nProvider>
    </AuthCtx.Provider>
  );
}
