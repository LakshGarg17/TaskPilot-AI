"use client";

import React, { useState, useEffect } from "react";
import { Wrench, Shield, AlertTriangle, ShieldAlert, CheckCircle, Code } from "lucide-react";
import { api } from "@/lib/api";
import { ToolDefinition } from "@/types";
import { Badge } from "@/components/ui/badge";

export default function ToolsPage() {
  const [tools, setTools] = useState<ToolDefinition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.tools
      .list()
      .then(setTools)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-foreground">
          Tool Registry & Capability Matrix
        </h1>
        <p className="text-sm text-muted-foreground font-sans mt-1">
          Catalog of sandbox-hardened capabilities available to TaskPilot&apos;s planning and execution engines.
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-surface border border-border animate-pulse" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {tools.map((tool) => {
            const isHigh = tool.risk_level === "HIGH";
            const isMedium = tool.risk_level === "MEDIUM";

            return (
              <div
                key={tool.name}
                className="p-5 rounded-xl bg-surface border border-border space-y-4 hover:border-brass/40 transition-colors shadow-sm flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded bg-surface-secondary border border-border text-brass">
                        <Wrench className="h-4 w-4" />
                      </div>
                      <h3 className="font-mono text-sm font-bold text-foreground">
                        {tool.name}
                      </h3>
                    </div>

                    <Badge
                      variant={
                        isHigh ? "clay" : isMedium ? "ochre" : "sage"
                      }
                      className="text-[10px]"
                    >
                      {tool.risk_level} RISK
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {tool.description}
                  </p>
                </div>

                <div className="space-y-2 pt-3 border-t border-border/60">
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-muted-foreground uppercase">
                    <Code className="h-3.5 w-3.5 text-brass" />
                    <span>Input Schema Spec</span>
                  </div>
                  <pre className="p-2.5 rounded bg-surface-secondary border border-border text-[10px] font-mono text-foreground/80 overflow-x-auto max-h-32">
                    {JSON.stringify(tool.schema?.properties || {}, null, 2)}
                  </pre>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
