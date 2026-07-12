"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import { getTalentPools, saveCandidate, searchCandidates, unlockCandidate } from "@/lib/api/recruiter.api";
import type { CandidateSearchResult, TalentPool } from "@/types/recruiter.types";

function CandidateSearchContent() {
  const { organization } = useRecruiterContext();
  const [filters, setFilters] = useState({
    search: "",
    skills: "",
    experience: "",
    country: "",
    city: "",
    languages: "",
    career_interests: "",
    availability: "",
    expected_salary: "",
    remote_preference: "",
    work_authorization: "",
    verification_status: "",
    portfolio_available: "",
    resume_available: "",
  });
  const [candidates, setCandidates] = useState<CandidateSearchResult[]>([]);
  const [pools, setPools] = useState<TalentPool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [unlockingId, setUnlockingId] = useState("");

  function setFilter(field: keyof typeof filters, value: string) {
    setFilters((prev) => ({ ...prev, [field]: value }));
  }

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      const [result, poolData] = await Promise.all([
        searchCandidates(organization.id, { ...filters, page_size: 50 }),
        getTalentPools(organization.id),
      ]);
      setCandidates(result.data);
      setPools(poolData);
      setError("");
    } catch {
      setError("Unable to search candidates. Check organization entitlement.");
    } finally {
      setLoading(false);
    }
  }, [filters, organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function save(candidate: CandidateSearchResult) {
    if (!organization) return;
    const label = window.prompt("Label for this candidate", candidate.desired_role || "candidate");
    const note = window.prompt("Private note", "");
    await saveCandidate(organization.id, {
      candidate_id: candidate.candidate_id,
      labels: label ? [label] : [],
      private_notes: note || "",
      talent_pool: pools[0]?.id || null,
    });
    await load();
  }

  async function unlock(candidate: CandidateSearchResult) {
    if (!organization) return;
    setUnlockingId(candidate.candidate_id);
    setError("");
    try {
      await unlockCandidate(organization.id, candidate.candidate_id);
      await load();
    } catch {
      setError("Candidate unlock denied. Check profile-view entitlement or organization permissions.");
    } finally {
      setUnlockingId("");
    }
  }

  return (
    <div className="space-y-5">
      <section className="border border-border rounded-xl bg-card p-4 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
        <input className="input" placeholder="Search" value={filters.search} onChange={(e) => setFilter("search", e.target.value)} />
        <input className="input" placeholder="Skills: Python,Django" value={filters.skills} onChange={(e) => setFilter("skills", e.target.value)} />
        <select className="input" value={filters.experience} onChange={(e) => setFilter("experience", e.target.value)}>
          <option value="">Any experience</option>
          <option value="student">Student</option>
          <option value="entry">Entry</option>
          <option value="mid">Mid</option>
          <option value="senior">Senior</option>
          <option value="lead">Lead</option>
        </select>
        <input className="input" placeholder="Availability" value={filters.availability} onChange={(e) => setFilter("availability", e.target.value)} />
        <input className="input" placeholder="Country code" value={filters.country} onChange={(e) => setFilter("country", e.target.value)} />
        <input className="input" placeholder="City" value={filters.city} onChange={(e) => setFilter("city", e.target.value)} />
        <input className="input" placeholder="Languages: en,fr" value={filters.languages} onChange={(e) => setFilter("languages", e.target.value)} />
        <input className="input" placeholder="Career interests" value={filters.career_interests} onChange={(e) => setFilter("career_interests", e.target.value)} />
        <input className="input" placeholder="Expected salary" value={filters.expected_salary} onChange={(e) => setFilter("expected_salary", e.target.value)} />
        <input className="input" placeholder="Work authorization" value={filters.work_authorization} onChange={(e) => setFilter("work_authorization", e.target.value)} />
        <select className="input" value={filters.remote_preference} onChange={(e) => setFilter("remote_preference", e.target.value)}>
          <option value="">Any remote preference</option>
          <option value="onsite">Onsite</option>
          <option value="hybrid">Hybrid</option>
          <option value="remote">Remote</option>
          <option value="flexible">Flexible</option>
        </select>
        <select className="input" value={filters.verification_status} onChange={(e) => setFilter("verification_status", e.target.value)}>
          <option value="">Any verification</option>
          <option value="verified">Verified</option>
        </select>
        <div className="flex gap-2">
          <select className="input" value={filters.portfolio_available} onChange={(e) => setFilter("portfolio_available", e.target.value)}>
            <option value="">Portfolio?</option>
            <option value="true">Available</option>
          </select>
          <select className="input" value={filters.resume_available} onChange={(e) => setFilter("resume_available", e.target.value)}>
            <option value="">Resume?</option>
            <option value="true">Available</option>
          </select>
        </div>
        <button onClick={load} className="btn-base btn-primary md:col-span-3 lg:col-span-4">Search candidates</button>
      </section>

      {loading ? <div className="h-64 bg-muted rounded-xl animate-pulse" /> : null}
      {error ? <EmptyState title="Candidate search unavailable" body={error} /> : null}
      {!loading && !error && candidates.length === 0 ? <EmptyState title="No candidates found" body="Try broadening filters or checking candidate search entitlement." /> : null}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {candidates.map((candidate) => (
          <div key={candidate.candidate_id} className="border border-border rounded-xl bg-card p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-semibold">{candidate.full_name}</h2>
                <p className="text-sm text-muted-foreground">{candidate.headline || candidate.desired_role || "Candidate"}</p>
              </div>
              {candidate.verified && <span className="badge-success">Verified</span>}
            </div>
            <div className="flex flex-wrap gap-1.5 mt-4">
              {candidate.skills.slice(0, 8).map((skill) => <span key={skill} className="tag">{skill}</span>)}
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-muted-foreground">
              <span>{candidate.location || "Location not set"}</span>
              <span>{candidate.remote_preference || "Any work mode"}</span>
              <span>{candidate.portfolio_available ? "Portfolio" : "No portfolio"}</span>
              <span>{candidate.resume_available ? "Resume" : "No resume"}</span>
            </div>
            <div className="flex gap-2 mt-4">
              <button onClick={() => save(candidate)} className="btn-sm btn-primary">{candidate.is_saved ? "Update saved" : "Save"}</button>
              {candidate.is_unlocked ? (
                <button className="btn-sm btn-secondary">Unlocked</button>
              ) : (
                <button onClick={() => unlock(candidate)} className="btn-sm btn-secondary" disabled={unlockingId === candidate.candidate_id}>
                  {unlockingId === candidate.candidate_id ? "Unlocking..." : "Unlock"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function RecruiterCandidatesPage() {
  return (
    <RecruiterShell title="Candidate search" description="Find visible candidates by skills, location, work preferences, and profile availability.">
      <CandidateSearchContent />
    </RecruiterShell>
  );
}
