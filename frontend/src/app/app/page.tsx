"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  ArrowRight,
  Compass,
  Search,
  FileText,
  Calculator,
  Mail,
  Clock,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { Task } from "@/types";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import Link from "next/link";

interface SuggestionChip {
  id: string;
  label: string;
  icon: any;
  prompt: string;
}

const DEMO_PROMPTS: SuggestionChip[] = [
  {
    id: "demo",
    label: "Demo: Research & Compare",
    icon: Search,
    prompt:
      "Research the top AI hackathons currently accepting applications, compare their deadlines, prizes and requirements, and create a concise report.",
  },
  {
    id: "data",
    label: "Analyze Data & Stats",
    icon: Calculator,
    prompt:
      "Analyze model inference latency numbers across batches [120, 145, 98, 110, 130], calculate mean and variance, and synthesize performance takeaways.",
  },
  {
    id: "email",
    label: "Draft & Send Email (Approval Flow)",
    icon: Mail,
    prompt:
      "Draft an executive notification email to team@example.com summarizing our upcoming AI hackathon strategy and dispatch the communication.",
  },
  {
    id: "extract",
    label: "Structured Extraction",
    icon: FileText,
    prompt:
      "Extract structured comparison details regarding leading autonomous agent frameworks including license, memory footprint, and strengths.",
  },
  {
    id: "compute",
    label: "Compute Cost Analysis",
    icon: Sparkles,
    prompt:
      "Calculate the annual cloud compute cost across 4 GPU clusters running at 3.50 per hour and summarize cost optimization recommendations.",
  },
];

export default function DashboardPage() {
  const [goal, setGoal] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.tasks
      .list()
      .then((tasks) => setRecentTasks(tasks.slice(0, 5)))
      .catch(() => null)
      .finally(() => setLoadingTasks(false));
  }, []);

  const handleRunTask = async () => {
    const trimmed = goal.trim();
    if (!trimmed) {
      toast.error("Please enter a goal for TaskPilot to execute.");
      return;
    }

    setSubmitting(true);
    try {
      const task = await api.tasks.create(trimmed);
      toast.success("Task initialized. Entering execution observatory.");
      router.push(`/app/tasks/${task.id}`);
    } catch (err: any) {
      toast.error(err.message || "Failed to launch task");
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleRunTask();
    }
  };

  return (
    <div className="space-y-10 max-w-4xl mx-auto py-4">
      {/* Heading */}
      <div className="space-y-2 text-center md:text-left">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-brass uppercase tracking-wider mb-1">
          <Compass className="h-4 w-4" />
          <span>AUTONOMOUS AGENT COMMAND CONSOLE</span>
        </div>
        <h1 className="font-serif text-3xl md:text-4xl font-bold tracking-tight text-foreground">
          What do you want TaskPilot to accomplish?
        </h1>
        <p className="text-sm md:text-base text-muted-foreground font-sans max-w-2xl">
          Give TaskPilot a goal. It will plan, execute with real tools, and verify the work for you.
        </p>
      </div>

      {/* Large Command Box */}
      <div className="p-4 md:p-6 rounded-xl border border-border bg-surface shadow-lg space-y-4 focus-within:border-brass/60 transition-colors">
        <textarea
          id="task-goal-input"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="State your goal in natural language... (e.g., Research top AI hackathons, compare prizes and deadlines, and draft an executive report)"
          rows={4}
          className="w-full bg-transparent resize-none text-base text-foreground placeholder:text-muted-foreground/60 focus:outline-none font-sans leading-relaxed"
        />

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-border">
          <span className="text-xs font-mono text-muted-foreground hidden sm:inline-block">
            PRESS <kbd className="px-1.5 py-0.5 rounded bg-surface-secondary border border-border text-[11px] text-foreground font-semibold">Cmd/Ctrl + Enter</kbd> TO RUN
          </span>

          <Button
            id="run-task-btn"
            onClick={handleRunTask}
            disabled={submitting || !goal.trim()}
            size="lg"
            className="w-full sm:w-auto font-sans"
          >
            {submitting ? "Formulating Plan..." : "Run Task"}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Clickable Suggestion Chips */}
      <div className="space-y-3">
        <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
          SUGGESTION CHIPS (CLICK TO POPULATE):
        </p>
        <div className="flex flex-wrap gap-2">
          {DEMO_PROMPTS.map((chip) => {
            const Icon = chip.icon;
            const isSelected = goal === chip.prompt;

            return (
              <button
                key={chip.id}
                onClick={() => setGoal(chip.prompt)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-mono transition-all text-left border ${
                  isSelected
                    ? "bg-brass/15 border-brass text-brass font-semibold"
                    : "bg-surface border-border text-foreground hover:border-brass/40 hover:bg-surface-secondary"
                }`}
              >
                <Icon className="h-3.5 w-3.5 text-brass shrink-0" />
                <span>{chip.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Recent Missions Section */}
      <div className="space-y-4 pt-4 border-t border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-brass" />
            <h2 className="font-serif text-lg font-bold">Recent Missions</h2>
          </div>
          <Link href="/app/tasks" className="text-xs font-mono text-brass hover:underline">
            VIEW ALL MISSIONS →
          </Link>
        </div>

        {loadingTasks ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-16 rounded-lg bg-surface border border-border animate-pulse" />
            ))}
          </div>
        ) : recentTasks.length === 0 ? (
          <div className="p-8 text-center rounded-lg border border-dashed border-border bg-surface/50 text-muted-foreground text-sm font-sans">
            No missions launched yet. Use the prompt box above or choose a suggestion chip to begin.
          </div>
        ) : (
          <div className="space-y-2">
            {recentTasks.map((t) => (
              <Link
                key={t.id}
                href={`/app/tasks/${t.id}`}
                className="flex items-center justify-between p-4 rounded-lg bg-surface border border-border hover:border-brass/40 transition-colors group"
              >
                <div className="min-w-0 pr-4">
                  <p className="text-sm font-medium text-foreground truncate group-hover:text-brass transition-colors">
                    {t.goal}
                  </p>
                  <p className="text-xs font-mono text-muted-foreground mt-0.5">
                    {formatDate(t.created_at)} • {t.steps?.length || 0} Steps
                  </p>
                </div>
                <div className="shrink-0 flex items-center gap-3">
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
                  <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
