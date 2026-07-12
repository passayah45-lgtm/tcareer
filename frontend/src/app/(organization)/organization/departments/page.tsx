"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { archiveDepartment, assignDepartmentMember, createDepartment, getDepartments, getOrganizationMembers } from "@/lib/api/organizations.api";
import type { Department } from "@/types/organization.types";
import type { OrganizationMember } from "@/types/recruiter.types";

export default function DepartmentsPage() {
  const { organization } = useOrganizationContext();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedMembers, setSelectedMembers] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    const [departmentItems, memberItems] = await Promise.all([getDepartments(organization.id), getOrganizationMembers(organization.id)]);
    setDepartments(departmentItems);
    setMembers(memberItems);
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load departments."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization || !name.trim()) return;
    await createDepartment(organization.id, { name, description });
    setName("");
    setDescription("");
    await load();
  }

  async function assign(departmentId: string) {
    if (!organization || !selectedMembers[departmentId]) return;
    await assignDepartmentMember(organization.id, departmentId, selectedMembers[departmentId]);
    await load();
  }

  async function archive(departmentId: string) {
    if (!organization) return;
    await archiveDepartment(organization.id, departmentId);
    await load();
  }

  return (
    <OrganizationShell title="Departments" description="Group learners, recruiters, instructors, and staff into organization departments.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      <form onSubmit={submit} className="rounded-xl border border-border bg-card p-5 grid gap-3 md:grid-cols-[1fr_1fr_auto] md:items-end mb-6">
        <label className="block text-sm">Name<input className="input mt-1" value={name} onChange={(event) => setName(event.target.value)} /></label>
        <label className="block text-sm">Description<input className="input mt-1" value={description} onChange={(event) => setDescription(event.target.value)} /></label>
        <button className="btn-base btn-primary">Create</button>
      </form>
      {departments.length === 0 ? <OrgEmptyState title="No departments" body="Create departments to mirror the customer organization." /> : (
        <div className="grid gap-4">
          {departments.map((department) => (
            <section key={department.id} className="rounded-xl border border-border bg-card p-5">
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <h2 className="font-semibold">{department.name}</h2>
                  <p className="text-sm text-muted-foreground">{department.description || "No description"} · {department.member_count} members · {department.status}</p>
                </div>
                <button onClick={() => archive(department.id)} className="btn-sm btn-secondary">Archive</button>
              </div>
              <div className="mt-4 flex flex-col gap-2 md:flex-row">
                <select className="input" value={selectedMembers[department.id] || ""} onChange={(event) => setSelectedMembers((current) => ({ ...current, [department.id]: event.target.value }))}>
                  <option value="">Assign member</option>
                  {members.map((member) => <option key={member.id} value={member.id}>{member.user_full_name || member.user_email}</option>)}
                </select>
                <button onClick={() => assign(department.id)} className="btn-sm btn-primary">Assign</button>
              </div>
              {department.members.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {department.members.map((member) => <span key={member.id} className="px-2 py-1 rounded-md bg-muted text-xs">{member.user_full_name || member.user_email}</span>)}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
    </OrganizationShell>
  );
}
