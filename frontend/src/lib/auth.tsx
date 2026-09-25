"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as api from "@/lib/api";

type User = { id: string; email: string };

type AuthContextValue = {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const USER_KEY = "paperpilot_user";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const token = api.getToken();
      const raw = localStorage.getItem(USER_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time rehydration from localStorage on mount
      if (token && raw) setUser(JSON.parse(raw));
    } catch {
      // ignore
    } finally {
      setReady(true);
    }
  }, []);

  function persist(token: string, user: User) {
    api.setToken(token);
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch {
      // ignore
    }
    setUser(user);
  }

  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    persist(result.token, result.user);
  }

  async function signup(email: string, password: string) {
    const result = await api.signup(email, password);
    persist(result.token, result.user);
  }

  function logout() {
    api.setToken(null);
    try {
      localStorage.removeItem(USER_KEY);
    } catch {
      // ignore
    }
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, ready, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
