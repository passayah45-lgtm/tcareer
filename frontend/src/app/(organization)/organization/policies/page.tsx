"use client";

import { FormEvent, useEffect, useState } from "react";
import { OrganizationShell, OrgEmptyState, useOrganizationContext } from "@/components/organization/OrganizationShell";
import { getOrganizationPolicies, updateOrganizationPolicies } from "@/lib/api/organizations.api";
import type { OrganizationPolicy } from "@/types/organization.types";

export default function OrganizationPoliciesPage() {
  const { organization } = useOrganizationContext();
  const [policy, setPolicy] = useState<OrganizationPolicy | null>(null);
  const [domains, setDomains] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!organization) return;
    getOrganizationPolicies(organization.id)
      .then((data) => {
        setPolicy(data);
        setDomains(data.allowed_email_domains.join(", "));
      })
      .catch(() => setError("Unable to load policies."));
  }, [organization]);

  function setBoolean(field: keyof OrganizationPolicy, value: boolean) {
    setPolicy((current) => current ? { ...current, [field]: value } : current);
  }

  function setNumber(field: keyof OrganizationPolicy, value: string) {
    setPolicy((current) => current ? { ...current, [field]: Number(value) || 0 } : current);
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organization || !policy) return;
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...policy,
        allowed_email_domains: domains.split(",").map((item) => item.trim()).filter(Boolean),
      };
      setPolicy(await updateOrganizationPolicies(organization.id, payload));
    } catch {
      setError("Unable to save policies.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <OrganizationShell title="Policies" description="Control security defaults, visibility defaults, invitation expiry, sessions, and notification defaults.">
      {error && <p className="text-sm text-destructive mb-4">{error}</p>}
      {!policy ? <OrgEmptyState title="Loading policies" body="Policy settings are being loaded." /> : (
        <form onSubmit={save} className="rounded-xl border border-border bg-card p-5 space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="block text-sm">Password minimum length<input className="input mt-1" value={policy.password_min_length} onChange={(event) => setNumber("password_min_length", event.target.value)} /></label>
            <label className="block text-sm">Session timeout minutes<input className="input mt-1" value={policy.session_timeout_minutes} onChange={(event) => setNumber("session_timeout_minutes", event.target.value)} /></label>
            <label className="block text-sm">Invitation expiry days<input className="input mt-1" value={policy.invitation_expiration_days} onChange={(event) => setNumber("invitation_expiration_days", event.target.value)} /></label>
            <label className="block text-sm">Digest frequency<input className="input mt-1" value={policy.digest_frequency} onChange={(event) => setPolicy((current) => current ? { ...current, digest_frequency: event.target.value } : current)} /></label>
          </div>
          <label className="block text-sm">Allowed email domains<input className="input mt-1" value={domains} onChange={(event) => setDomains(event.target.value)} /></label>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={policy.mfa_required} onChange={(event) => setBoolean("mfa_required", event.target.checked)} /> Require MFA</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={policy.profile_visibility_default} onChange={(event) => setBoolean("profile_visibility_default", event.target.checked)} /> Public profile default</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={policy.resume_visibility_default} onChange={(event) => setBoolean("resume_visibility_default", event.target.checked)} /> Resume visible by default</label>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={policy.portfolio_visibility_default} onChange={(event) => setBoolean("portfolio_visibility_default", event.target.checked)} /> Portfolio visible by default</label>
          </div>
          <button disabled={saving} className="btn-base btn-primary">{saving ? "Saving..." : "Save policies"}</button>
        </form>
      )}
    </OrganizationShell>
  );
}
