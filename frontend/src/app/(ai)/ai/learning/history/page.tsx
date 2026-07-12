"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLearningHistory } from "@/lib/api/ai.api";
import type { AILearningHistory } from "@/types/ai.types";

export default function AILearningHistoryPage() {
  const [history, setHistory] = useState<AILearningHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getLearningHistory()
      .then(setHistory)
      .catch(() => setError("Unable to load learning history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Learning history</h1>
            <p className="text-sm text-muted-foreground">Tutor conversations, study plans, and quiz feedback.</p>
          </div>
          <Link href="/ai/learning" className="btn-base btn-secondary">Learning tutor</Link>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}
        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading learning history...</div>}

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="card p-5">
            <h2 className="font-semibold">Tutor sessions</h2>
            <div className="mt-4 space-y-3">
              {history?.tutor_sessions.length === 0 && <p className="text-sm text-muted-foreground">No tutor sessions yet.</p>}
              {history?.tutor_sessions.map((item) => (
                <article key={item.id} className="rounded-lg border border-border p-3">
                  <p className="text-sm font-medium">{item.lesson_title || item.course_title}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.question}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold">Study plans</h2>
            <div className="mt-4 space-y-3">
              {history?.study_plans.length === 0 && <p className="text-sm text-muted-foreground">No study plans yet.</p>}
              {history?.study_plans.map((item) => (
                <article key={item.id} className="rounded-lg border border-border p-3">
                  <p className="text-sm font-medium">{item.title}</p>
                  <p className="text-xs text-muted-foreground">{item.cadence} - {item.pace}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold">Quiz feedback</h2>
            <div className="mt-4 space-y-3">
              {history?.quiz_feedback.length === 0 && <p className="text-sm text-muted-foreground">No feedback yet.</p>}
              {history?.quiz_feedback.map((item) => (
                <article key={item.id} className="rounded-lg border border-border p-3">
                  <p className="text-sm font-medium">{item.course_title}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{item.explanation}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
