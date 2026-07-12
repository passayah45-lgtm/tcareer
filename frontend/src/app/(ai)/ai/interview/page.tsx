"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getInterviewAnalytics, getInterviewSessions, startInterviewSession } from "@/lib/api/ai.api";
import type { AIInterviewAnalytics, AIInterviewDifficulty, AIInterviewSession, AIInterviewSessionType } from "@/types/ai.types";

const sessionTypes: AIInterviewSessionType[] = ["behavioral", "technical", "system_design", "coding", "hr", "leadership", "language_interview", "custom"];
const difficulties: AIInterviewDifficulty[] = ["beginner", "intermediate", "advanced", "expert"];

export default function AIInterviewPage() {
  const [sessions, setSessions] = useState<AIInterviewSession[]>([]);
  const [analytics, setAnalytics] = useState<AIInterviewAnalytics | null>(null);
  const [sessionType, setSessionType] = useState<AIInterviewSessionType>("behavioral");
  const [difficulty, setDifficulty] = useState<AIInterviewDifficulty>("intermediate");
  const [jobTitle, setJobTitle] = useState("Junior Data Analyst");
  const [skills, setSkills] = useState("Python, SQL, communication");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getInterviewSessions(), getInterviewAnalytics()])
      .then(([sessionData, analyticsData]) => {
        setSessions(sessionData);
        setAnalytics(analyticsData);
      })
      .catch(() => setError("Unable to load AI interview coach."))
      .finally(() => setLoading(false));
  }, []);

  async function startSession() {
    setBusy(true);
    setError("");
    try {
      const session = await startInterviewSession({
        session_type: sessionType,
        difficulty,
        job_title: jobTitle,
        skills: skills.split(",").map((item) => item.trim()).filter(Boolean),
      });
      window.location.href = `/ai/interview/session/${session.id}`;
    } catch {
      setError("Unable to start interview session.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Interview Coach</h1>
            <p className="text-sm text-muted-foreground">Practice interviews with AI-generated questions, scoring, feedback, replay, and improvement trends.</p>
          </div>
          <Link href="/ai/interview/history" className="btn-base btn-secondary">History</Link>
        </header>

        {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading interview coach...</div>}

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{analytics?.sessions ?? 0}</span><span className="stat-label">Sessions</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.completed ?? 0}</span><span className="stat-label">Completed</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.average_score ?? 0}</span><span className="stat-label">Average score</span></div>
          <div className="stat-card"><span className="stat-value">${analytics?.ai_cost ?? "0.000000"}</span><span className="stat-label">AI cost</span></div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
          <div className="card p-5">
            <h2 className="font-semibold">Start practice</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block text-muted-foreground">Interview type</span>
                <select value={sessionType} onChange={(event) => setSessionType(event.target.value as AIInterviewSessionType)} className="input w-full">
                  {sessionTypes.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}
                </select>
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-muted-foreground">Difficulty</span>
                <select value={difficulty} onChange={(event) => setDifficulty(event.target.value as AIInterviewDifficulty)} className="input w-full">
                  {difficulties.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-muted-foreground">Target role</span>
                <input value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} className="input w-full" />
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-muted-foreground">Skills</span>
                <input value={skills} onChange={(event) => setSkills(event.target.value)} className="input w-full" />
              </label>
            </div>
            <button disabled={busy} onClick={() => void startSession()} className="btn-base btn-primary mt-4">
              {busy ? "Starting..." : "Start mock interview"}
            </button>
          </div>

          <div className="card p-5">
            <h2 className="font-semibold">Coaching focus</h2>
            <div className="mt-4 space-y-3">
              {(analytics?.weak_areas ?? []).length === 0 && <p className="text-sm text-muted-foreground">Weak areas will appear after answer evaluations.</p>}
              {analytics?.weak_areas.map((item) => (
                <div key={item.area} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                  <span>{item.area.replaceAll("_", " ")}</span>
                  <span className="font-medium">{item.score}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="card p-5">
          <h2 className="font-semibold">Recent sessions</h2>
          <div className="mt-4 grid gap-3">
            {sessions.length === 0 && <p className="text-sm text-muted-foreground">No interview practice yet.</p>}
            {sessions.slice(0, 5).map((session) => (
              <Link key={session.id} href={`/ai/interview/session/${session.id}`} className="rounded-md border p-4 transition hover:border-primary">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">{session.job_title || session.session_type.replaceAll("_", " ")}</p>
                    <p className="text-sm text-muted-foreground">{session.difficulty} • {session.status}</p>
                  </div>
                  <span className="text-sm font-semibold text-primary">{session.overall_score || 0}/100</span>
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
