"use client";

import { useEffect, useState } from "react";
import { getAISettings } from "@/lib/api/ai.api";
import type { AISettings } from "@/types/ai.types";

export default function AISettingsPage() {
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getAISettings().then(setSettings).catch(() => setError("Unable to load AI settings."));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">AI Settings</h1>
          <p className="text-sm text-muted-foreground">Provider and model availability for the current environment.</p>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Providers</h2>
          <div className="divide-y divide-border">
            {settings?.providers.map((provider) => (
              <div key={provider.id} className="py-3 text-sm flex justify-between gap-3">
                <span>{provider.name}</span>
                <span className="text-muted-foreground">{provider.provider_type} {provider.is_default ? "default" : ""}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-lg border border-border bg-card p-5">
          <h2 className="font-semibold mb-3">Models</h2>
          <div className="divide-y divide-border">
            {settings?.models.map((model) => (
              <div key={model.id} className="py-3 text-sm grid gap-2 md:grid-cols-[1fr_160px_120px]">
                <span>{model.display_name || model.model_name}</span>
                <span className="text-muted-foreground">{model.provider_name}</span>
                <span>{model.max_tokens} tokens</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
