"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Compass,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  Terminal,
  FileText,
  Copy,
  Download,
  ShieldAlert,
  RotateCw,
  ExternalLink,
  ChevronRight,
  Activity,
  Layers,
  Wrench,
  Check,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { Task, TaskStep, TaskEvent, Approval } from "@/types";
import { formatDate, formatDuration } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function TaskExecutionPage() {
  const { id } = useParams() as { id: string };
  const router = useRouter();

  const [task, setTask] = useState<Task | null>(null);
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<string>("result");
  const [approvalModalOpen, setApprovalModalOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const activityScrollRef = useRef<HTMLDivElement>(null);

  // 1. Initial Task Hydration
  const loadTask = useCallback(async () => {
    try {
      const data = await api.tasks.get(id);
      setTask(data);
      if (data.status === "WAITING_APPROVAL") {
        setApprovalModalOpen(true);
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to load mission details");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadTask();
  }, [loadTask]);

  // 2. Elapsed Timer
  useEffect(() => {
    if (!task) return;
    const isTerminal = ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", "CANCELLED"].includes(task.status);
    if (isTerminal) {
      if (task.completed_at && task.created_at) {
        const diff = (new Date(task.completed_at).getTime() - new Date(task.created_at).getTime()) / 1000;
        setElapsedSeconds(Math.max(0, Math.round(diff)));
      }
      return;
    }

    const interval = setInterval(() => {
      const diff = (Date.now() - new Date(task.created_at).getTime()) / 1000;
      setElapsedSeconds(Math.max(0, Math.round(diff)));
    }, 1000);

    return () => clearInterval(interval);
  }, [task]);

  // 3. SSE Live Events Stream
  useEffect(() => {
    if (!task) return;
    const isTerminal = ["COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", "CANCELLED"].includes(task.status);

    // If terminal and result already hydrated, no need to open stream
    if (isTerminal && task.result) {
      return;
    }

    const sseUrl = api.tasks.getEventsUrl(id);
    const es = new EventSource(sseUrl, { withCredentials: true });
    eventSourceRef.current = es;

    const handleEvent = (event: MessageEvent) => {
      try {
        const data: TaskEvent = JSON.parse(event.data);
        setEvents((prev) => {
          if (prev.some((e) => e.id === data.id)) return prev;
          return [...prev, data];
        });

        // Trigger task refresh on structural milestone events
        if (
          [
            "PLAN_CREATED",
            "STEP_COMPLETED",
            "APPROVAL_REQUIRED",
            "APPROVAL_RESOLVED",
            "VERIFICATION_COMPLETED",
            "TASK_COMPLETED",
            "TASK_FAILED",
            "TASK_CANCELLED",
          ].includes(data.event_type)
        ) {
          loadTask();
        }

        if (data.event_type === "APPROVAL_REQUIRED") {
          setApprovalModalOpen(true);
        }

        if (["TASK_COMPLETED", "TASK_FAILED", "TASK_CANCELLED"].includes(data.event_type)) {
          es.close();
        }
      } catch {
        // Heartbeats or ping comments
      }
    };

    es.onmessage = handleEvent;

    // Listen to custom event types
    const eventTypes = [
      "TASK_STARTED",
      "PLAN_CREATED",
      "STEP_STARTED",
      "TOOL_STARTED",
      "TOOL_COMPLETED",
      "TOOL_FAILED",
      "RETRY",
      "STEP_COMPLETED",
      "APPROVAL_REQUIRED",
      "APPROVAL_RESOLVED",
      "VERIFICATION_STARTED",
      "VERIFICATION_COMPLETED",
      "TASK_COMPLETED",
      "TASK_FAILED",
      "TASK_CANCELLED",
    ];

    eventTypes.forEach((type) => es.addEventListener(type, handleEvent));

    es.onerror = () => {
      // Reconnect handled automatically by EventSource
    };

    return () => {
      es.close();
    };
  }, [id, task, loadTask]);

  // Auto-scroll activity feed to bottom
  useEffect(() => {
    if (activityScrollRef.current) {
      activityScrollRef.current.scrollTop = activityScrollRef.current.scrollHeight;
    }
  }, [events]);

  // 4. Approval Actions
  const handleApprove = async () => {
    setActionLoading(true);
    try {
      await api.tasks.approve(id);
      toast.success("Human authorization granted. Execution resuming.");
      setApprovalModalOpen(false);
      loadTask();
    } catch (err: any) {
      toast.error(err.message || "Failed to approve task");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    try {
      await api.tasks.reject(id);
      toast.info("Step rejected by operator. Skipping step.");
      setApprovalModalOpen(false);
      loadTask();
    } catch (err: any) {
      toast.error(err.message || "Failed to reject task");
    } finally {
      setActionLoading(false);
    }
  };

  // 5. Retry Action
  const handleRetry = async () => {
    setActionLoading(true);
    try {
      await api.tasks.retry(id);
      toast.success("Retry initiated. TaskPilot is resuming execution.");
      loadTask();
    } catch (err: any) {
      toast.error(err.message || "Failed to retry task");
    } finally {
      setActionLoading(false);
    }
  };

  // 6. Copy Markdown Report
  const handleCopyMarkdown = () => {
    if (!task?.result?.markdown) return;
    navigator.clipboard.writeText(task.result.markdown);
    setCopied(true);
    toast.success("Mission report copied to clipboard");
    setTimeout(() => setCopied(false), 2000);
  };

  // 7. Download Markdown Report
  const handleDownloadReport = () => {
    if (!task?.result?.markdown) return;
    const blob = new Blob([task.result.markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `taskpilot-report-${id.slice(0, 8)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Report downloaded");
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-3">
        <Compass className="h-8 w-8 text-brass animate-spin" />
        <p className="text-xs font-mono text-muted-foreground uppercase">
          CALIBRATING OBSERVATORY FEED...
        </p>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="p-12 text-center space-y-4">
        <AlertCircle className="h-10 w-10 text-clay mx-auto" />
        <h2 className="font-serif text-xl font-bold">Mission Not Found</h2>
        <Link href="/app">
          <Button variant="secondary" size="sm">Return to Command Station</Button>
        </Link>
      </div>
    );
  }

  const pendingApproval = task.approvals?.find((a) => a.status === "PENDING");
  const isRunning = ["PLANNING", "RUNNING", "VERIFYING"].includes(task.status);
  const isFailed = task.status === "FAILED";
  const isCompleted = ["COMPLETED", "COMPLETED_WITH_WARNINGS"].includes(task.status);

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Top Breadcrumb & Status Instrument */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
          <Link href="/app" className="hover:text-foreground flex items-center gap-1">
            <ArrowLeft className="h-3.5 w-3.5" /> Back
          </Link>
          <span>/</span>
          <span>MISSION {task.id.slice(0, 8)}</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-surface border border-border text-xs font-mono">
            <Clock className="h-3.5 w-3.5 text-brass" />
            <span className="text-muted-foreground">ELAPSED:</span>
            <span className="text-foreground font-bold">{formatDuration(elapsedSeconds)}</span>
          </div>

          <Badge
            variant={
              isCompleted
                ? "sage"
                : task.status === "WAITING_APPROVAL"
                ? "clay"
                : isFailed
                ? "clay"
                : "default"
            }
            className="text-xs px-2.5 py-1"
          >
            {isRunning && <span className="h-2 w-2 rounded-full bg-brass animate-pulse-subtle mr-1.5" />}
            {task.status}
          </Badge>
        </div>
      </div>

      {/* Goal Card */}
      <div className="p-6 rounded-xl bg-surface border border-border shadow-sm space-y-2">
        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-brass">
          <Compass className="h-3.5 w-3.5" />
          <span>ORIGINAL OPERATOR DIRECTIVE</span>
        </div>
        <h1 className="font-serif text-xl md:text-2xl font-bold text-foreground leading-snug">
          {task.goal}
        </h1>
        <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground pt-1">
          <span>INITIALIZED: {formatDate(task.created_at)}</span>
          {task.plan && <span>STEPS PLANNED: {task.plan.steps.length}</span>}
        </div>
      </div>

      {/* High-Risk Approval Alert Banner */}
      {task.status === "WAITING_APPROVAL" && pendingApproval && (
        <div className="p-4 rounded-lg bg-clay/10 border border-clay/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-in fade-in duration-300">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-clay shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-mono uppercase font-bold text-clay tracking-wider">
                AUTHORIZATION REQUIRED BEFORE SENSITIVE EXECUTION
              </p>
              <p className="text-sm font-sans text-foreground">
                {pendingApproval.action_summary}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button size="sm" onClick={() => setApprovalModalOpen(true)} className="font-sans">
              Review & Authorize
            </Button>
          </div>
        </div>
      )}

      {/* Failure Banner with Retry Button */}
      {isFailed && (
        <div className="p-4 rounded-lg bg-clay/10 border border-clay/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-clay shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-mono uppercase font-bold text-clay tracking-wider">
                MISSION HALTED: STEP COULD NOT BE COMPLETED
              </p>
              <p className="text-sm font-sans text-foreground">
                {task.error_message || "A tool execution encountered an unrecoverable failure after retries."}
              </p>
            </div>
          </div>
          <Button
            size="sm"
            onClick={handleRetry}
            disabled={actionLoading}
            className="font-sans shrink-0 bg-clay hover:bg-red-700 text-white"
          >
            <RotateCw className="h-3.5 w-3.5 mr-1.5" />
            Retry Mission
          </Button>
        </div>
      )}

      {/* Main Grid: Steps Timeline (Left) & Tabs (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Live Step Timeline & Activity Feed (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Step Timeline Card */}
          <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-brass" />
                <h3 className="font-serif text-sm font-bold uppercase tracking-wider text-foreground">
                  Execution DAG
                </h3>
              </div>
              <span className="text-[10px] font-mono text-muted-foreground">
                {task.steps?.filter((s) => s.status === "COMPLETED").length || 0} /{" "}
                {task.steps?.length || 0} COMPLETE
              </span>
            </div>

            {task.steps?.length === 0 ? (
              <div className="py-6 text-center text-xs font-mono text-muted-foreground animate-pulse">
                FORMULATING DEPENDENCY GRAPH...
              </div>
            ) : (
              <div className="space-y-3">
                {task.steps?.map((step, idx) => {
                  const isStepActive = step.status === "RUNNING";
                  const isStepCompleted = step.status === "COMPLETED";
                  const isStepWaiting = step.status === "WAITING_APPROVAL";
                  const isStepFailed = step.status === "FAILED";

                  return (
                    <div
                      key={step.id}
                      className={`p-3.5 rounded-lg border transition-all text-xs ${
                        isStepActive
                          ? "bg-surface-secondary border-brass/60 shadow-sm"
                          : isStepCompleted
                          ? "bg-surface border-border opacity-90"
                          : isStepWaiting
                          ? "bg-clay/10 border-clay/40"
                          : isStepFailed
                          ? "bg-clay/10 border-clay/40"
                          : "bg-surface/50 border-border/60 text-muted-foreground"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-bold text-brass">
                            0{idx + 1}
                          </span>
                          <span className="font-mono uppercase font-semibold text-foreground">
                            {step.tool_name}
                          </span>
                        </div>

                        <Badge
                          variant={
                            isStepCompleted
                              ? "sage"
                              : isStepActive
                              ? "default"
                              : isStepWaiting
                              ? "clay"
                              : isStepFailed
                              ? "clay"
                              : "outline"
                          }
                          className="text-[10px]"
                        >
                          {isStepActive && (
                            <span className="h-1.5 w-1.5 rounded-full bg-brass animate-pulse mr-1" />
                          )}
                          {step.status}
                        </Badge>
                      </div>

                      <p className="text-xs font-sans text-foreground/90 line-clamp-2">
                        {step.description}
                      </p>

                      <div className="flex items-center justify-between pt-2 mt-2 border-t border-border/50 text-[10px] font-mono text-muted-foreground">
                        <span>RISK: {step.risk_level}</span>
                        {step.retry_count > 0 && (
                          <span className="text-ochre">RETRIES: {step.retry_count}</span>
                        )}
                        {step.completed_at && step.started_at && (
                          <span>
                            {Math.round(
                              (new Date(step.completed_at).getTime() -
                                new Date(step.started_at).getTime()) /
                                1000
                            )}
                            s
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Live Agent Activity Feed */}
          <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-brass" />
                <h3 className="font-serif text-sm font-bold uppercase tracking-wider text-foreground">
                  Live Activity Feed
                </h3>
              </div>
              <span className="text-[10px] font-mono text-sage flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-sage animate-ping" />
                STREAMING
              </span>
            </div>

            <div
              ref={activityScrollRef}
              className="h-60 overflow-y-auto space-y-2 pr-1 font-mono text-xs"
            >
              {events.length === 0 ? (
                <p className="text-muted-foreground text-xs py-4 text-center">
                  Awaiting telemetry events...
                </p>
              ) : (
                events.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-2 rounded bg-surface-secondary/70 border border-border/50 text-[11px] space-y-0.5"
                  >
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <span className="text-brass font-bold">{ev.event_type}</span>
                      <span>{new Date(ev.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-foreground/90 font-sans leading-snug">
                      {ev.message}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Result, Trace, Verification Tabs (7 cols) */}
        <div className="lg:col-span-7">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid grid-cols-3 w-full">
              <TabsTrigger value="result" className="text-xs">
                Mission Report
              </TabsTrigger>
              <TabsTrigger value="trace" className="text-xs">
                Execution Trace
              </TabsTrigger>
              <TabsTrigger value="verification" className="text-xs">
                Verification ({task.result?.verification_report?.checks.length || 0})
              </TabsTrigger>
            </TabsList>

            {/* TAB 1: RESULT */}
            <TabsContent value="result" className="space-y-6">
              {task.result ? (
                <div className="space-y-6">
                  {/* Action Bar */}
                  <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border">
                    <span className="text-xs font-mono text-muted-foreground">
                      REPORT READY • {task.result.sources?.length || 0} SOURCES GROUNDED
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleCopyMarkdown}
                        className="font-mono text-xs h-8"
                      >
                        {copied ? <Check className="h-3.5 w-3.5 mr-1 text-sage" /> : <Copy className="h-3.5 w-3.5 mr-1" />}
                        {copied ? "Copied" : "Copy Markdown"}
                      </Button>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={handleDownloadReport}
                        className="font-mono text-xs h-8"
                      >
                        <Download className="h-3.5 w-3.5 mr-1" />
                        Download .md
                      </Button>
                    </div>
                  </div>

                  {/* Dynamic Metrics Cards */}
                  {task.result.cards && task.result.cards.length > 0 && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {task.result.cards.map((c, i) => (
                        <div key={i} className="p-4 rounded-lg bg-surface border border-border space-y-1">
                          <p className="text-[10px] font-mono uppercase text-muted-foreground tracking-wider">
                            {c.title}
                          </p>
                          <p className="font-serif text-2xl font-bold text-brass">{c.value}</p>
                          {c.description && (
                            <p className="text-xs text-muted-foreground font-sans">{c.description}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Chart Rendering if chart_data exists */}
                  {task.result.chart_data && task.result.chart_data.data && (
                    <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
                      <div className="flex items-center gap-2">
                        <Activity className="h-4 w-4 text-brass" />
                        <h4 className="font-serif text-sm font-bold text-foreground">
                          {task.result.chart_data.title}
                        </h4>
                      </div>
                      <div className="h-56 w-full pt-2">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={task.result.chart_data.data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                            <XAxis
                              dataKey="name"
                              tick={{ fill: "#8B8778", fontSize: 10, fontFamily: "monospace" }}
                            />
                            <YAxis
                              tick={{ fill: "#8B8778", fontSize: 10, fontFamily: "monospace" }}
                            />
                            <RechartsTooltip
                              contentStyle={{
                                backgroundColor: "#12151A",
                                borderColor: "rgba(255,255,255,0.1)",
                                borderRadius: 6,
                                fontSize: 11,
                                fontFamily: "monospace",
                              }}
                            />
                            <Bar dataKey="value" fill="#C8A15A" radius={[4, 4, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}

                  {/* Tables Rendering */}
                  {task.result.tables && task.result.tables.length > 0 && (
                    <div className="space-y-4">
                      {task.result.tables.map((table, tIdx) => (
                        <div key={tIdx} className="rounded-xl border border-border bg-surface overflow-hidden">
                          <div className="p-4 border-b border-border bg-surface-secondary/40">
                            <h4 className="font-serif text-sm font-bold text-foreground">
                              {table.title}
                            </h4>
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs text-left">
                              <thead className="bg-surface-secondary/70 border-b border-border font-mono uppercase text-muted-foreground">
                                <tr>
                                  {table.headers.map((h) => (
                                    <th key={h} className="p-3 font-semibold">
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-border/60">
                                {table.rows.map((row, rIdx) => (
                                  <tr key={rIdx} className="hover:bg-surface-secondary/30 transition-colors">
                                    {table.headers.map((h) => (
                                      <td key={h} className="p-3 text-foreground font-sans">
                                        {String(row[h] ?? "")}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Markdown Report Body */}
                  <div className="p-6 md:p-8 rounded-xl bg-surface border border-border prose dark:prose-invert max-w-none text-sm font-sans leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {task.result.markdown}
                    </ReactMarkdown>
                  </div>

                  {/* Citations & Sources Links */}
                  {task.result.sources && task.result.sources.length > 0 && (
                    <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
                      <h4 className="font-serif text-sm font-bold uppercase tracking-wider text-foreground">
                        Verified Sources & Citations
                      </h4>
                      <div className="space-y-2">
                        {task.result.sources.map((src, idx) => (
                          <a
                            key={idx}
                            href={src.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-between p-2.5 rounded bg-surface-secondary hover:bg-surface border border-border text-xs group transition-colors"
                          >
                            <span className="font-medium text-foreground group-hover:text-brass truncate max-w-[80%]">
                              {src.title || src.url}
                            </span>
                            <div className="flex items-center gap-1.5 text-muted-foreground text-[11px] font-mono shrink-0">
                              <span>{src.domain || "web"}</span>
                              <ExternalLink className="h-3 w-3" />
                            </div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-12 text-center rounded-xl border border-dashed border-border bg-surface/50 text-muted-foreground space-y-3">
                  <Compass className={`h-8 w-8 text-brass mx-auto ${isRunning ? "animate-spin" : ""}`} />
                  <h3 className="font-serif text-lg font-bold text-foreground">
                    {isRunning ? "Synthesizing Mission Report..." : "No Report Generated"}
                  </h3>
                  <p className="text-xs font-sans max-w-md mx-auto">
                    {isRunning
                      ? "TaskPilot is executing autonomous steps in dependency order. The final verified report will compile once all steps pass validation."
                      : "Task halted before completing report synthesis."}
                  </p>
                </div>
              )}
            </TabsContent>

            {/* TAB 2: AGENT TRACE */}
            <TabsContent value="trace" className="space-y-4">
              <div className="p-5 rounded-xl bg-surface border border-border space-y-6 font-mono text-xs">
                <div className="space-y-2 pb-4 border-b border-border">
                  <span className="text-[10px] text-brass uppercase font-bold">NODE 01 / DIRECTIVE</span>
                  <div className="p-3 rounded bg-surface-secondary border border-border text-foreground font-sans">
                    {task.goal}
                  </div>
                </div>

                <div className="space-y-2 pb-4 border-b border-border">
                  <span className="text-[10px] text-brass uppercase font-bold">NODE 02 / PLAN SPECIFICATION</span>
                  <pre className="p-3 rounded bg-surface-secondary border border-border overflow-x-auto text-[11px] text-muted-foreground">
                    {JSON.stringify(task.plan, null, 2)}
                  </pre>
                </div>

                <div className="space-y-3 pb-4 border-b border-border">
                  <span className="text-[10px] text-brass uppercase font-bold">NODE 03 / TOOL EXECUTION LOGS</span>
                  {task.tool_executions?.length === 0 ? (
                    <p className="text-muted-foreground">No tool executions recorded yet.</p>
                  ) : (
                    task.tool_executions?.map((ex, i) => (
                      <div key={ex.id} className="p-3 rounded bg-surface-secondary border border-border space-y-2">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-bold text-foreground">
                            CALL #{i + 1}: {ex.tool_name}
                          </span>
                          <span className="text-muted-foreground">
                            {ex.duration_ms.toFixed(1)}ms • Attempt {ex.attempt}
                          </span>
                        </div>
                        <div className="space-y-1">
                          <p className="text-[10px] text-muted-foreground uppercase">Parameters:</p>
                          <pre className="p-2 rounded bg-background border border-border overflow-x-auto text-[10px]">
                            {JSON.stringify(ex.inputs, null, 2)}
                          </pre>
                        </div>
                        <div className="space-y-1">
                          <p className="text-[10px] text-muted-foreground uppercase">Output:</p>
                          <pre className="p-2 rounded bg-background border border-border overflow-x-auto text-[10px] text-sage">
                            {JSON.stringify(ex.output, null, 2)}
                          </pre>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                <div className="space-y-2">
                  <span className="text-[10px] text-brass uppercase font-bold">NODE 04 / FINAL VERIFICATION</span>
                  <pre className="p-3 rounded bg-surface-secondary border border-border overflow-x-auto text-[11px] text-muted-foreground">
                    {JSON.stringify(task.result?.verification_report || "Pending verification", null, 2)}
                  </pre>
                </div>
              </div>
            </TabsContent>

            {/* TAB 3: VERIFICATION */}
            <TabsContent value="verification" className="space-y-4">
              <div className="p-6 rounded-xl bg-surface border border-border space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div>
                    <h3 className="font-serif text-base font-bold text-foreground">
                      Verification Inspector
                    </h3>
                    <p className="text-xs text-muted-foreground font-sans">
                      Automated structural rule evaluation and goal consistency guarantees.
                    </p>
                  </div>
                  <Badge
                    variant={
                      task.result?.verification_report?.passed ? "sage" : "clay"
                    }
                  >
                    {task.result?.verification_report?.passed ? "ALL CHECKS PASSED" : "PENDING / INCOMPLETE"}
                  </Badge>
                </div>

                <div className="space-y-3">
                  {task.result?.verification_report?.checks?.map((check, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-lg bg-surface-secondary border border-border flex items-start gap-3"
                    >
                      {check.passed ? (
                        <CheckCircle2 className="h-5 w-5 text-sage shrink-0 mt-0.5" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-ochre shrink-0 mt-0.5" />
                      )}
                      <div className="space-y-0.5">
                        <p className="text-xs font-mono font-bold uppercase text-foreground">
                          {check.name}
                        </p>
                        <p className="text-xs text-muted-foreground font-sans">
                          {check.detail}
                        </p>
                      </div>
                    </div>
                  )) || (
                    <p className="text-xs font-mono text-muted-foreground py-4 text-center">
                      Verification evaluates automatically once tool execution completes.
                    </p>
                  )}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Human Approval Modal Dialog */}
      <Dialog open={approvalModalOpen} onOpenChange={setApprovalModalOpen}>
        <DialogContent className="sm:max-w-md font-sans">
          <DialogHeader>
            <div className="flex items-center gap-2 text-clay mb-1">
              <ShieldAlert className="h-5 w-5" />
              <span className="text-xs font-mono font-bold uppercase tracking-wider">
                HUMAN-IN-THE-LOOP GATE
              </span>
            </div>
            <DialogTitle className="font-serif text-xl">TaskPilot Needs Your Approval</DialogTitle>
            <DialogDescription className="text-xs font-sans text-muted-foreground">
              A high-impact action has been planned. The engine has paused all execution until you explicitly authorize or reject this step.
            </DialogDescription>
          </DialogHeader>

          {pendingApproval && (
            <div className="p-3 rounded-lg bg-surface-secondary border border-border space-y-2 text-xs font-mono">
              <div>
                <span className="text-muted-foreground uppercase text-[10px]">TOOL:</span>
                <p className="font-bold text-foreground">{pendingApproval.tool_name}</p>
              </div>
              <div>
                <span className="text-muted-foreground uppercase text-[10px]">INTENDED ACTION:</span>
                <p className="font-sans text-foreground">{pendingApproval.action_summary}</p>
              </div>
              <div>
                <span className="text-muted-foreground uppercase text-[10px]">INPUT PAYLOAD:</span>
                <pre className="p-2 rounded bg-background border border-border overflow-x-auto text-[10px] text-muted-foreground mt-1 max-h-32">
                  {JSON.stringify(pendingApproval.inputs, null, 2)}
                </pre>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0 mt-4">
            <Button
              variant="secondary"
              onClick={handleReject}
              disabled={actionLoading}
              className="w-full sm:w-auto font-sans"
            >
              Reject Action
            </Button>
            <Button
              onClick={handleApprove}
              disabled={actionLoading}
              className="w-full sm:w-auto font-sans"
            >
              {actionLoading ? "Authorizing..." : "Approve & Execute"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
