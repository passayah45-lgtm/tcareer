"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  cancelInterviewSession,
  finishInterviewSession,
  generateInterviewQuestion,
  getInterviewSession,
  pauseInterviewSession,
  resumeInterviewSession,
  submitInterviewAnswer,
} from "@/lib/api/ai.api";
import type { AIInterviewQuestion, AIInterviewSession } from "@/types/ai.types";

interface PageProps {
  params: { sessionId: string };
}

export default function AIInterviewSessionPage({ params }: PageProps) {
  const [session, setSession] = useState<AIInterviewSession | null>(null);
  const [activeQuestion, setActiveQuestion] = useState<AIInterviewQuestion | null>(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function reload() {
    const data = await getInterviewSession(params.sessionId);
    setSession(data);
    setActiveQuestion(data.questions.at(-1) ?? null);
  }

  useEffect(() => {
    getInterviewSession(params.sessionId)
      .then((data) => {
        setSession(data);
        setActiveQuestion(data.questions.at(-1) ?? null);
      })
      .catch(() => setError("Unable to load interview session."))
      .finally(() => setLoading(false));
  }, [params.sessionId]);

  const latestEvaluation = useMemo(() => session?.evaluations.at(-1), [session]);
  const isClosed = session?.status === "completed" || session?.status === "cancelled";

  async function runAction(action: "question" | "answer" | "finish" | "pause" | "resume" | "cancel") {
    if (!session) return;
    setBusy(action);
    setError("");
    try {
      if (action === "question") {
        const question = await generateInterviewQuestion(session.id);
        setActiveQuestion(question);
      }
      if (action === "answer" && activeQuestion) {
        await submitInterviewAnswer(session.id, activeQuestion.id, answer);
        setAnswer("");
      }
      if (action === "finish") await finishInterviewSession(session.id);
      if (action === "pause") await pauseInterviewSession(session.id);
      if (action === "resume") await resumeInterviewSession(session.id);
      if (action === "cancel") await cancelInterviewSession(session.id);
      await reload();
    } catch {
      setError("Interview action failed.");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{session?.job_title || "AI mock interview"}</h1>
            <p className="text-sm text-muted-foreground">{session ? `${session.session_type.replaceAll("_", " ")} • ${session.difficulty} • ${session.status}` : "Loading session..."}</p>
          </div>
          <Link href="/ai/interview/history" className="btn-base btn-secondary">History</Link>
        </header>

        {loading && <div className="card p-5 text-sm text-muted-foreground">Loading session...</div>}
        {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

        {session && (
          <>
            <section className="grid gap-4 sm:grid-cols-4">
              <div className="stat-card"><span className="stat-value">{session.overall_score}</span><span className="stat-label">Overall score</span></div>
              <div className="stat-card"><span className="stat-value">{session.questions.length}</span><span className="stat-label">Questions</span></div>
              <div className="stat-card"><span className="stat-value">{session.evaluations.length}</span><span className="stat-label">Evaluations</span></div>
              <div className="stat-card"><span className="stat-value">{session.total_tokens}</span><span className="stat-label">AI tokens</span></div>
            </section>

            <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
              <div className="card p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <h2 className="font-semibold">Live practice</h2>
                  <div className="flex flex-wrap gap-2">
                    <button disabled={Boolean(busy) || isClosed} onClick={() => void runAction("question")} className="btn-base btn-primary">{busy === "question" ? "Generating..." : "Next question"}</button>
                    {session.status === "paused" ? (
                      <button disabled={Boolean(busy)} onClick={() => void runAction("resume")} className="btn-base btn-secondary">Resume</button>
                    ) : (
                      <button disabled={Boolean(busy) || isClosed} onClick={() => void runAction("pause")} className="btn-base btn-secondary">Pause</button>
                    )}
                    <button disabled={Boolean(busy) || isClosed} onClick={() => void runAction("finish")} className="btn-base btn-secondary">Finish</button>
                    <button disabled={Boolean(busy) || isClosed} onClick={() => void runAction("cancel")} className="btn-base btn-secondary text-red-600">Cancel</button>
                  </div>
                </div>

                <div className="mt-5 rounded-md border p-4">
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">Current question</p>
                  <p className="mt-2 text-lg font-medium">{activeQuestion?.question_text ?? "Generate the first question to begin."}</p>
                </div>

                <label className="mt-4 block text-sm">
                  <span className="mb-1 block text-muted-foreground">Your answer</span>
                  <textarea
                    value={answer}
                    onChange={(event) => setAnswer(event.target.value)}
                    disabled={!activeQuestion || isClosed}
                    className="input min-h-36 w-full"
                    placeholder="Answer in your own words. Use examples, impact, and structure."
                  />
                </label>
                <button disabled={Boolean(busy) || !activeQuestion || !answer.trim() || isClosed} onClick={() => void runAction("answer")} className="btn-base btn-primary mt-3">
                  {busy === "answer" ? "Evaluating..." : "Submit answer"}
                </button>
              </div>

              <div className="space-y-4">
                <div className="card p-5">
                  <h2 className="font-semibold">Latest feedback</h2>
                  {!latestEvaluation && <p className="mt-2 text-sm text-muted-foreground">Feedback appears after you submit an answer.</p>}
                  {latestEvaluation && (
                    <div className="mt-3 space-y-3 text-sm">
                      <p><strong className="text-primary">{latestEvaluation.overall_score}/100</strong> overall</p>
                      <p>{latestEvaluation.next_practice_goal}</p>
                      <div className="flex flex-wrap gap-2">
                        {latestEvaluation.tips.map((tip) => <span key={tip} className="tag">{tip}</span>)}
                      </div>
                    </div>
                  )}
                </div>

                <div className="card p-5">
                  <h2 className="font-semibold">Final report</h2>
                  <p className="mt-2 text-sm text-muted-foreground">{session.summary || "Finish the session to generate a full coaching report."}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(session.feedback.improvement_roadmap ?? []).map((item) => <span key={item} className="tag">{item}</span>)}
                  </div>
                </div>
              </div>
            </section>

            <section className="card p-5">
              <h2 className="font-semibold">Session replay</h2>
              <div className="mt-4 space-y-3">
                {session.history.length === 0 && <p className="text-sm text-muted-foreground">No timeline events yet.</p>}
                {session.history.map((event, index) => (
                  <div key={`${event.event}-${index}`} className="rounded-md border px-3 py-2 text-sm">
                    <p className="font-medium">{String(event.event ?? "event").replaceAll("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">{String(event.timestamp ?? "")}</p>
                  </div>
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
