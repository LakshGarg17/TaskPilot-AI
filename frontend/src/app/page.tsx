"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Compass,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Workflow,
  Search,
  Cpu,
  Lock,
  Layers,
  Sparkles,
  Terminal,
  ExternalLink,
  Check,
  Circle,
  Clock,
  Menu,
  X,
  FileSpreadsheet,
  Mail,
  BarChart3,
  Bot,
  Sliders,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeStage, setActiveStage] = useState(3); // 0-based: 0, 1, 2, 3 (Verify), 4 (Complete)

  // Gentle looping animation that cycles through stages
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStage((prev) => (prev >= 4 ? 0 : prev + 1));
    }, 3500);
    return () => clearInterval(timer);
  }, []);

  const demoGoal =
    "Research the top AI hackathons currently accepting applications, compare their deadlines, prizes and requirements, and create a concise report.";

  const stages = [
    {
      num: "01",
      name: "Understand",
      status: "Goal understood",
      detail: "Constraints & entities parsed",
      icon: CheckCircle2,
    },
    {
      num: "02",
      name: "Plan",
      status: "Dependency graph generated",
      detail: "3-step optimal DAG resolved",
      icon: CheckCircle2,
    },
    {
      num: "03",
      name: "Execute",
      status: "Web Search, Extraction, Comparison",
      detail: "3 real sandboxed tools run",
      icon: CheckCircle2,
    },
    {
      num: "04",
      name: "Verify",
      status: "Verification in progress",
      detail: "Validating web citations & tables",
      icon: Sparkles,
    },
    {
      num: "05",
      name: "Complete",
      status: "Report ready",
      detail: "Structured briefing compiled",
      icon: Circle,
    },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col selection:bg-brass selection:text-black">
      {/* 1. Navbar */}
      <nav className="border-b border-border/80 bg-background/85 backdrop-blur-md sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded bg-brass/10 border border-brass/30 flex items-center justify-center text-brass shadow-sm">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <span className="font-serif font-bold text-xl tracking-tight text-foreground">
                TaskPilot <span className="text-brass">AI</span>
              </span>
              <span className="hidden sm:inline-block ml-3 text-[10px] font-mono uppercase text-muted-foreground tracking-widest border-l border-border pl-3">
                Autonomous Workflow Engine
              </span>
            </div>
          </div>

          {/* Desktop Nav Items */}
          <div className="hidden md:flex items-center gap-5">
            <Link href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Features
            </Link>
            <Link href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              How It Works
            </Link>
            <Link href="#use-cases" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Use Cases
            </Link>
            <Link href="#safety" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Safety
            </Link>
            <Link href="#architecture" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Architecture
            </Link>
            <div className="h-4 w-px bg-border mx-1" />
            <ThemeToggle />
            <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground">
              Sign In
            </Link>
            <Link href="/signup">
              <Button size="sm" className="font-sans font-semibold">
                Try TaskPilot <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-3">
            <ThemeToggle />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-muted-foreground hover:text-foreground border border-border rounded-md"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-4 pt-4 border-t border-border flex flex-col gap-3 font-sans pb-2">
            <Link
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              Features
            </Link>
            <Link
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              How It Works
            </Link>
            <Link
              href="#use-cases"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              Use Cases
            </Link>
            <Link
              href="#safety"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              Safety
            </Link>
            <Link
              href="#architecture"
              onClick={() => setMobileMenuOpen(false)}
              className="px-2 py-1 text-sm text-muted-foreground hover:text-foreground"
            >
              Architecture
            </Link>
            <div className="pt-2 border-t border-border flex flex-col gap-2">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                <Button variant="outline" className="w-full justify-center">
                  Sign In
                </Button>
              </Link>
              <Link href="/signup" onClick={() => setMobileMenuOpen(false)}>
                <Button className="w-full justify-center">
                  Try TaskPilot Free
                </Button>
              </Link>
            </div>
          </div>
        )}
      </nav>

      {/* 2. Hero Section */}
      <section className="py-16 md:py-24 px-6 border-b border-border relative overflow-hidden">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div>
            <Badge variant="default" className="text-xs py-1 px-3">
              AUTONOMOUS • VERIFIABLE • HUMAN-CONTROLLED
            </Badge>
          </div>
          <h1 className="font-serif text-4xl sm:text-6xl md:text-7xl font-bold tracking-tight text-foreground leading-[1.12]">
            Your AI Agent for <br />
            <span className="italic font-normal text-brass">Everyday Digital Work</span>
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-muted-foreground font-sans max-w-2xl mx-auto leading-relaxed">
            State your goal in natural language. TaskPilot plans the work, executes the right tools, verifies the result, and asks for your approval before sensitive actions.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link href="/signup">
              <Button size="lg" className="w-full sm:w-auto text-base px-8 font-semibold">
                Try TaskPilot Free →
              </Button>
            </Link>
            <Link href="#demo">
              <Button variant="secondary" size="lg" className="w-full sm:w-auto text-base">
                View Live Demo
              </Button>
            </Link>
          </div>

          {/* 3. Live Agent Panel ("ACTIVE AGENT TASK" Card) */}
          <div id="demo" className="mt-12 p-5 md:p-7 rounded-xl border border-border bg-surface shadow-2xl text-left font-mono">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between pb-4 border-b border-border gap-2">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brass opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-brass" />
                </span>
                <span className="text-xs font-bold text-foreground tracking-wider uppercase">
                  ACTIVE AGENT TASK
                </span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                <span>STAGE: <strong className="text-brass">{stages[activeStage].name.toUpperCase()}</strong></span>
                <span className="border-l border-border pl-3">ID: TP-8849-AGENTIC</span>
              </div>
            </div>

            {/* Goal Card */}
            <div className="py-4 border-b border-border">
              <div className="text-[11px] text-brass uppercase font-bold tracking-wider mb-1">
                GOAL OBJECTIVE:
              </div>
              <p className="text-sm font-sans text-foreground leading-relaxed">
                &ldquo;{demoGoal}&rdquo;
              </p>
            </div>

            {/* 5-Stage Live Timeline */}
            <div className="pt-4 space-y-3">
              <div className="text-[10px] text-muted-foreground uppercase tracking-widest">
                EXECUTION PIPELINE
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5">
                {stages.map((stage, idx) => {
                  const isDone = idx < activeStage;
                  const isActive = idx === activeStage;
                  const isWaiting = idx > activeStage;

                  return (
                    <div
                      key={stage.num}
                      className={`p-3 rounded-lg border transition-all duration-300 ${
                        isActive
                          ? "border-brass bg-brass/10 shadow-sm"
                          : isDone
                          ? "border-sage/40 bg-surface-secondary/70"
                          : "border-border bg-surface-secondary/20 opacity-60"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-bold text-muted-foreground">
                          {stage.num}
                        </span>
                        {isDone && <CheckCircle2 className="h-3.5 w-3.5 text-sage" />}
                        {isActive && (
                          <span className="h-2 w-2 rounded-full bg-brass animate-pulse" />
                        )}
                        {isWaiting && <Circle className="h-3 w-3 text-muted-foreground/50" />}
                      </div>
                      <p className="font-semibold text-foreground text-xs font-sans">
                        {stage.name}
                      </p>
                      <p
                        className={`text-[10px] mt-1 line-clamp-1 ${
                          isActive
                            ? "text-brass font-medium"
                            : isDone
                            ? "text-sage"
                            : "text-muted-foreground"
                        }`}
                      >
                        {isDone ? "✓ " + stage.status : isActive ? "◉ " + stage.status : "○ " + stage.status}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Features Section */}
      <section id="features" className="py-20 px-6 border-b border-border bg-surface-secondary/20">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest text-brass">Key Capabilities</span>
            <h2 className="font-serif text-3xl md:text-4xl font-bold">Engineered for Autonomous Reliability</h2>
            <p className="text-muted-foreground max-w-xl mx-auto text-sm">
              Not a conversational toy. Every component is architected for transparent, verifiable mission execution.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-brass/10 border border-brass/30 flex items-center justify-center text-brass">
                <Workflow className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Autonomous Planning</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Decomposes natural language requests into optimal Directed Acyclic Graphs (DAGs) with dynamic input mapping and cycle prevention.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-brass/10 border border-brass/30 flex items-center justify-center text-brass">
                <Layers className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Multi-Step Execution</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Orchestrates complex chains of dependencies, passing outputs forward and maintaining atomic database state transitions.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-brass/10 border border-brass/30 flex items-center justify-center text-brass">
                <Cpu className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Tool Integration</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                7 native sandboxed tools: web search, SSRF-safe HTML extractor, AST-whitelisted safe calculator, summarizer, tables, and email flows.
              </p>
            </div>

            {/* Card 4 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-sage/10 border border-sage/30 flex items-center justify-center text-sage">
                <ShieldCheck className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Result Verification</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Two-stage validation engine checks required fields, live web citations, URL well-formedness, and LLM consistency.
              </p>
            </div>

            {/* Card 5 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-ochre/10 border border-ochre/30 flex items-center justify-center text-ochre">
                <Lock className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Human Approval</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                High-risk actions pause execution automatically with full parameter inspection until an operator clicks Approve or Reject.
              </p>
            </div>

            {/* Card 6 */}
            <div className="p-6 rounded-lg bg-surface border border-border space-y-3">
              <div className="h-9 w-9 rounded bg-brass/10 border border-brass/30 flex items-center justify-center text-brass">
                <Terminal className="h-4.5 w-4.5" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-foreground">Execution Trace</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Audit every decision, tool call, error, and retry event. Transparent reasoning without exposing confidential chain-of-thought.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. How It Works Section */}
      <section id="how-it-works" className="py-20 px-6 border-b border-border">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest text-brass">The Lifecycle</span>
            <h2 className="font-serif text-3xl md:text-4xl font-bold">Understand → Plan → Execute → Verify</h2>
            <p className="text-muted-foreground max-w-xl mx-auto text-sm">
              Real agentic architecture where every stage is auditable, deterministic, and streamed via Server-Sent Events.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-lg bg-surface border border-border relative">
              <div className="font-mono text-xs text-brass font-bold mb-2">01 / UNDERSTAND</div>
              <h3 className="font-serif text-lg font-bold mb-2 text-foreground">Goal Ingestion</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Analyzes natural language intent, determines required parameters, identifies constraints, and chooses optimal tool sets.
              </p>
            </div>
            <div className="p-6 rounded-lg bg-surface border border-border relative">
              <div className="font-mono text-xs text-brass font-bold mb-2">02 / PLAN</div>
              <h3 className="font-serif text-lg font-bold mb-2 text-foreground">DAG Construction</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Builds an acyclic dependency graph, validates tool compatibility in the registry, and executes self-repair loops if invalid.
              </p>
            </div>
            <div className="p-6 rounded-lg bg-surface border border-border relative">
              <div className="font-mono text-xs text-brass font-bold mb-2">03 / EXECUTE</div>
              <h3 className="font-serif text-lg font-bold mb-2 text-foreground">Sandboxed Runs</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Runs steps with up to 3 automatic retries. Low-risk operations run automatically; sensitive actions pause for human sign-off.
              </p>
            </div>
            <div className="p-6 rounded-lg bg-surface border border-border relative">
              <div className="font-mono text-xs text-brass font-bold mb-2">04 / VERIFY</div>
              <h3 className="font-serif text-lg font-bold mb-2 text-foreground">Output Assurance</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Runs deterministic schema and citation integrity checks before marking the mission completed with interactive reports.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. Use Cases Section */}
      <section id="use-cases" className="py-20 px-6 border-b border-border bg-surface-secondary/20">
        <div className="max-w-6xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest text-brass">Practical Applications</span>
            <h2 className="font-serif text-3xl md:text-4xl font-bold">Built for Real-World Knowledge Work</h2>
            <p className="text-muted-foreground max-w-xl mx-auto text-sm">
              From competitive intelligence to executive communications, TaskPilot handles multi-step digital work.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <Search className="h-4 w-4" />
                <span className="font-bold">RESEARCH & COMPARE</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">Market & Tech Intelligence</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Discovers live hackathons, compares cloud pricing structures, and summarizes competitive features with citations.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <BarChart3 className="h-4 w-4" />
                <span className="font-bold">DATA ANALYSIS</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">Safe Statistical Computation</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Calculates metrics, medians, and compound growth rates using safe AST math evaluation without dangerous eval().
              </p>
            </div>

            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <FileSpreadsheet className="h-4 w-4" />
                <span className="font-bold">REPORT GENERATION</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">Executive Briefings & Tables</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Synthesizes complex multi-source findings into structured tables, downloadable Markdown reports, and interactive charts.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <Mail className="h-4 w-4" />
                <span className="font-bold">EMAIL DRAFTING</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">Targeted Communications</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Drafts polished emails aligned with technical findings, allowing instant review and modification before sending.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <ExternalLink className="h-4 w-4" />
                <span className="font-bold">WEB RESEARCH</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">Deep Content Scraping</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Fetches raw web documentation, parses clean text, and filters out boilerplate with full socket-level SSRF safeguards.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-surface border border-border space-y-2">
              <div className="flex items-center gap-2 text-brass font-mono text-xs">
                <Sliders className="h-4 w-4" />
                <span className="font-bold">WORKFLOW AUTOMATION</span>
              </div>
              <h4 className="font-serif font-semibold text-foreground text-sm">End-to-End Task Chains</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Connects search, computation, data structuring, and human sign-off into seamless automated pipelines.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Safety / Human Control Section */}
      <section id="safety" className="py-20 px-6 border-b border-border">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <Badge variant="ochre">SAFETY & HUMAN CONTROL</Badge>
            <h2 className="font-serif text-3xl md:text-4xl font-bold text-foreground">
              Autonomous Execution, <br />
              <span className="italic font-normal text-brass">Uncompromising Human Control</span>
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed font-sans">
              Low-risk exploratory actions execute automatically at machine speed. Irreversible operations (such as sending external communications or modifying data) immediately pause the orchestrator and require explicit operator authorization.
            </p>

            <div className="space-y-3 font-sans text-sm">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-sage shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground">Policy-Governed Risk Levels:</strong>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Tools are statically categorized into LOW, MEDIUM, and HIGH risk policies.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-sage shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground">Full Payload Transparency:</strong>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Before approving, view recipient addresses, message content, and exact execution arguments.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-sage shrink-0 mt-0.5" />
                <div>
                  <strong className="text-foreground">Socket-Level SSRF Hardening:</strong>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Pre-flight DNS validation prevents access to AWS metadata, RFC 1918 subnets, and loopback IPs.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Mock Approval Card */}
          <div className="p-6 rounded-xl border border-ochre/40 bg-surface shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-ochre animate-pulse" />
                <span className="font-mono text-xs font-bold text-foreground uppercase tracking-wider">
                  Human Gatekeeper
                </span>
              </div>
              <Badge variant="clay">APPROVAL REQUIRED</Badge>
            </div>

            <div className="p-4 rounded-lg bg-surface-secondary border border-border space-y-2 font-mono text-xs">
              <div className="flex justify-between text-muted-foreground text-[11px]">
                <span>TOOL: <strong className="text-foreground">email_send</strong></span>
                <span>RISK: <strong className="text-clay">HIGH</strong></span>
              </div>
              <p className="font-sans text-xs text-foreground font-medium pt-1">
                Dispatch the finalized notification to team@example.com summarizing AI hackathon findings.
              </p>
              <div className="p-2.5 rounded bg-background border border-border text-[11px] text-muted-foreground font-mono mt-2">
                <div>Recipient: team@example.com</div>
                <div>Subject: Upcoming AI Hackathons Strategy</div>
              </div>
            </div>

            <div className="flex gap-3 pt-1">
              <Button size="sm" className="w-full bg-brass text-black font-semibold hover:bg-brass-hover">
                Approve Action
              </Button>
              <Button size="sm" variant="secondary" className="w-full">
                Reject Action
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 8. Technology & Architecture Section */}
      <section id="architecture" className="py-20 px-6 border-b border-border bg-surface-secondary/20">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-widest text-brass">Under The Hood</span>
            <h2 className="font-serif text-3xl md:text-4xl font-bold">Observatory Architecture</h2>
            <p className="text-muted-foreground max-w-xl mx-auto text-sm">
              Clean vertical flow from user prompt down through state machine execution and two-stage verification.
            </p>
          </div>

          {/* Clean Vertical Flow Card */}
          <div className="p-6 md:p-8 rounded-xl bg-surface border border-border font-mono text-xs space-y-4 shadow-lg">
            <div className="text-center font-bold text-brass uppercase tracking-wider pb-2 border-b border-border">
              SYSTEM TOPOLOGY & DATA FLOW
            </div>
            
            <div className="flex flex-col items-center gap-2 max-w-xl mx-auto py-2">
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">01 /</span> <strong className="text-foreground">User Goal Prompt</strong> (Web Client)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">02 /</span> <strong className="text-foreground">TaskPilot AI Engine</strong> (FastAPI & Cookie Auth)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">03 /</span> <strong className="text-foreground">Dynamic DAG Planner</strong> (Cycle Check & Repair)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">04 /</span> <strong className="text-foreground">Agent Orchestrator</strong> (State Machine & SSE Stream)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">05 /</span> <strong className="text-foreground">Sandboxed Tools</strong> (Search, Web Extract, AST Math, Email)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-border bg-background text-center">
                <span className="text-muted-foreground">06 /</span> <strong className="text-foreground">Two-Stage Verifier</strong> (Rule Checks + Consistency)
              </div>
              <div className="text-brass font-bold">↓</div>
              <div className="w-full p-3 rounded-lg border border-brass/40 bg-brass/10 text-center text-brass font-semibold">
                <span className="text-brass">07 /</span> <strong>Verified Interactive Result & Agent Trace</strong>
              </div>
            </div>

            {/* Tech Stack Row */}
            <div className="pt-4 border-t border-border">
              <div className="text-[10px] text-muted-foreground uppercase tracking-widest text-center mb-3">
                BUILT WITH PINNED PRODUCTION STACK
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 text-[11px]">
                <Badge variant="outline">Next.js 14 (App Router)</Badge>
                <Badge variant="outline">FastAPI & Uvicorn</Badge>
                <Badge variant="outline">SQLAlchemy 2.0 Async</Badge>
                <Badge variant="outline">PostgreSQL 16</Badge>
                <Badge variant="outline">Tailwind CSS 3.4</Badge>
                <Badge variant="outline">Argon2-cffi Auth</Badge>
                <Badge variant="outline">Server-Sent Events</Badge>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 9. Footer */}
      <footer className="py-12 px-6 border-t border-border bg-surface text-xs font-mono text-muted-foreground">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="h-6 w-6 rounded bg-brass/15 border border-brass/30 flex items-center justify-center text-brass">
              <Compass className="h-3.5 w-3.5" />
            </div>
            <span className="text-foreground font-semibold">TaskPilot AI</span>
            <span className="hidden sm:inline">— Autonomous Digital Agent</span>
          </div>
          <div className="flex flex-wrap items-center gap-6">
            <Link href="/app" className="hover:text-foreground transition-colors">
              Mission Dashboard
            </Link>
            <Link href="/app/tools" className="hover:text-foreground transition-colors">
              Tool Matrix
            </Link>
            <Link href="/login" className="hover:text-foreground transition-colors">
              Instant Demo
            </Link>
            <Link href="/signup" className="hover:text-foreground transition-colors">
              Get Started
            </Link>
          </div>
          <div className="text-[11px] text-muted-foreground">
            © 2026 TaskPilot AI. Ink &amp; Brass Theme.
          </div>
        </div>
      </footer>
    </div>
  );
}
