"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { archiveTeam, assignTeamMember, createTeam, getOrganizationMembers, getTeams } from "@/lib/api/organizations.api";
import type { OrganizationTeam } from "@/types/organization.types";
import type { OrganizationMember } from "@/types/recruiter.types";

const TEAM_TYPES = ["recruiting", "instructor", "career", "placement", "admissions", "operations", "finance", "other"];

export default function TeamsPage() {
  const { organization } = useOrganizationContext();
  const [teams, setTeams] = useState<OrganizationTeam[]>([]);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [name, setName] = useState("");
  const [teamType, setTeamType] = useState("recruiting");
  const [selectedMembers, setSelectedMembers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    const [teamItems, memberItems] = await Promise.all([getTeams(organization.id), getOrganizationMembers(organization.id)]);
    setTeams(teamItems);
    setMembers(memberItems);
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load teams."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization || !name.trim()) return;
    await createTeam(organization.id, { name, team_type: teamType });
    setName("");
    await load();
  }

  async function assign(teamId: string) {
    if (!organization || !selectedMembers[teamId]) return;
    await assignTeamMember(organization.id, teamId, selectedMembers[teamId]);
    await load();
  }

  async function archive(teamId: string) {
    if (!organization) return;
    await archiveTeam(organization.id, teamId);
    await load();
  }

  return (
    <OrganizationShell title="Teams" description="Manage functional teams for recruiting, learning operations, placement, and administration.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-5 grid gap-3 md:grid-cols-[1fr_220px_auto] md:items-end mb-6">
        <label className="block text-sm">Name<input className="input mt-1" value={name} onChange={(event) => setName(event.target.value)} /></label>
        <label className="block text-sm">Type<select className="input mt-1" value={teamType} onChange={(event) => setTeamType(event.target.value)}>{TEAM_TYPES.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
        <button className="btn-base btn-primary">Create</button>
      </form>
      {teams.length === 0 ? <OrgEmptyState title="No teams" body="Create teams to assign operational ownership." /> : (
        <div className="grid gap-4 md:grid-cols-2">
          {teams.map((team) => (
            <section key={team.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">{team.name}</h2>
                  <p className="text-sm text-muted-foreground">{team.team_type} · {team.member_count} members · {team.status}</p>
                </div>
                <button onClick={() => archive(team.id)} className="btn-sm btn-secondary">Archive</button>
              </div>
              <div className="mt-4 flex gap-2">
                <select className="input" value={selectedMembers[team.id] || ""} onChange={(event) => setSelectedMembers((current) => ({ ...current, [team.id]: event.target.value }))}>
                  <option value="">Assign member</option>
                  {members.map((member) => <option key={member.id} value={member.id}>{member.user_full_name || member.user_email}</option>)}
                </select>
                <button onClick={() => assign(team.id)} className="btn-sm btn-primary">Assign</button>
              </div>
            </section>
          ))}
        </div>
      )}
    </OrganizationShell>
  );
}
