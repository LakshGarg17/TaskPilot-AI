"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AlertCircle, ShieldCheck, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function Header() {
  const [healthData, setHealthData] = useState<{
    mock_mode: boolean;
    app: string;
    version: string;
    search_provider: string;
    openai_model: string;
  } | null>(null);

  useEffect(() => {
    api.health.check().then(setHealthData).catch(() => null);
  }, []);

  return (
    <header className="border-b border-border bg-surface px-6 py-3 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-3">
        <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
          STATION: <span className="text-foreground">STANDALONE OBSERVATORY</span>
        </span>
        {healthData?.mock_mode ? (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-ochre/15 border border-ochre/30 text-ochre text-xs font-mono font-medium">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>MOCK MODE ACTIVE (SYNTHETIC PROVIDERS)</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-sage/15 border border-sage/30 text-sage text-xs font-mono font-medium">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>LIVE INTEGRATION (OPENAI & TAVILY)</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 text-xs font-mono text-muted-foreground">
        <div>
          MODEL: <span className="text-brass">{healthData?.openai_model || "gpt-4o-mini"}</span>
        </div>
        <div className="hidden sm:inline-block">
          SEARCH: <span className="text-foreground">{healthData?.search_provider || "tavily"}</span>
        </div>
      </div>
    </header>
  );
}
