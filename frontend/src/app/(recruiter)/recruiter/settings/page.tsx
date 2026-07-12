"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState, RecruiterShell, useRecruiterContext } from "@/components/recruiter/RecruiterShell";
import {
  changeOrganizationMemberRole,
  getRecruiterSettings,
  inviteRecruiter,
  removeOrganizationMember,
} from "@/lib/api/recruiter.api";
import type { RecruiterSettings } from "@/types/recruiter.types";

const MEMBER_ROLES = ["recruiter", "company_admin", "finance_admin", "content_moderator"];

function SettingsContent() {
  const { organization } = useRecruiterContext();
  const [settings, setSettings] = useState<RecruiterSettings | null>(null);
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!organization) return;
    setLoading(true);
    try {
      setSettings(await getRecruiterSettings(organization.id));
      setError("");
    } catch {
      setError("Unable to load recruiter settings.");
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

  async function invite(event: React.FormEvent) {
    event.preventDefault();
    if (!organization || !email.trim()) return;
    setSaving(true);
    try {
      await inviteRecruiter(organization.id, email.trim());
      setEmail("");
      await load();
    } catch {
      setError("Unable to invite recruiter. Check seats and permissions.");
    } finally {
      setSaving(false);
    }
  }

  async function changeRole(membershipId: string, role: string) {
    if (!organization) return;
    await changeOrganizationMemberRole(organization.id, membershipId, role);
    await load();
  }

  async function removeMember(membershipId: string) {
    if (!organization) return;
    await removeOrganizationMember(organization.id, membershipId);
    await load();
  }

  if (loading) return <div className="h-72 bg-muted rounded-xl animate-pulse" />;
  if (!settings) return <EmptyState title="Settings unavailable" body={error || "Recruiter settings could not be loaded."} />;

  const entitlement = settings.entitlement;
  const seatText = `${entitlement.active_recruiter_seats}/${entitlement.max_recruiter_seats}`;
  const unlockText = settings.candidate_unlock_usage.limit === null
    ? `${settings.candidate_unlock_usage.used}`
    : `${settings.candidate_unlock_usage.used}/${settings.candidate_unlock_usage.limit}`;

  return (
    <div className="space-y-6">
      {error && <div className="alert-error">{error}</div>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card"><span className="stat-value">{seatText}</span><span className="stat-label">Recruiter seats</span></div>
        <div className="stat-card"><span className="stat-value">{entitlement.remaining_recruiter_seats}</span><span className="stat-label">Seats remaining</span></div>
        <div className="stat-card"><span className="stat-value">{unlockText}</span><span className="stat-label">Candidate unlocks</span></div>
        <div className="stat-card"><span className="stat-value">{entitlement.has_active_recruiter_entitlement ? "Active" : "Missing"}</span><span className="stat-label">Entitlement</span></div>
      </div>

      <section className="border border-border rounded-xl bg-card p-6">
        <h2 className="font-semibold mb-4">Organization profile</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div><p className="text-muted-foreground">Name</p><p className="font-medium">{settings.organization.name}</p></div>
          <div><p className="text-muted-foreground">Type</p><p className="font-medium capitalize">{settings.organization.organization_type.replaceAll("_", " ")}</p></div>
          <div><p className="text-muted-foreground">Status</p><p className="font-medium capitalize">{settings.organization.status}</p></div>
        </div>
      </section>

      <section className="border border-border rounded-xl bg-card p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
          <h2 className="font-semibold">Members and roles</h2>
          {settings.can_manage && (
            <form onSubmit={invite} className="flex gap-2">
              <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="recruiter@example.com" type="email" />
              <button disabled={saving} className="btn-base btn-primary" type="submit">Invite</button>
            </form>
          )}
        </div>
        <div className="space-y-3">
          {settings.members.map((member) => (
            <div key={member.id} className="border border-border rounded-xl p-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="font-medium text-sm">{member.user_full_name}</p>
                <p className="text-xs text-muted-foreground">{member.user_email} - {member.status}</p>
              </div>
              <div className="flex gap-2">
                <select disabled={!settings.can_manage} className="input-sm border rounded" value={member.role} onChange={(event) => changeRole(member.id, event.target.value)}>
                  {[member.role, ...MEMBER_ROLES.filter((role) => role !== member.role)].map((role) => <option key={role} value={role}>{role.replaceAll("_", " ")}</option>)}
                </select>
                {settings.can_manage && <button onClick={() => removeMember(member.id)} className="btn-sm btn-secondary">Remove</button>}
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="border border-border rounded-xl bg-card p-6">
          <h2 className="font-semibold mb-4">Pending invitations</h2>
          {settings.pending_invitations.length === 0 ? <p className="text-sm text-muted-foreground">No pending invitations.</p> : (
            <div className="space-y-3">
              {settings.pending_invitations.map((inviteItem) => (
                <div key={inviteItem.id} className="border border-border rounded-lg p-3">
                  <p className="text-sm font-medium">{inviteItem.email}</p>
                  <p className="text-xs text-muted-foreground">{inviteItem.role} - expires {new Date(inviteItem.expires_at).toLocaleDateString()}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="border border-border rounded-xl bg-card p-6">
          <h2 className="font-semibold mb-4">Recent audit activity</h2>
          {settings.recent_audit_activity.length === 0 ? <p className="text-sm text-muted-foreground">No audit activity yet.</p> : (
            <div className="space-y-3">
              {settings.recent_audit_activity.map((item) => (
                <div key={item.id} className="border-l-2 border-primary/30 pl-3">
                  <p className="text-sm font-medium">{item.action.replaceAll("_", " ")}</p>
                  <p className="text-xs text-muted-foreground">{item.target_type} - {new Date(item.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default function RecruiterSettingsPage() {
  return (
    <RecruiterShell title="Recruiter settings" description="Organization profile, members, seats, invitations, entitlement, unlocks, and audit activity.">
      <SettingsContent />
    </RecruiterShell>
  );
}
