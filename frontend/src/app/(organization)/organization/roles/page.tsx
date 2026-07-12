"use client";

import { useCallback, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { assignEnterpriseRole, getEnterpriseRoles } from "@/lib/api/organizations.api";
import type { EnterpriseRoleResponse } from "@/types/organization.types";

const ROLES = ["student", "instructor", "mentor", "recruiter", "company_admin", "university_admin", "report_viewer", "department_manager", "cohort_manager", "team_manager", "export_manager"];

export default function OrganizationRolesPage() {
  const { organization } = useOrganizationContext();
  const [data, setData] = useState<EnterpriseRoleResponse | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setData(await getEnterpriseRoles(organization.id));
  }, [organization]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      load().catch(() => setError("Unable to load enterprise roles."));
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function changeRole(membershipId: string, role: string) {
    if (!organization) return;
    await assignEnterpriseRole(organization.id, membershipId, role);
    await load();
  }

  const members = data?.memberships.filter((member) => {
    const text = `${member.user_email} ${member.user_full_name} ${member.role}`.toLowerCase();
    return text.includes(query.toLowerCase());
  }) ?? [];

  return (
    <OrganizationShell title="Enterprise roles" description="Assign scoped reporting, export, and hierarchy management roles.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      {!data ? <OrgEmptyState title="Loading roles" body="Role assignments are being loaded." /> : (
        <div className="space-y-6">
          <section className="rounded-xl border border-border bg-card p-5">
            <input className="input mb-4" placeholder="Search members or roles" value={query} onChange={(event) => setQuery(event.target.value)} />
            <div className="divide-y divide-border">
              {members.map((member) => (
                <div key={member.id} className="py-3 grid gap-3 md:grid-cols-[1fr_220px] md:items-center">
                  <div>
                    <p className="font-medium text-sm">{member.user_full_name || member.user_email}</p>
                    <p className="text-xs text-muted-foreground">{member.user_email} · {member.status}</p>
                  </div>
                  <select className="input" value={member.role} onChange={(event) => changeRole(member.id, event.target.value)}>
                    {ROLES.map((role) => <option key={role} value={role}>{role.replaceAll("_", " ")}</option>)}
                  </select>
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-semibold mb-4">Permission summary</h2>
            {Object.entries(data.permission_summary).map(([role, summary]) => (
              <p key={role} className="text-sm py-2 border-b border-border last:border-0"><strong>{role.replaceAll("_", " ")}:</strong> {summary}</p>
            ))}
          </section>
        </div>
      )}
    </OrganizationShell>
  );
}
