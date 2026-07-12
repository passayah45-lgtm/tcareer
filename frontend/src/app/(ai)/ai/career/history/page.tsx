"use client";

import { useEffect, useState } from "react";
import { getCareerHistory } from "@/lib/api/ai.api";
import type { AICareerHistory } from "@/types/ai.types";

export default function AICareerHistoryPage() {
  const [history, setHistory] = useState<AICareerHistory | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getCareerHistory().then(setHistory).catch(() => setError("Unable to load career coach history."));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">Career Coach History</h1>
          <p className="text-sm text-muted-foreground">Assessment, roadmap, skill gap, and weekly coaching records.</p>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="card p-5">
            <h2 className="font-semibold">Assessments</h2>
            <div className="mt-4 space-y-3">
              {(history?.assessments ?? []).map((item) => (
                <div key={item.id} className="rounded-md border border-border p-3 text-sm">
                  <p className="font-medium">Readiness {item.readiness_score}</p>
                  <p className="text-muted-foreground">{item.recommendations.slice(0, 2).join(" - ")}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold">Weekly coaching</h2>
            <div className="mt-4 space-y-3">
              {(history?.coaching ?? []).map((item) => (
                <div key={item.id} className="rounded-md border border-border p-3 text-sm">
                  <p className="font-medium">{item.week_start}</p>
                  <p className="text-muted-foreground">{item.motivation_summary || item.summary}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
