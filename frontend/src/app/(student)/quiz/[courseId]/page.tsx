"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { useAuthStore } from "@/stores/auth.store";
import { getQuizQuestions, canAttemptQuiz, submitQuiz, getAttemptHistory } from "@/lib/api/assessments.api";
import { generateQuizFeedback } from "@/lib/api/ai.api";
import type { QuizResult, QuizMeta } from "@/lib/api/assessments.api";
import type { AIQuizFeedback } from "@/types/ai.types";

type Phase = "loading" | "locked" | "quiz" | "results";

function ScoreRing({ percentage, passed }: { percentage: number; passed: boolean }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color = passed ? "#10b981" : "#ef4444";
  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
        <circle cx="60" cy="60" r={radius} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold" style={{ color }}>{percentage}%</span>
        <span className="text-xs text-muted-foreground font-medium mt-0.5">{passed ? "Passed" : "Failed"}</span>
      </div>
    </div>
  );
}

function QuestionResultCard({ result, index }: { result: QuizResult["question_results"][0]; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const correct = result.is_correct;
  return (
    <div className={"border rounded-xl overflow-hidden transition-all duration-200 " + (correct ? "border-emerald-200 bg-emerald-50/50" : "border-red-200 bg-red-50/50")}>
      <button onClick={() => setExpanded(!expanded)} className="w-full flex items-start gap-3 p-4 text-left">
        <div className={"flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5 " + (correct ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700")}>
          {correct ? "✓" : "✕"}
        </div>
        <p className="flex-1 text-sm font-medium">{index + 1}. {result.question_text}</p>
        <svg className={"w-4 h-4 flex-shrink-0 text-muted-foreground transition-transform duration-200 mt-0.5 " + (expanded ? "rotate-180" : "")} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-current/10 pt-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {result.options.map((opt, i) => {
              const isCorrect = i === result.correct_index;
              const isSelected = i === result.selected_index;
              let cls = "text-xs px-3 py-2 rounded-lg border ";
              if (isCorrect) cls += "bg-emerald-50 border-emerald-300 text-emerald-800 font-medium";
              else if (isSelected && !isCorrect) cls += "bg-red-50 border-red-300 text-red-700 line-through";
              else cls += "bg-background border-border text-muted-foreground";
              return (
                <div key={i} className={cls}>
                  <span className="font-semibold mr-1">{["A","B","C","D"][i]}.</span>{opt}
                  {isCorrect && <span className="ml-1 text-emerald-600">✓</span>}
                  {isSelected && !isCorrect && <span className="ml-1 text-red-600">✕</span>}
                </div>
              );
            })}
          </div>
          {result.explanation && (
            <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs font-semibold text-blue-800 mb-0.5">Explanation</p>
              <p className="text-xs text-blue-700">{result.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultsView({ result, courseId, onRetake }: { result: QuizResult; courseId: string; onRetake: () => void }) {
  const [feedback, setFeedback] = useState<AIQuizFeedback | null>(null);
  const [feedbackLoading, setFeedbackLoading] = useState(false);

  async function loadFeedback() {
    setFeedbackLoading(true);
    try {
      setFeedback(await generateQuizFeedback({ course_id: courseId, attempt_id: result.id }));
    } finally {
      setFeedbackLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="border border-border rounded-xl p-6 bg-card text-center">
        <ScoreRing percentage={result.percentage} passed={result.passed} />
        <div className="mt-4 space-y-1">
          <p className="text-lg font-bold">{result.passed ? "You passed!" : "Not quite there yet"}</p>
          <p className="text-sm text-muted-foreground">{result.score} out of {result.total_questions} correct · Pass threshold: {result.pass_threshold}%</p>
          <p className="text-xs text-muted-foreground">Attempt {result.attempt_number}</p>
        </div>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          {result.passed ? (
            <>
              <Link href="/certificates" className="h-9 px-5 inline-flex items-center text-sm font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors">View certificate</Link>
              <Link href="/courses" className="h-9 px-5 inline-flex items-center text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors">Browse courses</Link>
            </>
          ) : (
            <button onClick={onRetake} className="h-9 px-5 inline-flex items-center text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">Try again</button>
          )}
          <button onClick={() => void loadFeedback()} disabled={feedbackLoading} className="h-9 px-5 inline-flex items-center text-sm font-medium border border-border rounded-lg hover:bg-muted transition-colors">
            {feedbackLoading ? "Generating..." : "AI feedback"}
          </button>
        </div>
      </div>
      {feedback && (
        <section className="border border-border rounded-xl p-5 bg-card">
          <h2 className="font-semibold mb-2">AI quiz feedback</h2>
          <p className="text-sm text-muted-foreground">{feedback.explanation}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {feedback.weak_topics.map((topic) => <span key={topic} className="tag">{topic}</span>)}
          </div>
        </section>
      )}
      <div>
        <h2 className="font-semibold mb-3">Question breakdown <span className="ml-2 text-xs text-muted-foreground font-normal">click to expand</span></h2>
        <div className="space-y-2">
          {result.question_results.map((qr, i) => (
            <QuestionResultCard key={qr.question_id} result={qr} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}

function QuizView({ meta, courseId, onSubmit }: { meta: QuizMeta; courseId: string; onSubmit: (result: QuizResult) => void }) {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const total = meta.questions.length;
  const answered = Object.keys(answers).length;
  const allAnswered = answered === total;

  async function handleSubmit() {
    if (!allAnswered) { setError("Answer all " + total + " questions before submitting."); return; }
    setSubmitting(true); setError("");
    try { const result = await submitQuiz(courseId, answers); onSubmit(result); }
    catch { setError("Submission failed. Check your connection and try again."); setSubmitting(false); }
  }

  if (!meta.questions.length) return <div className="border border-border rounded-xl p-8 text-center bg-card"><p className="font-semibold mb-1">No questions yet</p><p className="text-sm text-muted-foreground">The instructor has not added any questions to this quiz.</p></div>;
  const q = meta.questions[currentIndex];
  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
          <span>Question {currentIndex + 1} of {total}</span><span>{answered} answered</span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: ((currentIndex + 1) / total * 100) + "%" }} />
        </div>
      </div>
      <div className="border border-border rounded-xl p-5 bg-card min-h-64">
        <p className="font-medium mb-5 text-base leading-relaxed">{q.question_text}</p>
        <div className="space-y-2">
          {q.options.filter(opt => opt.trim()).map((opt, i) => {
            const selected = answers[q.id] === i;
            return (
              <button key={i} onClick={() => setAnswers(prev => ({ ...prev, [q.id]: i }))}
                className={"w-full flex items-center gap-3 px-4 py-3 rounded-lg border text-sm text-left transition-all duration-150 " + (selected ? "border-primary bg-primary/5 text-primary font-medium" : "border-border bg-background hover:border-primary/50 hover:bg-muted/50")}>
                <span className={"w-6 h-6 flex-shrink-0 rounded-full border-2 flex items-center justify-center text-xs font-bold " + (selected ? "border-primary bg-primary text-white" : "border-muted-foreground/30 text-muted-foreground")}>
                  {["A","B","C","D"][i]}
                </span>
                {opt}
              </button>
            );
          })}
        </div>
      </div>
      <div className="flex items-center justify-between gap-3">
        <button onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))} disabled={currentIndex === 0}
          className="h-9 px-4 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-40 transition-colors">Previous</button>
        <div className="flex items-center gap-1.5 flex-wrap justify-center">
          {meta.questions.map((_, i) => (
            <button key={i} onClick={() => setCurrentIndex(i)}
              className={"w-7 h-7 rounded-full text-xs font-medium transition-all duration-150 " + (i === currentIndex ? "bg-primary text-white" : answers[meta.questions[i].id] !== undefined ? "bg-emerald-100 text-emerald-700" : "bg-muted text-muted-foreground")}>
              {i + 1}
            </button>
          ))}
        </div>
        {currentIndex < total - 1 ? (
          <button onClick={() => setCurrentIndex(currentIndex + 1)}
            className="h-9 px-4 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary-600 transition-colors">Next</button>
        ) : (
          <button onClick={handleSubmit} disabled={submitting || !allAnswered}
            className="h-9 px-4 text-sm font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors">
            {submitting ? "Submitting..." : "Submit quiz"}
          </button>
        )}
      </div>
      {error && <p className="text-sm text-destructive text-center">{error}</p>}
    </div>
  );
}

export default function QuizPage({ params }: { params: { courseId: string } }) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("loading");
  const [meta, setMeta] = useState<QuizMeta | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [lockReason, setLockReason] = useState("");
  const [latestAttempt, setLatestAttempt] = useState<QuizResult | null>(null);

  const load = useCallback(async () => {
    try {
      const [canData, quizData, historyData] = await Promise.all([
        canAttemptQuiz(params.courseId),
        getQuizQuestions(params.courseId),
        getAttemptHistory(params.courseId).catch(() => []),
      ]);
      setMeta(quizData);
      if (historyData.length > 0) setLatestAttempt(historyData[0]);
      if (!canData.can_attempt) { setLockReason(canData.reason); setPhase("locked"); }
      else setPhase("quiz");
    } catch {
      setLockReason("Could not load the quiz. Make sure you are enrolled in this course.");
      setPhase("locked");
    }
  }, [params.courseId]);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) { router.push("/login?next=/quiz/" + params.courseId); return; }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [isLoading, isAuthenticated, load, router, params.courseId]);

  return (
    <>
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="mb-6">
          <button onClick={() => router.back()} className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1 mb-3">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
            Back
          </button>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">Course quiz</h1>
          {meta && <p className="text-sm text-muted-foreground mt-1">{meta.total} question{meta.total !== 1 ? "s" : ""} · Pass at {meta.pass_threshold}% or higher</p>}
        </div>
        {latestAttempt && phase === "locked" && latestAttempt.passed && (
          <div className="mb-4 p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
            <p className="text-sm font-semibold text-emerald-800">You already passed this quiz with {latestAttempt.percentage}%.</p>
            <Link href="/certificates" className="text-xs text-emerald-700 hover:underline mt-1 block">View your certificate</Link>
          </div>
        )}
        {phase === "loading" && (
          <div className="space-y-3">
            <div className="h-4 bg-muted rounded animate-pulse w-48" />
            <div className="h-64 bg-muted rounded-xl animate-pulse" />
            <div className="h-10 bg-muted rounded animate-pulse" />
          </div>
        )}
        {phase === "locked" && (
          <div className="border border-border rounded-xl p-8 text-center bg-card">
            <p className="font-semibold mb-1">Quiz not available</p>
            <p className="text-sm text-muted-foreground">{lockReason}</p>
          </div>
        )}
        {phase === "quiz" && meta && <QuizView meta={meta} courseId={params.courseId} onSubmit={(r) => { setResult(r); setPhase("results"); }} />}
        {phase === "results" && result && <ResultsView result={result} courseId={params.courseId} onRetake={() => { setResult(null); setPhase("quiz"); }} />}
      </main>
    </>
  );
}
