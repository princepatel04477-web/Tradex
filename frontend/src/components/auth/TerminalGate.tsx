"use client";

import React, { useState } from "react";
import { Lock, Mail, ShieldAlert, Zap, AlertCircle, ArrowRight, ShieldCheck, Key } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export default function TerminalGate({ children }: { children: React.ReactNode }) {
  const { user, isLoading, login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Invite code registration toggle
  const [showInviteRegister, setShowInviteRegister] = useState(false);
  const [name, setName] = useState("");
  const [inviteCode, setInviteCode] = useState("");

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#07090E] flex flex-col items-center justify-center text-tradly-muted font-mono text-xs space-y-3">
        <div className="w-10 h-10 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center animate-pulse">
          <Zap className="w-5 h-5 text-cyan-400" />
        </div>
        <div>AUTHENTICATING SYSTEM CREDENTIALS...</div>
      </div>
    );
  }

  // If user is authenticated, unlock the full terminal
  if (user) {
    return <>{children}</>;
  }

  // Otherwise, lock behind the Private Terminal Gate
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (showInviteRegister) {
        if (!name.trim()) throw new Error("Please enter your name");
        if (!inviteCode.trim()) throw new Error("A valid Administrator Invitation Code is required");
        await register(name, email, password, inviteCode);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || "Invalid credentials or unauthorized access.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07090E] flex flex-col items-center justify-center p-4 selection:bg-cyan-500 selection:text-black">
      {/* Background Matrix Grid Pattern */}
      <div className="absolute inset-0 bg-[radial-gradient(#1E2638_1px,transparent_1px)] [background-size:24px_24px] opacity-30 pointer-events-none" />

      <div className="relative w-full max-w-md bg-tradly-card border border-tradly-border rounded-3xl p-8 shadow-2xl shadow-cyan-500/10 space-y-6">
        {/* Security Lock Header */}
        <div className="flex flex-col items-center text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-xl shadow-cyan-500/20">
            <Lock className="w-7 h-7 text-black stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center justify-center space-x-2">
              <span className="font-extrabold text-2xl tracking-wider text-white">TRADLY</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/30 flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-ping" />
                <span>RESTRICTED</span>
              </span>
            </div>
            <p className="text-xs text-tradly-muted mt-1 font-mono">
              Institutional Forex Intelligence Terminal
            </p>
          </div>
        </div>

        {/* Access Warning Banner */}
        <div className="p-3.5 rounded-2xl bg-tradly-bg border border-tradly-border flex items-start space-x-3 text-xs">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-slate-300 leading-relaxed font-mono text-[11px]">
            Private terminal. Access is strictly restricted to authorized operator accounts.
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Secure Login Form */}
        <form onSubmit={handleLogin} className="space-y-4 text-xs font-mono">
          {showInviteRegister && (
            <>
              <div>
                <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="Operator Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 px-3 text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
                  Administrator Invitation Code
                </label>
                <div className="relative">
                  <Key className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    placeholder="TRADLY_..."
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value)}
                    className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
              Operator Email / ID
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
              <input
                type="email"
                required
                placeholder="name@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <div>
            <label className="text-tradly-muted block mb-1.5 font-bold uppercase tracking-wider text-[10px]">
              Security Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3" />
              <input
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-tradly-bg border border-tradly-border rounded-xl py-2.5 pl-10 pr-3 text-white focus:outline-none focus:border-cyan-400"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center justify-center space-x-2 transition-all disabled:opacity-50 cursor-pointer"
          >
            <span>{isSubmitting ? "Verifying..." : showInviteRegister ? "Create Authorized Account" : "Unlock Terminal"}</span>
            <ArrowRight className="w-4 h-4 text-black" />
          </button>
        </form>

        {/* Toggle Invitation Registration */}
        <div className="pt-3 border-t border-tradly-border flex items-center justify-between text-[11px] font-mono text-tradly-muted">
          <button
            type="button"
            onClick={() => { setShowInviteRegister(!showInviteRegister); setError(null); }}
            className="hover:text-cyan-400 transition-colors cursor-pointer"
          >
            {showInviteRegister ? "← Back to Operator Sign In" : "Have an Invite Code? Register"}
          </button>

          <span className="flex items-center space-x-1 text-emerald-400">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Encrypted</span>
          </span>
        </div>
      </div>
    </div>
  );
}
