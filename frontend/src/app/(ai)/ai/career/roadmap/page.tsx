"use client";

import { useEffect, useState } from "react";
import { generateCareerRoadmap, getCareerGoals, getCareerHistory } from "@/lib/api/ai.api";
import type { AICareerGoal, AICareerRoadmap } from "@/types/ai.types";

export default function AICareerRoadmapPage() {
  const [goals, setGoals] = useState<AICareerGoal[]>([]);
  const [roadmaps, setRoadmaps] = useState<AICareerRoadmap[]>([]);
  const [horizon, setHorizon] = useState<AICareerRoadmap["horizon"]>("6_months");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    const [goalData, history] = await Promise.all([getCareerGoals(), getCareerHistory()]);
    setGoals(goalData);
    setRoadmaps(history.roadmaps);
  }

  useEffect(() => {
    let isMounted = true;
    Promise.all([getCareerGoals(), getCareerHistory()])
      .then(([goalData, history]) => {
        if (!isMounted) return;
        setGoals(goalData);
        setRoadmaps(history.roadmaps);
      })
      .catch(() => {
        if (isMounted) setError("Unable to load career roadmaps.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  async function createRoadmap() {
    setBusy(true);
    setError("");
    try {
      const goal = goals.find((item) => item.status === "active") ?? goals[0];
      await generateCareerRoadmap({ goal_id: goal?.id, horizon, target_role: goal?.target_role });
      await load();
    } catch {
      setError("Unable to generate roadmap.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Career Roadmap</h1>
            <p className="text-sm text-muted-foreground">Personalized milestones across skills, projects, certificates, interviews, portfolio, resume, and job search.</p>
          </div>
          <div className="flex gap-2">
            <select className="input" value={horizon} onChange={(event) => setHorizon(event.target.value as AICareerRoadmap["horizon"])}>
              <option value="3_months">3 months</option>
              <option value="6_months">6 months</option>
              <option value="12_months">12 months</option>
              <option value="24_months">24 months</option>
            </select>
            <button className="btn-base btn-primary" disabled={busy} onClick={() => void createRoadmap()}>{busy ? "Generating..." : "Generate"}</button>
          </div>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <section className="grid gap-4">
          {roadmaps.length === 0 && <div className="card p-5 text-sm text-muted-foreground">No roadmaps yet.</div>}
          {roadmaps.map((roadmap) => (
            <article key={roadmap.id} className="card p-5">
              <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="font-semibold">{roadmap.title}</h2>
                  <p className="text-sm text-muted-foreground">{roadmap.horizon.replace("_", " ")} - {roadmap.progress_percentage}% complete</p>
                </div>
                <span className="tag">{roadmap.goal_title || "Career plan"}</span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-4">
                {roadmap.milestones.map((item, index) => (
                  <div key={`${roadmap.id}-${index}`} className="rounded-md border border-border p-3 text-sm">
                    <p className="font-medium">{item.title || "Milestone"}</p>
                    <p className="text-muted-foreground">{item.due || "planned"} - {item.status || "planned"}</p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
