"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { API_BASE } from "../services/api";

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (name: string, email: string, pass: string) => Promise<void>;
  logout: () => void;
  isAuthModalOpen: boolean;
  openAuthModal: () => void;
  closeAuthModal: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  useEffect(() => {
    const savedToken = typeof window !== "undefined" ? localStorage.getItem("tradly_token") : null;
    const savedUser = typeof window !== "undefined" ? localStorage.getItem("tradly_user") : null;

    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem("tradly_token");
        localStorage.removeItem("tradly_user");
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password: pass }),
    });

    const json = await res.json();
    if (!res.ok || json.error) {
      throw new Error(json.error?.message || "Invalid credentials");
    }

    const authData = json.data;
    setToken(authData.access_token);
    setUser(authData.user);
    if (typeof window !== "undefined") {
      localStorage.setItem("tradly_token", authData.access_token);
      localStorage.setItem("tradly_user", JSON.stringify(authData.user));
    }
    setIsAuthModalOpen(false);
  };

  const register = async (name: string, email: string, pass: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password: pass }),
    });

    const json = await res.json();
    if (!res.ok || json.error) {
      throw new Error(json.error?.message || "Registration failed");
    }

    const authData = json.data;
    setToken(authData.access_token);
    setUser(authData.user);
    if (typeof window !== "undefined") {
      localStorage.setItem("tradly_token", authData.access_token);
      localStorage.setItem("tradly_user", JSON.stringify(authData.user));
    }
    setIsAuthModalOpen(false);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("tradly_token");
      localStorage.removeItem("tradly_user");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        register,
        logout,
        isAuthModalOpen,
        openAuthModal: () => setIsAuthModalOpen(true),
        closeAuthModal: () => setIsAuthModalOpen(false),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
