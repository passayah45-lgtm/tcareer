"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getInterviewSessions } from "@/lib/api/ai.api";
import type { AIInterviewSession } from "@/types/ai.types";

export default function AIInterviewHistoryPage() {
  const [sessions, setSessions] = useState<AIInterviewSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getInterviewSessions()
      .then(setSessions)
      .catch(() => setError("Unable to load interview history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Interview history</h1>
            <p className="text-sm text-muted-foreground">Review prior mock interviews, scores, trends, and replay details.</p>
          </div>
          <Link href="/ai/interview" className="btn-base btn-secondary">New session</Link>
        </header>
        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading history...</div>}
        {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        <section className="grid gap-3">
          {!loading && sessions.length === 0 && <div className="card p-5 text-sm text-muted-foreground">No interview sessions yet.</div>}
          {sessions.map((session) => (
            <Link key={session.id} href={`/ai/interview/session/${session.id}`} className="card block p-5 transition hover:border-primary">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold">{session.job_title || session.session_type.replaceAll("_", " ")}</p>
                  <p className="text-sm text-muted-foreground">{session.session_type.replaceAll("_", " ")} • {session.difficulty} • {session.status}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{new Date(session.created_at).toLocaleString()}</p>
                </div>
                <div className="grid grid-cols-3 gap-3 text-center text-sm">
                  <span><strong className="block text-lg text-primary">{session.overall_score}</strong>Score</span>
                  <span><strong className="block text-lg text-primary">{session.questions.length}</strong>Questions</span>
                  <span><strong className="block text-lg text-primary">{session.duration_seconds}s</strong>Duration</span>
                </div>
              </div>
            </Link>
          ))}
        </section>
      </div>
    </main>
  );
}
