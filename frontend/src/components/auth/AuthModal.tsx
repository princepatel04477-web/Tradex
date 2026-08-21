"use client";

import React, { useState } from "react";
import { Lock, Mail, User, X, AlertCircle, CheckCircle2, Shield, Zap } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, login, register } = useAuth();
  const [tab, setTab] = useState<"login" | "register">("login");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (tab === "login") {
        await login(email, password);
      } else {
        if (!name.trim()) throw new Error("Please enter your name");
        await register(name, email, password);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const fillDemoAccount = () => {
    setEmail("princepatel01258@gmail.com");
    setPassword("Prince_1258");
    setTab("login");
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md bg-tradly-card border border-tradly-border rounded-3xl p-6 shadow-2xl shadow-cyan-500/10 space-y-6">
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-5 right-5 p-2 rounded-xl text-tradly-muted hover:text-white hover:bg-tradly-bg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap className="w-5 h-5 text-black stroke-[2.5]" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">
              {tab === "login" ? "Trader Sign In" : "Create Trader Account"}
            </h2>
            <p className="text-xs text-tradly-muted">
              {tab === "login"
                ? "Access institutional paper engine & AI research"
                : "Join Tradly Forex Intelligence terminal"}
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex p-1 bg-tradly-bg rounded-2xl border border-tradly-border text-xs font-mono">
          <button
            onClick={() => { setTab("login"); setError(null); }}
            className={`flex-1 py-2 rounded-xl font-bold transition-all ${
              tab === "login"
                ? "bg-cyan-500 text-black shadow-md"
                : "text-tradly-muted hover:text-white"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setTab("register"); setError(null); }}
            className={`flex-1 py-2 rounded-xl font-bold transition-all ${
              tab === "register"
                ? "bg-cyan-500 text-black shadow-md"
                : "text-tradly-muted hover:text-white"
            }`}
          >
            Register
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
          {tab === "register" && (
            <div>
              <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Satoshi Nakamoto"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
                />
              </div>
            </div>
          )}

          <div>
            <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
              <input
                type="email"
                required
                placeholder="trader@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <div>
            <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
              <input
                type="password"
                required
                placeholder="Min 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting
              ? "Authenticating..."
              : tab === "login"
              ? "Sign In to Terminal"
              : "Create Account"}
          </button>
        </form>

        {/* Demo Account 1-Click Button */}
        <div className="pt-2 border-t border-tradly-border">
          <button
            type="button"
            onClick={fillDemoAccount}
            className="w-full py-2.5 rounded-xl bg-tradly-bg hover:bg-tradly-hover border border-tradly-border text-slate-300 text-xs font-mono flex items-center justify-center space-x-2 transition-colors cursor-pointer"
          >
            <Shield className="w-3.5 h-3.5 text-cyan-400" />
            <span>Use Demo Trader Credentials (1-Click)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
