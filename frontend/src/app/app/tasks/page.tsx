"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Clock, Search, ArrowRight, CheckCircle2, AlertTriangle, AlertCircle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { Task } from "@/types";
import { Badge } from "@/components/ui/badge";
import { formatDate, formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export default function TasksHistoryPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const data = await api.tasks.list();
      setTasks(data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const filteredTasks = tasks.filter((t) => {
    const matchesFilter = filter === "ALL" || t.status === filter;
    const matchesSearch =
      t.goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground">
            Missions & History
          </h1>
          <p className="text-sm text-muted-foreground font-sans">
            Audit log of all autonomous plans, tool executions, and verified reports.
          </p>
        </div>

        <Button onClick={fetchTasks} variant="secondary" size="sm" className="font-mono text-xs">
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-3 rounded-lg bg-surface border border-border">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search missions by goal or ID..."
            className="w-full pl-9 pr-3 py-1.5 bg-background border border-border rounded-md text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brass font-sans"
          />
        </div>

        <div className="flex items-center gap-1.5 flex-wrap w-full sm:w-auto">
          {["ALL", "COMPLETED", "WAITING_APPROVAL", "RUNNING", "FAILED"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                filter === status
                  ? "bg-brass text-black font-bold"
                  : "bg-surface-secondary text-muted-foreground hover:text-foreground border border-border"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Tasks List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-lg bg-surface border border-border animate-pulse" />
          ))}
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="p-12 text-center rounded-lg border border-dashed border-border bg-surface/50 text-muted-foreground space-y-3">
          <Clock className="h-8 w-8 text-muted-foreground/60 mx-auto" />
          <p className="text-sm font-sans">No matching missions found.</p>
          <Link href="/app">
            <Button size="sm" variant="secondary" className="font-sans mt-2">
              Launch a New Mission
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredTasks.map((t) => {
            const durationSec =
              t.completed_at && t.created_at
                ? (new Date(t.completed_at).getTime() - new Date(t.created_at).getTime()) / 1000
                : null;

            return (
              <Link
                key={t.id}
                href={`/app/tasks/${t.id}`}
                className="block p-5 rounded-lg bg-surface border border-border hover:border-brass/50 transition-all group shadow-sm hover:shadow-md"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-muted-foreground uppercase">
                        ID: {t.id.slice(0, 8)}...
                      </span>
                      <Badge
                        variant={
                          t.status === "COMPLETED"
                            ? "sage"
                            : t.status === "WAITING_APPROVAL"
                            ? "clay"
                            : t.status === "FAILED"
                            ? "clay"
                            : "default"
                        }
                      >
                        {t.status}
                      </Badge>
                    </div>
                    <h3 className="text-sm font-semibold text-foreground group-hover:text-brass transition-colors line-clamp-2 font-sans">
                      {t.goal}
                    </h3>
                    <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground">
                      <span>Created: {formatDate(t.created_at)}</span>
                      {durationSec != null && <span>Duration: {formatDuration(durationSec)}</span>}
                      <span>{t.steps?.length || 0} Steps</span>
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center gap-2 text-xs font-mono text-muted-foreground group-hover:text-brass">
                    <span>INSPECT OBSERVATORY</span>
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
