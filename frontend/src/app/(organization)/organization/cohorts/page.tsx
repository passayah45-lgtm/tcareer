"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { archiveCohort, assignCohortMember, createCohort, getCohorts, getOrganizationMembers } from "@/lib/api/organizations.api";
import type { Cohort } from "@/types/organization.types";
import type { OrganizationMember } from "@/types/recruiter.types";

export default function CohortsPage() {
  const { organization } = useOrganizationContext();
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [name, setName] = useState("");
  const [program, setProgram] = useState("");
  const [graduationYear, setGraduationYear] = useState("");
  const [selectedMembers, setSelectedMembers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    const [cohortItems, memberItems] = await Promise.all([getCohorts(organization.id), getOrganizationMembers(organization.id)]);
    setCohorts(cohortItems);
    setMembers(memberItems);
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load cohorts."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization || !name.trim()) return;
    await createCohort(organization.id, { name, program, graduation_year: graduationYear ? Number(graduationYear) : null });
    setName("");
    setProgram("");
    setGraduationYear("");
    await load();
  }

  async function assign(cohortId: string) {
    if (!organization || !selectedMembers[cohortId]) return;
    await assignCohortMember(organization.id, cohortId, selectedMembers[cohortId]);
    await load();
  }

  async function archive(cohortId: string) {
    if (!organization) return;
    await archiveCohort(organization.id, cohortId);
    await load();
  }

  return (
    <OrganizationShell title="Cohorts" description="Group learners by academic year, program, graduation class, or enterprise training batch.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-5 grid gap-3 md:grid-cols-[1fr_1fr_160px_auto] md:items-end mb-6">
        <label className="block text-sm">Name<input className="input mt-1" value={name} onChange={(event) => setName(event.target.value)} /></label>
        <label className="block text-sm">Program<input className="input mt-1" value={program} onChange={(event) => setProgram(event.target.value)} /></label>
        <label className="block text-sm">Graduation<input className="input mt-1" value={graduationYear} onChange={(event) => setGraduationYear(event.target.value)} /></label>
        <button className="btn-base btn-primary">Create</button>
      </form>
      {cohorts.length === 0 ? <OrgEmptyState title="No cohorts" body="Create cohorts to track learner groups and training batches." /> : (
        <div className="grid gap-4">
          {cohorts.map((cohort) => (
            <section key={cohort.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="font-semibold">{cohort.name}</h2>
                  <p className="text-sm text-muted-foreground">{cohort.program || "No program"} · {cohort.graduation_year || "No graduation year"} · {cohort.member_count} members</p>
                </div>
                <button onClick={() => archive(cohort.id)} className="btn-sm btn-secondary">Archive</button>
              </div>
              <div className="mt-4 flex gap-2">
                <select className="input" value={selectedMembers[cohort.id] || ""} onChange={(event) => setSelectedMembers((current) => ({ ...current, [cohort.id]: event.target.value }))}>
                  <option value="">Assign member</option>
                  {members.map((member) => <option key={member.id} value={member.id}>{member.user_full_name || member.user_email}</option>)}
                </select>
                <button onClick={() => assign(cohort.id)} className="btn-sm btn-primary">Assign</button>
              </div>
            </section>
          ))}
        </div>
      )}
    </OrganizationShell>
  );
}
