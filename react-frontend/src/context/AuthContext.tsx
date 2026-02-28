"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from "react";
import api from "@/lib/api";

// ---- Types --------------------------------------------------------------

interface User {
  user_id: string;
  username: string;
  email: string;
  api_key: string;
  is_active: boolean;
  agents: { agent_id: string; is_active: boolean; last_seen_at: string | null }[];
}

interface AuthState {
  token: string | null;
  user: User | null;
  loading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string, email: string) => Promise<void>;
  logout: () => void;
}

// ---- Context ------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    user: null,
    loading: true,
  });

  // Hydrate from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("access_token");
    if (stored) {
      setState((s) => ({ ...s, token: stored }));
      fetchProfile(stored);
    } else {
      setState((s) => ({ ...s, loading: false }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchProfile = useCallback(async (token: string) => {
    try {
      const { data } = await api.get<User>("/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setState({ token, user: data, loading: false });
    } catch {
      localStorage.removeItem("access_token");
      setState({ token: null, user: null, loading: false });
    }
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { data } = await api.post("/auth/login", { username, password });
    localStorage.setItem("access_token", data.access_token);
    setState((s) => ({ ...s, token: data.access_token }));
    await fetchProfile(data.access_token);
  }, [fetchProfile]);

  const register = useCallback(
    async (username: string, password: string, email: string) => {
      await api.post("/auth/register", { username, password, email });
      // Auto-login after registration
      await login(username, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    setState({ token: null, user: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}
