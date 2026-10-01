"use client";

import React from "react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { useAuth } from "@/lib/auth-context";
import { Compass } from "lucide-react";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center space-y-4">
        <div className="h-12 w-12 rounded-lg border border-brass/40 flex items-center justify-center text-brass animate-spin">
          <Compass className="h-6 w-6" />
        </div>
        <p className="text-xs font-mono text-muted-foreground uppercase tracking-widest">
          INITIALIZING OBSERVATORY LINK...
        </p>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect via AuthContext
  }

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
