"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User } from "@/types";
import { api, ApiError } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const refreshUser = async () => {
    try {
      const currentUser = await api.auth.me();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  // Client protection for /app/* routes
  useEffect(() => {
    if (!isLoading) {
      if (pathname.startsWith("/app") && !user) {
        router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
      }
    }
  }, [isLoading, user, pathname, router]);

  const login = async (email: string, password: string) => {
    const res = await api.auth.login({ email, password });
    setUser(res.user);
    const redirectUrl = new URLSearchParams(window.location.search).get("redirect") || "/app";
    router.push(redirectUrl);
  };

  const signup = async (email: string, password: string) => {
    const newUser = await api.auth.signup({ email, password });
    setUser(newUser);
    router.push("/app");
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      router.push("/");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        signup,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
