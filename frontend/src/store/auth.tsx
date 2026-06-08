import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import { authenticate, depsApi } from "../api/client";
import type { Department, User } from "../api/types";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [deps, setDeps] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const { user } = await authenticate();
      setUser(user);
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

  return (
    <AuthCtx.Provider
      value={{
        user, deps, loading, error,
        isBoss: user?.role === "boss",
        reload: load,
      }}
    >
      {children}
    </AuthCtx.Provider>
  );
}
