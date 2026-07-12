"use client";

import { useEffect, useState } from "react";
import { createCareerGoal, getCareerGoals, updateCareerGoal } from "@/lib/api/ai.api";
import type { AICareerGoal } from "@/types/ai.types";

export default function AICareerGoalsPage() {
  const [goals, setGoals] = useState<AICareerGoal[]>([]);
  const [targetRole, setTargetRole] = useState("Data Analyst");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setGoals(await getCareerGoals());
  }

  useEffect(() => {
    let isMounted = true;
    getCareerGoals()
      .then((data) => {
        if (isMounted) setGoals(data);
      })
      .catch(() => {
        if (isMounted) setError("Unable to load career goals.");
      });
    return () => {
      isMounted = false;
    };
  }, []);

  async function addGoal() {
    setBusy("create");
    try {
      await createCareerGoal({ target_role: targetRole, title: `Become ${targetRole}` });
      await load();
    } catch {
      setError("Unable to create career goal.");
    } finally {
      setBusy("");
    }
  }

  async function markComplete(goal: AICareerGoal) {
    setBusy(goal.id);
    try {
      await updateCareerGoal(goal.id, { status: "completed", progress_percentage: 100 });
      await load();
    } catch {
      setError("Unable to update career goal.");
    } finally {
      setBusy("");
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">Career Goals</h1>
          <p className="text-sm text-muted-foreground">Track target roles, milestones, progress, and coaching history.</p>
        </header>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <section className="card p-5">
          <div className="flex flex-col gap-3 md:flex-row">
            <input className="input" value={targetRole} onChange={(event) => setTargetRole(event.target.value)} />
            <button className="btn-base btn-primary" disabled={busy !== ""} onClick={() => void addGoal()}>{busy === "create" ? "Creating..." : "Create goal"}</button>
          </div>
        </section>
        <section className="grid gap-4">
          {goals.map((goal) => (
            <article key={goal.id} className="card p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="font-semibold">{goal.title}</h2>
                  <p className="text-sm text-muted-foreground">{goal.target_role} - {goal.status}</p>
                </div>
                <button className="btn-base btn-secondary" disabled={busy !== "" || goal.status === "completed"} onClick={() => void markComplete(goal)}>Mark complete</button>
              </div>
              <div className="mt-4 h-2 rounded-full bg-muted">
                <div className="h-2 rounded-full bg-primary" style={{ width: `${goal.progress_percentage}%` }} />
              </div>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}
