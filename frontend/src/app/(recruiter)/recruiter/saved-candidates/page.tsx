"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { createTalentPool, getSavedCandidates, getTalentPools, removeSavedCandidate } from "@/lib/api/recruiter.api";
import type { SavedCandidate, TalentPool } from "@/types/recruiter.types";

function SavedCandidatesContent() {
  const { organization } = useRecruiterContext();
  const [saved, setSaved] = useState<SavedCandidate[]>([]);
  const [pools, setPools] = useState<TalentPool[]>([]);
  const [poolName, setPoolName] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const [savedData, poolData] = await Promise.all([
        getSavedCandidates(organization.id),
        getTalentPools(organization.id),
      ]);
      setSaved(savedData);
      setPools(poolData);
      setError("");
    } catch {
      setError("Unable to load saved candidates.");
    } finally {
      setLoading(false);
    }
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function addPool(event: React.FormEvent) {
    event.preventDefault();
    if (!organization || !poolName.trim()) return;
    await createTalentPool(organization.id, { name: poolName.trim() });
    setPoolName("");
    await load();
  }

  async function remove(candidateId: string) {
    if (!organization) return;
    await removeSavedCandidate(organization.id, candidateId);
    await load();
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <section className="lg:col-span-2 space-y-4">
        {loading ? <div className="h-52 bg-muted rounded-xl animate-pulse" /> : null}
        {error ? <EmptyState title="Saved candidates unavailable" body={error} /> : null}
        {!loading && !error && saved.length === 0 ? <EmptyState title="No saved candidates" body="Save candidates from search to build talent pools." /> : null}
        {saved.map((candidate) => (
          <div key={candidate.id} className="border border-border rounded-xl bg-card p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <h2 className="font-semibold">{candidate.candidate_name}</h2>
                <p className="text-sm text-muted-foreground">{candidate.candidate_email}</p>
                {candidate.talent_pool_name && <p className="text-xs text-primary mt-1">{candidate.talent_pool_name}</p>}
              </div>
              <button onClick={() => remove(candidate.candidate)} className="btn-sm btn-secondary">Remove</button>
            </div>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {candidate.labels.map((label) => <span key={label} className="tag">{label}</span>)}
            </div>
            {candidate.private_notes && <p className="text-sm text-muted-foreground mt-3">{candidate.private_notes}</p>}
          </div>
        ))}
      </section>

      <aside className="border border-border rounded-xl bg-card p-5 h-fit">
        <h2 className="font-semibold mb-4">Talent pools</h2>
        <form onSubmit={addPool} className="flex gap-2 mb-4">
          <input className="input" value={poolName} onChange={(event) => setPoolName(event.target.value)} placeholder="Pool name" />
          <button className="btn-base btn-primary" type="submit">Add</button>
        </form>
        {pools.length === 0 ? <p className="text-sm text-muted-foreground">No talent pools yet.</p> : (
          <div className="space-y-2">
            {pools.map((pool) => (
              <div key={pool.id} className="border border-border rounded-lg p-3">
                <p className="text-sm font-medium">{pool.name}</p>
                {pool.description && <p className="text-xs text-muted-foreground">{pool.description}</p>}
              </div>
            ))}
          </div>
        )}
      </aside>
    </div>
  );
}

export default function RecruiterSavedCandidatesPage() {
  return (
    <RecruiterShell title="Saved candidates" description="Manage saved candidates, private notes, labels, and talent pools.">
      <SavedCandidatesContent />
    </RecruiterShell>
  );
}
