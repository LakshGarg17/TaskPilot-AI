"use client";

import React, { useState, useEffect } from "react";
import { Settings, Shield, User, Globe, AlertCircle, Sun, Moon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "next-themes";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [healthData, setHealthData] = useState<any>(null);

  useEffect(() => {
    api.health.check().then(setHealthData).catch(() => null);
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12 font-sans">
      <div>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground">
          Observatory Settings
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          System telemetry, model providers, network origin configuration, and theme preferences.
        </p>
      </div>

      <div className="space-y-6">
        {/* User Account Details */}
        <div className="p-6 rounded-xl bg-surface border border-border space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <User className="h-4 w-4 text-brass" />
            <h2 className="font-serif text-base font-bold">Operator Profile</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Email Address</span>
              <p className="text-sm text-foreground font-sans mt-0.5">{user?.email}</p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Station Role</span>
              <p className="text-sm text-foreground font-sans mt-0.5">Primary Operator (Superuser)</p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Operator ID</span>
              <p className="text-xs text-foreground mt-0.5 truncate">{user?.id}</p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Enrolled Since</span>
              <p className="text-xs text-foreground mt-0.5">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "Active"}
              </p>
            </div>
          </div>
        </div>

        {/* Engine Telemetry & Providers */}
        <div className="p-6 rounded-xl bg-surface border border-border space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-brass" />
              <h2 className="font-serif text-base font-bold">Engine Telemetry & Configuration</h2>
            </div>
            <Badge variant={healthData?.mock_mode ? "ochre" : "sage"}>
              {healthData?.mock_mode ? "MOCK MODE" : "PRODUCTION"}
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Backend API URL</span>
              <p className="text-xs text-foreground mt-0.5">
                {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">LLM Provider Model</span>
              <p className="text-xs text-brass font-bold mt-0.5">
                {healthData?.openai_model || "gpt-4o-mini"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Search Engine Provider</span>
              <p className="text-xs text-foreground mt-0.5">
                {healthData?.search_provider || "tavily"}
              </p>
            </div>
            <div>
              <span className="text-muted-foreground uppercase text-[10px]">Security Policy</span>
              <p className="text-xs text-sage mt-0.5">Strict Human Gate (HIGH Risk Paused)</p>
            </div>
          </div>

          {healthData?.mock_mode && (
            <div className="p-3 rounded bg-ochre/10 border border-ochre/30 text-xs text-ochre font-sans flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                Mock mode is active. AI planning, tool actions, and search queries produce deterministic, offline mock data clearly labeled in results.
              </span>
            </div>
          )}
        </div>

        {/* Appearance & Theme */}
        <div className="p-6 rounded-xl bg-surface border border-border space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-border">
            <Sun className="h-4 w-4 text-brass" />
            <h2 className="font-serif text-base font-bold">Theme & Observatory Aesthetics</h2>
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="text-sm font-medium">Ink &amp; Brass Color Theme</p>
              <p className="text-xs text-muted-foreground">
                Toggle between Dark Ink (#0B0D10) and Light Paper (#F6F2EA).
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant={theme === "dark" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("dark")}
                className="font-mono text-xs"
              >
                <Moon className="h-3.5 w-3.5 mr-1" /> Dark Ink
              </Button>
              <Button
                variant={theme === "light" ? "default" : "outline"}
                size="sm"
                onClick={() => setTheme("light")}
                className="font-mono text-xs"
              >
                <Sun className="h-3.5 w-3.5 mr-1" /> Light Paper
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
