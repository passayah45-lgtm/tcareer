"use client";

import Link from "next/link";
import { useState } from "react";
import { generateStudyPlan } from "@/lib/api/ai.api";
import type { AIStudyPlan } from "@/types/ai.types";

export default function AILearningPlansPage() {
  const [cadence, setCadence] = useState<"daily" | "weekly" | "monthly">("weekly");
  const [pace, setPace] = useState<"relaxed" | "balanced" | "intensive">("balanced");
  const [minutes, setMinutes] = useState(60);
  const [deadline, setDeadline] = useState("");
  const [plan, setPlan] = useState<AIStudyPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function createPlan() {
    setBusy(true);
    setError("");
    try {
      setPlan(await generateStudyPlan({ cadence, pace, available_minutes_per_day: minutes, deadline: deadline || undefined }));
    } catch {
      setError("Unable to create study plan.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Study Plans</h1>
            <p className="text-sm text-muted-foreground">Personalized study plans based on courses, progress, quiz results, and career goals.</p>
          </div>
          <Link href="/ai/learning/history" className="btn-base btn-secondary">History</Link>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1fr]">
          <div className="card p-5">
            <h2 className="font-semibold">Plan settings</h2>
            <div className="mt-4 space-y-3">
              <select className="input w-full" value={cadence} onChange={(event) => setCadence(event.target.value as typeof cadence)}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
              <select className="input w-full" value={pace} onChange={(event) => setPace(event.target.value as typeof pace)}>
                <option value="relaxed">Relaxed</option>
                <option value="balanced">Balanced</option>
                <option value="intensive">Intensive</option>
              </select>
              <input className="input w-full" type="number" min={10} max={720} value={minutes} onChange={(event) => setMinutes(Number(event.target.value))} />
              <input className="input w-full" type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} />
              <button className="btn-base btn-primary" disabled={busy} onClick={() => void createPlan()}>{busy ? "Generating..." : "Generate plan"}</button>
            </div>
          </div>
          <section className="card p-5">
            {!plan ? (
              <p className="text-sm text-muted-foreground">Generate a plan to see milestones and recommendations.</p>
            ) : (
              <>
                <h2 className="font-semibold">{plan.title}</h2>
                <p className="mt-2 text-sm text-muted-foreground">Confidence {plan.confidence_score} - ${plan.estimated_cost}</p>
                <div className="mt-4 space-y-3">
                  {plan.milestones.map((item, index) => (
                    <div key={index} className="rounded-lg border border-border p-3 text-sm">
                      {String(item.title ?? `Milestone ${index + 1}`)}
                    </div>
                  ))}
                </div>
                <pre className="mt-4 max-h-80 overflow-auto rounded-lg bg-muted p-4 text-xs">{JSON.stringify(plan.plan, null, 2)}</pre>
              </>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
