"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AIChatPanel } from "@/components/ai/AIChatPanel";
import { getAIOverview } from "@/lib/api/ai.api";
import type { AIOverview } from "@/types/ai.types";

export default function AIPage() {
  const [overview, setOverview] = useState<AIOverview | null>(null);

  useEffect(() => {
    getAIOverview().then(setOverview).catch(() => setOverview(null));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">AI Platform</h1>
          <p className="text-sm text-muted-foreground">Central gateway for T-Career AI conversations and feature foundations.</p>
        </header>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="stat-card"><span className="stat-value">{overview?.requests ?? 0}</span><span className="stat-label">Requests</span></div>
          <div className="stat-card"><span className="stat-value">{overview?.usage.tokens ?? 0}</span><span className="stat-label">Tokens</span></div>
          <div className="stat-card"><span className="stat-value">{overview?.providers_configured ?? 0}</span><span className="stat-label">Providers</span></div>
        </div>
        <section className="card p-5">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="font-semibold">AI Interview Coach</h2>
                <p className="text-sm text-muted-foreground">Practice behavioral, technical, coding, HR, leadership, language, and custom interviews.</p>
              </div>
              <Link href="/ai/interview" className="btn-base btn-primary">Open coach</Link>
            </div>
            <div className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
              <div>
                <h2 className="font-semibold">AI Quality</h2>
                <p className="text-sm text-muted-foreground">Monitor evaluation, confidence, feedback, fairness, privacy, provider, cache, and cost signals.</p>
              </div>
              <Link href="/ai/quality" className="btn-base btn-secondary">Review quality</Link>
            </div>
          </div>
        </section>
        <AIChatPanel />
      </div>
    </main>
  );
}
