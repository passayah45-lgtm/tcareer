"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { askLearningTutor, generateLearningQuiz, generateLessonIntelligence, generateQuizFeedback, getLearningAnalytics } from "@/lib/api/ai.api";
import type { AIGeneratedQuiz, AILearningAnalytics, AILearningTutorSession, AILessonIntelligence, AIQuizFeedback } from "@/types/ai.types";

type Result = AILearningTutorSession | AILessonIntelligence | AIGeneratedQuiz | AIQuizFeedback | null;

export default function AILearningPage() {
  const [analytics, setAnalytics] = useState<AILearningAnalytics | null>(null);
  const [courseId, setCourseId] = useState("");
  const [lessonId, setLessonId] = useState("");
  const [question, setQuestion] = useState("Explain this concept with an example.");
  const [mode, setMode] = useState("question");
  const [result, setResult] = useState<Result>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      setCourseId(params.get("course") ?? "");
      setLessonId(params.get("lesson") ?? "");
      getLearningAnalytics().then(setAnalytics).catch(() => setError("Unable to load AI learning analytics."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function run(action: "tutor" | "lesson" | "quiz" | "feedback") {
    if (!courseId.trim()) {
      setError("Enter a course ID first.");
      return;
    }
    setBusy(action);
    setError("");
    try {
      if (action === "tutor") {
        setResult(await askLearningTutor({ course_id: courseId.trim(), lesson_id: lessonId.trim() || undefined, question, mode }));
      } else if (action === "lesson") {
        if (!lessonId.trim()) throw new Error("Lesson ID required.");
        setResult(await generateLessonIntelligence({ course_id: courseId.trim(), lesson_id: lessonId.trim() }));
      } else if (action === "quiz") {
        setResult(await generateLearningQuiz({ course_id: courseId.trim(), lesson_id: lessonId.trim() || undefined, difficulty: "intermediate", number_of_questions: 5 }));
      } else {
        setResult(await generateQuizFeedback({ course_id: courseId.trim() }));
      }
      setAnalytics(await getLearningAnalytics());
    } catch {
      setError(`Unable to run ${action}. Check permissions and inputs.`);
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">AI Learning Tutor</h1>
            <p className="text-sm text-muted-foreground">Course tutoring, lesson summaries, generated quizzes, quiz feedback, and personalized study support.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/ai/learning/plans" className="btn-base btn-primary">Study plans</Link>
            <Link href="/ai/learning/history" className="btn-base btn-secondary">History</Link>
          </div>
        </header>

        {error && <div className="rounded-lg border border-destructive/30 bg-card p-4 text-sm text-destructive">{error}</div>}

        <section className="grid gap-4 sm:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{analytics?.tutor_sessions ?? 0}</span><span className="stat-label">Tutor sessions</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.concepts_mastered ?? 0}</span><span className="stat-label">Concepts mastered</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.quiz_improvement ?? "0"}</span><span className="stat-label">Quiz average</span></div>
          <div className="stat-card"><span className="stat-value">${analytics?.cost ?? "0.000000"}</span><span className="stat-label">AI cost</span></div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1fr]">
          <div className="card p-5">
            <h2 className="font-semibold">Learning context</h2>
            <div className="mt-4 space-y-3">
              <input className="input w-full" value={courseId} onChange={(event) => setCourseId(event.target.value)} placeholder="Course ID" />
              <input className="input w-full" value={lessonId} onChange={(event) => setLessonId(event.target.value)} placeholder="Lesson ID optional for course tutor" />
              <select className="input w-full" value={mode} onChange={(event) => setMode(event.target.value)}>
                <option value="question">Answer question</option>
                <option value="explain">Explain concept</option>
                <option value="summarize">Summarize lesson</option>
                <option value="examples">Generate examples</option>
                <option value="simplify">Simplify topic</option>
                <option value="practice">Practice exercises</option>
                <option value="reading">Additional reading</option>
                <option value="connect">Connect lessons</option>
              </select>
              <textarea className="input min-h-24 w-full" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask the tutor..." />
              <div className="flex flex-wrap gap-2">
                <button className="btn-base btn-primary" disabled={busy !== ""} onClick={() => void run("tutor")}>{busy === "tutor" ? "Asking..." : "Ask tutor"}</button>
                <button className="btn-base btn-secondary" disabled={busy !== "" || !lessonId.trim()} onClick={() => void run("lesson")}>Lesson summary</button>
                <button className="btn-base btn-secondary" disabled={busy !== ""} onClick={() => void run("quiz")}>Generate quiz</button>
                <button className="btn-base btn-secondary" disabled={busy !== ""} onClick={() => void run("feedback")}>Quiz feedback</button>
              </div>
            </div>
          </div>

          <section className="card p-5">
            {!result ? (
              <p className="text-sm text-muted-foreground">Run a tutor action to see AI learning output.</p>
            ) : (
              <>
                <h2 className="font-semibold">AI output</h2>
                <pre className="mt-4 max-h-[34rem] overflow-auto rounded-lg bg-muted p-4 text-xs">{JSON.stringify(result, null, 2)}</pre>
              </>
            )}
          </section>
        </section>
      </div>
    </main>
  );
}
