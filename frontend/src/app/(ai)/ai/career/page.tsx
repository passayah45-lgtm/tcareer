"use client";

import { useEffect, useState } from "react";
import { generateWeeklyCareerCoaching, getCareerAnalytics, getCareerGoals, getCareerHistory, runCareerAssessment, runCareerSkillGap } from "@/lib/api/ai.api";
import type { AICareerAnalytics, AICareerAssessment, AICareerCoachingSummary, AICareerGoal, AICareerHistory, AICareerSkillGap } from "@/types/ai.types";

export default function AICareerPage() {
  const [goals, setGoals] = useState<AICareerGoal[]>([]);
  const [history, setHistory] = useState<AICareerHistory | null>(null);
  const [analytics, setAnalytics] = useState<AICareerAnalytics | null>(null);
  const [assessment, setAssessment] = useState<AICareerAssessment | null>(null);
  const [gap, setGap] = useState<AICareerSkillGap | null>(null);
  const [coaching, setCoaching] = useState<AICareerCoachingSummary | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    const [goalData, historyData, analyticsData] = await Promise.all([getCareerGoals(), getCareerHistory(), getCareerAnalytics()]);
    setGoals(goalData);
    setHistory(historyData);
    setAnalytics(analyticsData);
  }

  useEffect(() => {
    let isMounted = true;
    Promise.all([getCareerGoals(), getCareerHistory(), getCareerAnalytics()])
      .then(([goalData, historyData, analyticsData]) => {
        if (!isMounted) return;
        setGoals(goalData);
        setHistory(historyData);
        setAnalytics(analyticsData);
      })
      .catch(() => {
        if (isMounted) setError("Unable to load AI Career Coach.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const activeGoal = goals.find((goal) => goal.status === "active") ?? goals[0];

  async function runAssessment() {
    setBusy("assessment");
    setError("");
    try {
      setAssessment(await runCareerAssessment({ goal_id: activeGoal?.id, current_skills: ["communication", "problem solving"] }));
      await refresh();
    } catch {
      setError("Unable to run career assessment.");
    } finally {
      setBusy("");
    }
  }

  async function runGap() {
    setBusy("gap");
    setError("");
    try {
      setGap(await runCareerSkillGap({ goal_id: activeGoal?.id, target: activeGoal?.target_role || "career goal", desired_skills: ["python", "sql", "communication"] }));
      await refresh();
    } catch {
      setError("Unable to run skill gap analysis.");
    } finally {
      setBusy("");
    }
  }

  async function runCoaching() {
    setBusy("coaching");
    setError("");
    try {
      setCoaching(await generateWeeklyCareerCoaching({ goal_id: activeGoal?.id, achievements: ["Reviewed career plan"] }));
      await refresh();
    } catch {
      setError("Unable to generate weekly coaching.");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">AI Career Coach</h1>
          <p className="text-sm text-muted-foreground">Long-term planning, readiness, skill gaps, weekly coaching, and career momentum.</p>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}

        <section className="grid gap-4 md:grid-cols-4">
          <div className="stat-card"><span className="stat-value">{analytics?.active_goals ?? 0}</span><span className="stat-label">Active goals</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.latest_readiness_score ?? "0.00"}</span><span className="stat-label">Readiness</span></div>
          <div className="stat-card"><span className="stat-value">{Math.round(Number(analytics?.roadmap_completion ?? 0))}%</span><span className="stat-label">Roadmap completion</span></div>
          <div className="stat-card"><span className="stat-value">{analytics?.weekly_coaching_count ?? 0}</span><span className="stat-label">Coaching weeks</span></div>
        </section>

        <section className="card p-5">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="font-semibold">{activeGoal?.title || "No active goal yet"}</h2>
              <p className="text-sm text-muted-foreground">{activeGoal ? `${activeGoal.target_role} - ${activeGoal.progress_percentage}% progress` : "Create a career goal to personalize coaching."}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="btn-base btn-primary" disabled={busy !== ""} onClick={() => void runAssessment()}>{busy === "assessment" ? "Assessing..." : "Run assessment"}</button>
              <button className="btn-base btn-secondary" disabled={busy !== ""} onClick={() => void runGap()}>{busy === "gap" ? "Analyzing..." : "Skill gap"}</button>
              <button className="btn-base btn-secondary" disabled={busy !== ""} onClick={() => void runCoaching()}>{busy === "coaching" ? "Coaching..." : "Weekly coaching"}</button>
            </div>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <div className="card p-5">
            <h2 className="font-semibold">Assessment</h2>
            <p className="mt-3 text-3xl font-semibold text-primary">{assessment?.readiness_score ?? history?.assessments[0]?.readiness_score ?? "0.00"}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {(assessment?.strengths ?? history?.assessments[0]?.strengths ?? []).slice(0, 5).map((item) => <span key={item} className="tag">{item}</span>)}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold">Priority gaps</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(gap?.priority_skills ?? history?.skill_gaps[0]?.priority_skills ?? []).slice(0, 6).map((item) => <span key={item} className="tag">{item}</span>)}
            </div>
          </div>
          <div className="card p-5">
            <h2 className="font-semibold">Weekly coaching</h2>
            <p className="mt-3 text-sm text-muted-foreground">{coaching?.motivation_summary || history?.coaching[0]?.motivation_summary || "Generate a weekly summary to keep your plan moving."}</p>
          </div>
        </section>
      </div>
    </main>
  );
}
