"use client";

import React, { useState, useEffect, useRef } from "react";
import { Lock, Mail, ShieldAlert, Zap, AlertCircle, ArrowRight, ShieldCheck, Key, Terminal } from "lucide-react";
import gsap from "gsap";
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

  const cardRef = useRef<HTMLDivElement>(null);
  const bgGlowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLoading || user) return;

    // GSAP entrance animation for login card
    const ctx = gsap.context(() => {
      gsap.fromTo(
        cardRef.current,
        { opacity: 0, y: 30, scale: 0.96 },
        { opacity: 1, y: 0, scale: 1, duration: 0.8, ease: "power4.out" }
      );

      // Subtle ambient background breathing
      gsap.to(bgGlowRef.current, {
        scale: 1.15,
        opacity: 0.7,
        duration: 4,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    }, cardRef);

    return () => ctx.revert();
  }, [isLoading, user]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#06080D] flex flex-col items-center justify-center text-tradly-secondary font-mono text-xs space-y-4 selection:bg-cyan-500 selection:text-black">
        <div className="relative w-12 h-12 flex items-center justify-center">
          <div className="absolute inset-0 rounded-2xl bg-cyan-500/20 animate-ping" />
          <div className="w-12 h-12 rounded-2xl bg-tradly-card border border-cyan-500/40 flex items-center justify-center shadow-neon-cyan relative z-10">
            <Zap className="w-6 h-6 text-cyan-400 animate-pulse" />
          </div>
        </div>
        <div className="tracking-widest uppercase text-[11px] text-slate-400 flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span>Verifying Cryptographic Credentials...</span>
        </div>
      </div>
    );
  }

  // If user is authenticated, unlock the full trading terminal
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
      if (cardRef.current) {
        gsap.fromTo(
          cardRef.current,
          { x: -8 },
          { x: 8, duration: 0.08, repeat: 4, yoyo: true, ease: "power1.inOut", clearProps: "x" }
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#06080D] text-tradly-text flex flex-col items-center justify-center p-4 relative overflow-hidden selection:bg-cyan-500 selection:text-black">
      {/* Ambient background glows */}
      <div
        ref={bgGlowRef}
        className="absolute w-[600px] h-[600px] bg-gradient-to-tr from-cyan-600/10 via-blue-700/10 to-transparent rounded-full blur-3xl pointer-events-none -top-32 -left-32"
      />
      <div className="absolute w-[500px] h-[500px] bg-gradient-to-bl from-emerald-600/10 via-teal-800/5 to-transparent rounded-full blur-3xl pointer-events-none -bottom-32 -right-32" />

      {/* Cyberpunk Grid Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#182238_1px,transparent_1px),linear-gradient(to_bottom,#182238_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-25 pointer-events-none" />

      {/* Central Login Card */}
      <div
        ref={cardRef}
        className="relative w-full max-w-md bg-tradly-card/90 backdrop-blur-2xl border border-tradly-border rounded-3xl p-8 shadow-card-depth space-y-6 z-10"
      >
        {/* Terminal Header */}
        <div className="flex flex-col items-center text-center space-y-3.5">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-600 p-[1px] shadow-neon-cyan">
              <div className="w-full h-full bg-[#080C14] rounded-2xl flex items-center justify-center">
                <Lock className="w-7 h-7 text-cyan-400 stroke-[2.2]" />
              </div>
            </div>
            <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-red-500/20 border border-red-500/60 flex items-center justify-center">
              <span className="w-2 h-2 rounded-full bg-red-400 animate-ping" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-center space-x-2.5">
              <span className="font-black text-2xl tracking-wider text-white font-mono">TRADLY</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/30">
                RESTRICTED
              </span>
            </div>
            <p className="text-xs text-tradly-muted mt-1.5 font-medium tracking-wide">
              Institutional Forex Intelligence Terminal
            </p>
          </div>
        </div>

        {/* Security Warning Notice */}
        <div className="p-3.5 rounded-2xl bg-[#080C14] border border-tradly-border flex items-start space-x-3 text-xs">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-tradly-secondary leading-relaxed font-mono text-[11px]">
            Access is restricted to authorized operators. All interactions and IP streams are cryptographically logged.
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3.5 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center space-x-2 font-mono">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleLogin} className="space-y-4 text-xs font-mono">
          {showInviteRegister && (
            <>
              <div className="space-y-1.5">
                <label className="text-tradly-muted block font-semibold uppercase tracking-wider text-[10px]">
                  Operator Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Prince Patel"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-[#080C14] border border-tradly-border rounded-xl py-3 px-3.5 text-white placeholder:text-tradly-muted focus:outline-none focus:border-cyan-400 transition-colors"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-tradly-muted block font-semibold uppercase tracking-wider text-[10px]">
                  Administrator Invitation Code
                </label>
                <div className="relative">
                  <Key className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3.5" />
                  <input
                    type="password"
                    required
                    placeholder="TRADLY_..."
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value)}
                    className="w-full bg-[#080C14] border border-tradly-border rounded-xl py-3 pl-10 pr-3.5 text-white placeholder:text-tradly-muted focus:outline-none focus:border-cyan-400 transition-colors"
                  />
                </div>
              </div>
            </>
          )}

          <div className="space-y-1.5">
            <label className="text-tradly-muted block font-semibold uppercase tracking-wider text-[10px]">
              Operator Email / ID
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3.5" />
              <input
                type="email"
                required
                placeholder="name@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#080C14] border border-tradly-border rounded-xl py-3 pl-10 pr-3.5 text-white placeholder:text-tradly-muted focus:outline-none focus:border-cyan-400 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-tradly-muted block font-semibold uppercase tracking-wider text-[10px]">
              Security Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-tradly-muted absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-[#080C14] border border-tradly-border rounded-xl py-3 pl-10 pr-3.5 text-white placeholder:text-tradly-muted focus:outline-none focus:border-cyan-400 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-extrabold text-xs shadow-neon-cyan flex items-center justify-center space-x-2 transition-all transform active:scale-[0.98] disabled:opacity-50 cursor-pointer"
          >
            <span>{isSubmitting ? "Authenticating Session..." : showInviteRegister ? "Create Master Account" : "Unlock Trading Terminal"}</span>
            <ArrowRight className="w-4 h-4 text-black stroke-[2.5]" />
          </button>
        </form>

        {/* Footer Actions */}
        <div className="pt-4 border-t border-tradly-border/70 flex items-center justify-between text-[11px] font-mono text-tradly-muted">
          <button
            type="button"
            onClick={() => { setShowInviteRegister(!showInviteRegister); setError(null); }}
            className="hover:text-cyan-400 transition-colors cursor-pointer"
          >
            {showInviteRegister ? "← Return to Operator Sign In" : "Have an Invite Code? Register"}
          </button>

          <span className="flex items-center space-x-1 text-emerald-400 font-medium">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>256-Bit SSL</span>
          </span>
        </div>
      </div>
    </div>
  );
}
