"use client";

import { useEffect, useState } from "react";
import { getAIHistory } from "@/lib/api/ai.api";
import type { AIRequest } from "@/types/ai.types";

export default function AIHistoryPage() {
  const [items, setItems] = useState<AIRequest[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getAIHistory().then(setItems).catch(() => setError("Unable to load AI history."));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-5xl">
        <h1 className="text-2xl font-semibold mb-2">AI History</h1>
        <p className="text-sm text-muted-foreground mb-6">Recent AI requests, safety flags, latency, and responses.</p>
        {error && <p className="text-sm text-destructive mb-4">{error}</p>}
        <section className="rounded-lg border border-border bg-card p-5">
          <div className="divide-y divide-border">
            {items.map((item) => (
              <div key={item.id} className="py-3 text-sm grid gap-2 md:grid-cols-[140px_100px_1fr_120px]">
                <span>{item.feature.replaceAll("_", " ")}</span>
                <span>{item.status}</span>
                <span className="text-muted-foreground truncate">{item.response_text || item.redacted_input}</span>
                <span>{item.latency_ms} ms</span>
              </div>
            ))}
            {items.length === 0 && <p className="text-sm text-muted-foreground">No AI requests yet.</p>}
          </div>
        </section>
      </div>
    </main>
  );
}
