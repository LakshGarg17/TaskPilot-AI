"use client";

import React from "react";
import Link from "next/navigation";
import NextLink from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  PlusCircle,
  Clock,
  Wrench,
  Settings,
  LogOut,
  User as UserIcon,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Badge } from "@/components/ui/badge";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { label: "New Task", href: "/app", icon: PlusCircle, exact: true },
    { label: "Tasks & History", href: "/app/tasks", icon: Clock },
    { label: "Tool Registry", href: "/app/tools", icon: Wrench },
    { label: "Settings", href: "/app/settings", icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-border bg-surface flex flex-col justify-between h-screen sticky top-0 select-none z-30">
      <div>
        {/* Logo and Brand Header */}
        <div className="p-5 border-b border-border flex items-center justify-between">
          <NextLink href="/" className="flex items-center gap-2.5 group">
            <div className="h-8 w-8 rounded-md bg-brass/10 border border-brass/30 flex items-center justify-center text-brass group-hover:scale-105 transition-transform">
              <Compass className="h-4 w-4" />
            </div>
            <div>
              <span className="font-serif font-bold text-lg tracking-tight text-foreground">
                TaskPilot <span className="text-brass">AI</span>
              </span>
              <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">
                OBSERVATORY V0.1
              </p>
            </div>
          </NextLink>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
            Control Station
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);

            return (
              <NextLink
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brass/15 text-brass border border-brass/30 font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-surface-secondary"
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? "text-brass" : ""}`} />
                <span>{item.label}</span>
              </NextLink>
            );
          })}
        </nav>
      </div>

      {/* Footer / User Profile & Mode */}
      <div className="p-4 border-t border-border bg-surface-secondary/40 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-sage animate-pulse-subtle" />
            <span className="text-xs font-mono text-muted-foreground">ENGINE ONLINE</span>
          </div>
          <ThemeToggle />
        </div>

        {user && (
          <div className="flex items-center justify-between pt-2 border-t border-border/50">
            <div className="flex items-center gap-2 min-w-0">
              <div className="h-7 w-7 rounded bg-surface border border-border flex items-center justify-center text-muted-foreground shrink-0">
                <UserIcon className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-medium text-foreground truncate max-w-[110px]" title={user.email}>
                  {user.email}
                </p>
                <p className="text-[10px] font-mono text-muted-foreground">OPERATOR</p>
              </div>
            </div>
            <button
              onClick={() => logout()}
              title="Sign Out"
              className="p-1.5 text-muted-foreground hover:text-clay transition-colors rounded hover:bg-surface"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
