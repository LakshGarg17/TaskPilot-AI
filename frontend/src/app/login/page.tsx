"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Compass, ArrowRight, Lock, Mail, AlertCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const { login, signup } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSubmitting(true);
    try {
      await login(email, password);
      toast.success("Welcome back to TaskPilot");
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid email or password");
      toast.error(err.message || "Failed to log in");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setErrorMsg("");
    setSubmitting(true);
    const demoEmail = "demo@example.com";
    const demoPass = "TaskPilotDemo2026!";
    try {
      try {
        await login(demoEmail, demoPass);
      } catch {
        // If demo user doesn't exist, sign up
        await signup(demoEmail, demoPass);
      }
      toast.success("Authenticated with demo credentials");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to sign in with demo account");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col justify-center items-center px-4">
      <div className="w-full max-w-md space-y-8 p-8 rounded-xl bg-surface border border-border shadow-xl">
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center gap-2 text-brass mb-2">
            <Compass className="h-6 w-6" />
            <span className="font-serif font-bold text-xl text-foreground">TaskPilot AI</span>
          </Link>
          <h1 className="font-serif text-2xl font-bold tracking-tight">Observatory Access</h1>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
            AUTHENTICATE OPERATOR CREDENTIALS
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded bg-clay/10 border border-clay/30 text-clay text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Operator Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@taskpilot.local"
                className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-brass"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-mono uppercase text-muted-foreground">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-brass"
              />
            </div>
          </div>

          <Button type="submit" disabled={submitting} className="w-full mt-2">
            {submitting ? "Authenticating..." : "Sign In to Station"}
          </Button>
        </form>

        <div className="relative border-t border-border pt-4 text-center">
          <p className="text-xs text-muted-foreground mb-3 font-mono uppercase">Quick Demo Access</p>
          <Button
            type="button"
            variant="secondary"
            onClick={handleDemoLogin}
            disabled={submitting}
            className="w-full text-xs font-mono"
          >
            ⚡ Instant 1-Click Demo Login
          </Button>
        </div>

        <p className="text-center text-xs text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/signup" className="text-brass hover:underline font-medium">
            Create an Operator Account
          </Link>
        </p>
      </div>
    </div>
  );
}
